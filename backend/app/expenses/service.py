import uuid
from datetime import datetime, timezone, date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.expenses.models import Expense, ExpenseCategory
from app.expenses.schemas import ExpenseCategoryCreate, ExpenseCreate
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction

DEFAULT_CATEGORIES = ("Rent", "Electricity", "Internet", "Salaries", "Transport", "Logistics", "Repairs", "Maintenance", "Marketing", "Packaging", "Security", "Bank/payment charges", "Miscellaneous")


def list_categories(db: Session, organization_id: uuid.UUID):
    existing = {name.lower() for name in db.scalars(select(ExpenseCategory.name).where(ExpenseCategory.organization_id == organization_id)).all()}
    for name in DEFAULT_CATEGORIES:
        if name.lower() not in existing:
            db.add(ExpenseCategory(organization_id=organization_id, name=name))
    db.flush()
    return list(db.scalars(select(ExpenseCategory).where(ExpenseCategory.organization_id == organization_id, ExpenseCategory.is_active.is_(True)).order_by(ExpenseCategory.name)).all())


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


def create_expense(db: Session, payload: ExpenseCreate, actor_id: uuid.UUID):
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
        expense_date=payload.expense_date or date.today(),
        store_id=payload.store_id,
        payment_account=payload.payment_account.strip(),
        attachment_reference=payload.attachment_reference.strip(),
        actor_id=actor_id,
    )
    db.add(expense)
    db.flush()
    db.add(AuditLog(organization_id=payload.organization_id, user_id=actor_id,
        action="expense.recorded", entity_type="expense", entity_id=expense.id,
        description=f"Expense recorded: {payload.reference_number.strip()}", metadata_json="{}"))
    db.commit()
    db.refresh(expense)
    return expense


def update_expense_status(
    db: Session,
    organization_id: uuid.UUID,
    expense_id: uuid.UUID,
    status: str,
    actor_id: uuid.UUID,
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

    previous_status = expense.status
    if status == "approved" and expense.status not in {"recorded", "approved"}:
        raise ValueError("Only recorded expenses can be approved")
    if status == "paid" and expense.status not in {"approved", "paid"}:
        raise ValueError("Expense must be approved before payment")
    expense.status = status
    if status == "approved":
        expense.approved_by_user_id = actor_id
        expense.approved_at = datetime.now(timezone.utc)
    if status == "paid" and previous_status != "paid":
        db.add(FinancialTransaction(organization_id=organization_id, transaction_type="expense_payment",
            direction="debit", amount=expense.amount, reference_type="expense", reference_id=expense.id,
            description=f"Payment for expense {expense.reference_number}", actor_id=actor_id, store_id=expense.store_id))
    db.add(AuditLog(organization_id=organization_id, user_id=actor_id,
        action=f"expense.{status}", entity_type="expense", entity_id=expense.id,
        description=f"Expense {expense.reference_number} status changed to {status}", metadata_json="{}"))
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
