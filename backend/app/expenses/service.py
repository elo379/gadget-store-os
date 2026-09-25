import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.expenses.models import Expense, ExpenseCategory
from app.expenses.schemas import ExpenseCategoryCreate, ExpenseCreate


def create_category(db: Session, payload: ExpenseCategoryCreate):
    existing = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.organization_id == payload.organization_id,
            ExpenseCategory.name == payload.name.strip(),
        )
    )
    if existing:
        raise ValueError("Expense category already exists")

    category = ExpenseCategory(
        organization_id=payload.organization_id,
        name=payload.name.strip(),
        description=payload.description.strip(),
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_expense(db: Session, payload: ExpenseCreate):
    category = db.scalar(
        select(ExpenseCategory).where(
            ExpenseCategory.id == payload.category_id,
            ExpenseCategory.organization_id == payload.organization_id,
            ExpenseCategory.is_active.is_(True),
        )
    )
    if category is None:
        raise ValueError("Expense category not found")

    existing = db.scalar(
        select(Expense).where(
            Expense.organization_id == payload.organization_id,
            Expense.reference_number == payload.reference_number,
        )
    )
    if existing:
        raise ValueError("Expense reference already exists")

    expense = Expense(
        organization_id=payload.organization_id,
        category_id=payload.category_id,
        amount=payload.amount,
        payment_method=payload.payment_method.strip(),
        reference_number=payload.reference_number.strip(),
        description=payload.description.strip(),
        status="recorded",
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense_status(
    db: Session,
    organization_id: uuid.UUID,
    expense_id: uuid.UUID,
    status: str,
):
    allowed = {"recorded", "approved", "paid", "cancelled"}

    if status not in allowed:
        raise ValueError("Invalid expense status")

    expense = db.scalar(
        select(Expense).where(
            Expense.id == expense_id,
            Expense.organization_id == organization_id,
        )
    )

    if expense is None:
        raise ValueError("Expense not found")

    if expense.status == "cancelled":
        raise ValueError("Cancelled expense cannot be changed")

    if expense.status == "paid" and status != "paid":
        raise ValueError("Paid expense cannot be changed")

    expense.status = status
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    organization_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(Expense)
            .where(
                Expense.organization_id == organization_id
            )
            .order_by(Expense.created_at.desc())
        ).all()
    )


def get_expense_summary(
    db: Session,
    organization_id: uuid.UUID,
):
    from decimal import Decimal
    from sqlalchemy import func

    total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id,
            Expense.status.in_(["recorded", "approved", "paid"]),
        )
    )

    paid = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id,
            Expense.status == "paid",
        )
    )

    return {
        "total_expenses": Decimal(total or 0),
        "paid_expenses": Decimal(paid or 0),
        "outstanding_expenses": Decimal(total or 0) - Decimal(paid or 0),
    }
