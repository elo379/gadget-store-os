import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.products.models import Product
from app.purchasing.models import (
    PurchaseLine,
    PurchaseOrder,
    SupplierTransaction,
)
from app.purchasing.schemas import (
    PurchaseOrderCreate,
    SupplierTransactionCreate,
)
from app.suppliers.models import Supplier
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction


def create_purchase_order(
    db: Session,
    payload: PurchaseOrderCreate,
) -> PurchaseOrder:
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == payload.supplier_id,
            Supplier.organization_id == payload.organization_id,
            Supplier.is_active.is_(True),
        )
    )

    if supplier is None:
        raise ValueError("Supplier not found")

    duplicate = db.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.organization_id == payload.organization_id,
            PurchaseOrder.reference_number
            == payload.reference_number.strip(),
        )
    )

    if duplicate is not None:
        raise ValueError("Purchase reference already exists")

    purchase = PurchaseOrder(
        organization_id=payload.organization_id,
        supplier_id=payload.supplier_id,
        reference_number=payload.reference_number.strip(),
        status="draft",
        notes=payload.notes.strip(),
    )

    subtotal = Decimal("0")

    for item in payload.lines:
        product = db.scalar(
            select(Product).where(
                Product.id == item.product_id,
                Product.organization_id == payload.organization_id,
                Product.is_active.is_(True),
            )
        )

        if product is None:
            raise ValueError("Product not found")

        line_total = item.quantity * item.unit_cost
        subtotal += line_total

        purchase.lines.append(
            PurchaseLine(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                line_total=line_total,
            )
        )

    purchase.subtotal = subtotal
    purchase.total = subtotal

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    return purchase


def get_purchase_order(
    db: Session,
    organization_id: uuid.UUID,
    purchase_id: uuid.UUID,
) -> PurchaseOrder | None:
    return db.scalar(
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(
            PurchaseOrder.id == purchase_id,
            PurchaseOrder.organization_id == organization_id,
        )
    )


def list_purchase_orders(
    db: Session,
    organization_id: uuid.UUID,
) -> list[PurchaseOrder]:
    statement = (
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.organization_id == organization_id)
        .order_by(PurchaseOrder.created_at.desc())
    )

    return list(db.scalars(statement).unique().all())


def create_supplier_transaction(
    db: Session,
    payload: SupplierTransactionCreate,
    performed_by_user_id: uuid.UUID | None = None,
) -> SupplierTransaction:
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == payload.supplier_id,
            Supplier.organization_id == payload.organization_id,
            Supplier.is_active.is_(True),
        )
    )

    if supplier is None:
        raise ValueError("Supplier not found")

    transaction = SupplierTransaction(
        organization_id=payload.organization_id,
        supplier_id=payload.supplier_id,
        transaction_type=payload.transaction_type.strip().lower(),
        amount=payload.amount,
        reference_type=payload.reference_type.strip(),
        reference_id=payload.reference_id,
        notes=payload.notes.strip(),
    )

    db.add(transaction)
    db.flush()
    db.add(AuditLog(
        organization_id=payload.organization_id,
        user_id=performed_by_user_id,
        action="supplier.transaction_recorded",
        entity_type="supplier_transaction",
        entity_id=transaction.id,
        description=f"Supplier {transaction.transaction_type} transaction recorded",
        metadata_json="{}",
    ))
    if transaction.transaction_type in {"payment", "credit"}:
        db.add(FinancialTransaction(
            organization_id=payload.organization_id, transaction_type="supplier_payment", direction="debit",
            amount=transaction.amount, reference_type="supplier_transaction", reference_id=transaction.id,
            description=f"Payment to supplier {supplier.name}", actor_id=performed_by_user_id,
        ))

    return transaction


def get_supplier_balance(
    db: Session,
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
) -> Decimal:
    supplier = db.scalar(
        select(Supplier).where(
            Supplier.id == supplier_id,
            Supplier.organization_id == organization_id,
        )
    )

    if supplier is None:
        raise ValueError("Supplier not found")

    transactions = db.scalars(
        select(SupplierTransaction).where(
            SupplierTransaction.organization_id == organization_id,
            SupplierTransaction.supplier_id == supplier_id,
        )
    ).all()

    balance = Decimal("0")

    for transaction in transactions:
        if transaction.transaction_type in {"purchase", "debit"}:
            balance += transaction.amount
        elif transaction.transaction_type in {"payment", "credit"}:
            balance -= transaction.amount

    return balance
