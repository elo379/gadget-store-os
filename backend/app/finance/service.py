import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.finance.models import FinancialTransaction
from app.finance.schemas import FinancialTransactionCreate
from app.sales.models import Sale


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

    expenses = db.scalar(
        select(func.coalesce(func.sum(FinancialTransaction.amount), 0)).where(
            FinancialTransaction.organization_id == organization_id,
            FinancialTransaction.transaction_type == "expense",
            FinancialTransaction.direction == "debit",
        )
    )

    revenue = Decimal(revenue or 0)
    cogs = Decimal(cogs or 0)
    expenses = Decimal(expenses or 0)

    gross_profit = revenue - cogs
    net_operating_profit = gross_profit - expenses

    return {
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "expenses": expenses,
        "net_operating_profit": net_operating_profit,
    }
