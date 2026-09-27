import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.customers.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.customers.service import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
)
from app.db.session import get_db

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
def customers(
    organization_id: uuid.UUID,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return list_customers(db, organization_id, search)


@router.post("", response_model=CustomerResponse, status_code=201)
def add_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return create_customer(db, payload)


@router.get("/{customer_id}", response_model=CustomerResponse)
def customer(
    customer_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
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
    result = get_customer(db, organization_id, customer_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return update_customer(db, result, payload)
