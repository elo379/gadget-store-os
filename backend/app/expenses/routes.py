import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.expenses.schemas import (
    ExpenseCategoryCreate,
    ExpenseCreate,
    ExpenseResponse,
)
from app.expenses.service import (
    create_category,
    create_expense,
    get_expense_summary,
    list_expenses,
    list_categories,
    update_expense_status,
)
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("/categories/{organization_id}")
def categories(organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    from app.permissions.access import require_organization_permission
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "finance.view")
    return list_categories(db, organization_id)


@router.post("/categories")
def add_category(
    payload: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "expenses.manage")
        return create_category(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("", response_model=ExpenseResponse)
def add_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "expenses.manage")
        return create_expense(db, payload, uuid.UUID(current_user.user_id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/{expense_id}/status")
def change_status(
    expense_id: uuid.UUID,
    status: str,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "expenses.manage")
        return update_expense_status(
            db,
            organization_id,
            expense_id,
            status,
            uuid.UUID(current_user.user_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}")
def expenses(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.permissions.access import require_organization_permission
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "finance.view")
    return list_expenses(db, organization_id)


@router.get("/{organization_id}/summary")
def summary(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.permissions.access import require_organization_permission
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "finance.view")
    return get_expense_summary(db, organization_id)
