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
    SaleReceiptResponse,
    SalesSummaryResponse,
)
from app.sales.models import Sale
from app.sales.service import (
    add_sale_payment,
    create_sale,
    get_sale,
    get_sales_summary,
    list_sales,
)
from sqlalchemy import func, select
from app.sales.models import SalePayment
from app.auth.schemas import AuthenticatedUser
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleResponse)
def create_sale_route(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "sales.create")
        authoritative_payload = payload.model_copy(update={"sold_by_user_id": uuid.UUID(current_user.user_id)})
        sale = create_sale(db, authoritative_payload)
        db.commit()
        return sale
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
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "sales.view")
    return list_sales(db, organization_id)


@router.get("/summary", response_model=SalesSummaryResponse)
def sales_summary_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "sales.view")
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
        sale = db.get(Sale, payload.sale_id)
        if sale is None:
            raise ValueError("Sale not found")
        require_organization_permission(db, uuid.UUID(current_user.user_id), sale.organization_id, "sales.manage")
        payment = add_sale_payment(db, payload.sale_id, payload.payment_method, payload.amount, payload.reference, payload.notes, uuid.UUID(current_user.user_id))
        db.commit()
        return payment
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
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "sales.view")
    sale = get_sale(db, organization_id, sale_id)

    if sale is None:
        raise HTTPException(
            status_code=404,
            detail="Sale not found",
        )

    return sale


@router.get("/{sale_id}/receipt", response_model=SaleReceiptResponse)
def sale_receipt_route(sale_id: uuid.UUID, organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "sales.view")
    sale = get_sale(db, organization_id, sale_id)
    paid = db.scalar(select(func.coalesce(func.sum(SalePayment.amount), 0)).where(SalePayment.sale_id == sale.id)) or 0
    return {"sale_id": sale.id, "reference_number": sale.reference_number, "status": sale.status, "payment_status": sale.payment_status, "customer_id": sale.customer_id, "sold_by_user_id": sale.sold_by_user_id, "subtotal": sale.subtotal, "discount": sale.discount, "total": sale.total, "amount_paid": paid, "amount_due": sale.total - paid, "cogs": sale.cogs, "gross_profit": sale.gross_profit, "lines": sale.lines}
