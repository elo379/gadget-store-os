import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.finance.models import FinancialTransaction
from app.finance.schemas import FinancialTransactionCreate
from app.sales.models import Sale
from app.sales.models import SalePayment
from app.expenses.models import Expense
from app.inventory.ledger import InventoryMovement
from app.inventory.models import InventoryItem
from app.devices.models import DeviceRecord
from app.customers.returns import CustomerReturn
from app.purchasing.models import SupplierTransaction
from app.products.models import Product


def create_financial_transaction(
    db: Session,
    payload: FinancialTransactionCreate,
):
    if payload.direction not in {"credit", "debit"}:
        raise ValueError("Invalid transaction direction")

    transaction = FinancialTransaction(
        organization_id=payload.organization_id,
        transaction_type=payload.transaction_type.strip(),
        direction=payload.direction,
        amount=payload.amount,
        reference_type=payload.reference_type.strip(),
        reference_id=payload.reference_id,
        description=payload.description.strip(),
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def get_financial_summary(
    db: Session,
    organization_id: uuid.UUID,
):
    revenue = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    cogs = db.scalar(
        select(func.coalesce(func.sum(Sale.cogs), 0)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    expenses = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.organization_id == organization_id, Expense.status.in_(["recorded", "approved", "paid"])))
    payments = db.scalar(select(func.coalesce(func.sum(SalePayment.amount), 0)).join(Sale).where(
        Sale.organization_id == organization_id, Sale.status == "completed"))
    receivables = db.scalar(select(func.coalesce(func.sum(Sale.total), 0)).where(
        Sale.organization_id == organization_id, Sale.status == "completed")) - payments

    revenue = Decimal(revenue or 0)
    cogs = Decimal(cogs or 0)
    expenses = Decimal(expenses or 0)

    gross_profit = revenue - cogs
    operating_result = gross_profit - expenses
    supplier_credits = db.scalar(select(func.coalesce(func.sum(SupplierTransaction.amount), 0)).where(
        SupplierTransaction.organization_id == organization_id, SupplierTransaction.transaction_type.in_(["purchase", "debit"]))) or 0
    supplier_payments = db.scalar(select(func.coalesce(func.sum(SupplierTransaction.amount), 0)).where(
        SupplierTransaction.organization_id == organization_id, SupplierTransaction.transaction_type.in_(["payment", "credit"]))) or 0
    quantity_value = db.scalar(select(func.coalesce(func.sum(InventoryItem.quantity * InventoryItem.average_unit_cost), 0))
        .join(Product, Product.id == InventoryItem.product_id).where(
            InventoryItem.organization_id == organization_id, InventoryItem.status == "active", Product.is_serialized.is_(False))) or 0
    device_value = db.scalar(select(func.coalesce(func.sum(DeviceRecord.acquisition_cost), 0)).where(
        DeviceRecord.organization_id == organization_id, DeviceRecord.is_active.is_(True),
        DeviceRecord.status.in_(["in_stock", "received", "active"]))) or 0

    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "expenses": expenses,
        "operating_result": operating_result,
        "payments_received": Decimal(payments or 0),
        "customer_outstanding": Decimal(receivables or 0),
        "supplier_outstanding": Decimal(supplier_credits) - Decimal(supplier_payments),
        "inventory_value": Decimal(quantity_value) + Decimal(device_value),
    }


