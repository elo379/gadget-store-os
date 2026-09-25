import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.suppliers.schemas import SupplierCreate, SupplierResponse
from app.suppliers.service import (
    create_supplier,
    get_supplier,
    list_suppliers,
)

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
)


@router.post("", response_model=SupplierResponse)
def create_supplier_route(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_supplier(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.get("", response_model=list[SupplierResponse])
def list_supplier_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_suppliers(
        db,
        organization_id,
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier_route(
    supplier_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    supplier = get_supplier(
        db,
        organization_id,
        supplier_id,
    )

    if supplier is None:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found",
        )

    return supplier
