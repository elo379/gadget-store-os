import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.customers.schemas import (CustomerCreate, CustomerUpdate, CustomerResponse,
                                   CustomerReturnCreate, CustomerReturnResponse)
from app.customers.service import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
)
from app.db.session import get_db
from app.permissions.access import require_organization_permission
from app.customers.returns import process_return

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/returns", response_model=CustomerReturnResponse, status_code=201)
def create_customer_return(
    payload: CustomerReturnCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        require_organization_permission(
            db, uuid.UUID(current_user.user_id), payload.organization_id, "sales.manage"
        )
        result = process_return(
            db,
            payload.organization_id,
            payload.sale_id,
            payload.reference_number,
            [line.model_dump() for line in payload.lines],
            payload.reason,
            performed_by_user_id=uuid.UUID(current_user.user_id),
        )
        db.commit()
        return result
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("", response_model=list[CustomerResponse])
def customers(
    organization_id: uuid.UUID,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.view")
    return list_customers(db, organization_id, search)


@router.post("", response_model=CustomerResponse, status_code=201)
def add_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "customers.manage")
    return create_customer(db, payload)


@router.get("/{customer_id}", response_model=CustomerResponse)
def customer(
    customer_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.view")
    result = get_customer(db, organization_id, customer_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return result


@router.patch("/{customer_id}", response_model=CustomerResponse)
def edit_customer(
    customer_id: uuid.UUID,
    organization_id: uuid.UUID,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "customers.manage")
    result = get_customer(db, organization_id, customer_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return update_customer(db, result, payload)