def get_reconciliation(db: Session, organization_id: uuid.UUID):
    issues = []
    sales = db.scalars(select(Sale).where(Sale.organization_id == organization_id, Sale.status == "completed")).all()
    for sale in sales:
        paid = db.scalar(select(func.coalesce(func.sum(SalePayment.amount), 0)).where(SalePayment.sale_id == sale.id)) or 0
        expected = "paid" if Decimal(str(paid)) >= sale.total else ("partial" if paid else "unpaid")
        if sale.payment_status != expected:
            issues.append({"code": "sale_payment_state", "entity_id": str(sale.id), "reference": sale.reference_number,
                           "detail": f"Stored state {sale.payment_status}; payment ledger implies {expected}."})
        if sale.lines and sum((line.line_cogs for line in sale.lines), Decimal("0")) != sale.cogs:
            issues.append({"code": "sale_cogs_mismatch", "entity_id": str(sale.id), "reference": sale.reference_number,
                           "detail": "Sale COGS does not equal its line costs."})
    for tx in db.scalars(select(FinancialTransaction).where(FinancialTransaction.organization_id == organization_id)).all():
        if tx.actor_id is None:
            issues.append({"code": "financial_event_without_actor", "entity_id": str(tx.id), "reference": tx.reference_type, "detail": "Financial event has no attributed actor."})
        if tx.reference_type == "sale" and tx.reference_id and db.get(Sale, tx.reference_id) is None:
            issues.append({"code": "financial_event_without_sale", "entity_id": str(tx.id), "reference": str(tx.reference_id), "detail": "Financial event references a missing sale."})
        if tx.transaction_type == "payment" and tx.reference_type == "payment" and tx.reference_id and db.get(SalePayment, tx.reference_id) is None:
            issues.append({"code": "payment_without_sale", "entity_id": str(tx.id), "reference": str(tx.reference_id), "detail": "Payment event references a missing payment."})
        if tx.transaction_type == "supplier_payment" and (tx.reference_type != "supplier_transaction" or not tx.reference_id or db.get(SupplierTransaction, tx.reference_id) is None):
            issues.append({"code": "supplier_payment_without_transaction", "entity_id": str(tx.id), "reference": str(tx.reference_id), "detail": "Supplier payment has no valid supplier transaction."})
    for tx in db.scalars(select(FinancialTransaction).where(FinancialTransaction.organization_id == organization_id, FinancialTransaction.transaction_type == "expense_payment")).all():
        if tx.reference_type != "expense" or not tx.reference_id or db.get(Expense, tx.reference_id) is None:
            issues.append({"code": "expense_payment_without_expense", "entity_id": str(tx.id), "reference": str(tx.reference_id), "detail": "Expense payment has no valid expense."})
    for movement in db.scalars(select(InventoryMovement).where(InventoryMovement.organization_id == organization_id)).all():
        if movement.movement_type == "sale" and (movement.reference_type != "sale" or not movement.reference_id or db.get(Sale, movement.reference_id) is None):
            issues.append({"code": "inventory_movement_without_source", "entity_id": str(movement.id), "reference": str(movement.reference_id), "detail": "Sale stock movement has no valid sale source."})
    for sale in sales:
        for line in sale.lines:
            if line.device_id:
                device = db.get(DeviceRecord, line.device_id)
                if device and device.status in {"in_stock", "received", "active"}:
                    issues.append({"code": "sold_device_available", "entity_id": str(device.id), "reference": sale.reference_number, "detail": "Device on a completed sale is still available."})
            else:
                movements = db.scalars(select(InventoryMovement).where(
                    InventoryMovement.organization_id == organization_id,
                    InventoryMovement.movement_type == "sale", InventoryMovement.reference_id == sale.id,
                    InventoryMovement.product_id == line.product_id,
                )).all()
                if sum((abs(Decimal(str(m.quantity))) for m in movements), Decimal("0")) < line.quantity:
                    issues.append({"code": "sale_without_inventory_deduction", "entity_id": str(sale.id), "reference": sale.reference_number,
                                   "detail": f"Insufficient stock deduction for product {line.product_id}."})
    for returned in db.scalars(select(CustomerReturn).where(CustomerReturn.organization_id == organization_id)).all():
        if db.get(Sale, returned.sale_id) is None:
            issues.append({"code": "return_without_original_sale", "entity_id": str(returned.id), "reference": returned.reference_number, "detail": "Return has no original sale."})
    for expense in db.scalars(select(Expense).where(Expense.organization_id == organization_id)).all():
        if expense.actor_id is None:
            issues.append({"code": "expense_without_actor", "entity_id": str(expense.id), "reference": expense.reference_number, "detail": "Expense has no attributed actor."})
    revenue_events = Decimal(str(db.scalar(select(func.coalesce(func.sum(FinancialTransaction.amount), 0)).where(
        FinancialTransaction.organization_id == organization_id, FinancialTransaction.transaction_type == "sale",
        FinancialTransaction.direction == "credit")) or 0))
    sales_total = Decimal(str(db.scalar(select(func.coalesce(func.sum(Sale.total), 0)).where(
        Sale.organization_id == organization_id, Sale.status == "completed")) or 0))
    if revenue_events != sales_total:
        issues.append({"code": "financial_totals_inconsistent", "entity_id": str(organization_id), "reference": "revenue",
                       "detail": f"Financial event revenue {revenue_events} differs from completed sales {sales_total}."})
    return {"issue_count": len(issues), "issues": issues}
