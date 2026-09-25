import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.sales.schemas import (
    SaleCreate,
    SalePaymentCreate,
    SalePaymentResponse,
    SaleResponse,
    SalesSummaryResponse,
)
from app.sales.service import (
    add_sale_payment,
    create_sale,
    get_sale,
    get_sales_summary,
    list_sales,
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleResponse)
def create_sale_route(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_sale(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.get("", response_model=list[SaleResponse])
def list_sales_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_sales(db, organization_id)


@router.get("/summary", response_model=SalesSummaryResponse)
def sales_summary_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_sales_summary(db, organization_id)


@router.post(
    "/payments",
    response_model=SalePaymentResponse,
)
def add_sale_payment_route(
    payload: SalePaymentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return add_sale_payment(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale_route(
    sale_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sale = get_sale(db, organization_id, sale_id)

    if sale is None:
        raise HTTPException(
            status_code=404,
            detail="Sale not found",
        )

    return sale
