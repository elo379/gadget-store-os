import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.finance.models import FinancialTransaction
from app.purchasing.models import SupplierTransaction
from app.sales.models import Sale, SalePayment


def record_sale_financials(db: Session, sale: Sale):
    existing = db.scalar(
        select(FinancialTransaction).where(
            FinancialTransaction.organization_id == sale.organization_id,
            FinancialTransaction.reference_type == "sale",
            FinancialTransaction.reference_id == sale.id,
        )
    )

    if existing is not None:
        return

    revenue = FinancialTransaction(
        organization_id=sale.organization_id,
        transaction_type="sale",
        direction="credit",
        amount=sale.total,
        reference_type="sale",
        reference_id=sale.id,
        description=f"Revenue from sale {sale.reference_number}",
    )

    cogs = FinancialTransaction(
        organization_id=sale.organization_id,
        transaction_type="cogs",
        direction="debit",
        amount=sale.cogs,
        reference_type="sale",
        reference_id=sale.id,
        description=f"COGS from sale {sale.reference_number}",
    )

    db.add_all([revenue, cogs])
    db.commit()


def record_sale_payment(
    db: Session,
    sale: Sale,
    payment: SalePayment,
):
    existing = db.scalar(
        select(FinancialTransaction).where(
            FinancialTransaction.reference_type == "payment",
            FinancialTransaction.reference_id == payment.id,
        )
    )

    if existing is not None:
        return

    transaction = FinancialTransaction(
        organization_id=sale.organization_id,
        transaction_type="payment",
        direction="credit",
        amount=payment.amount,
        reference_type="payment",
        reference_id=payment.id,
        description=f"Payment for sale {sale.reference_number}",
    )

    db.add(transaction)
    db.commit()


def get_payment_total(
    db: Session,
    sale_id: uuid.UUID,
):
    return Decimal(
        db.scalar(
            select(
                func.coalesce(
                    func.sum(SalePayment.amount),
                    0,
                )
            ).where(
                SalePayment.sale_id == sale_id
            )
        )
        or 0
    )


def get_supplier_payments(
    db: Session,
    organization_id: uuid.UUID,
    supplier_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(SupplierTransaction).where(
                SupplierTransaction.organization_id == organization_id,
                SupplierTransaction.supplier_id == supplier_id,
                SupplierTransaction.transaction_type == "payment",
            ).order_by(
                SupplierTransaction.created_at.desc()
            )
        ).all()
    )
