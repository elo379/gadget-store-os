import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.purchasing.receiving import receive_purchase
from app.purchasing.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseReceiveRequest,
    SupplierTransactionCreate,
    SupplierTransactionResponse,
)
from app.purchasing.service import (
    create_purchase_order,
    create_supplier_transaction,
    get_purchase_order,
    get_supplier_balance,
    list_purchase_orders,
)
from app.auth.schemas import AuthenticatedUser
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/purchasing", tags=["purchasing"])


@router.post("/orders", response_model=PurchaseOrderResponse)
def create_purchase_order_route(
    payload: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "purchases.manage")
        return create_purchase_order(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/orders", response_model=list[PurchaseOrderResponse])
def list_purchase_order_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "purchases.view")
    return list_purchase_orders(db, organization_id)


@router.get("/orders/{purchase_id}", response_model=PurchaseOrderResponse)
def get_purchase_order_route(
    purchase_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "purchases.view")
    purchase = get_purchase_order(
        db,
        organization_id,
        purchase_id,
    )

    if purchase is None:
        raise HTTPException(
            status_code=404,
            detail="Purchase order not found",
        )

    return purchase


@router.post(
    "/supplier-transactions",
    response_model=SupplierTransactionResponse,
)
def create_supplier_transaction_route(
    payload: SupplierTransactionCreate,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "purchases.manage")
        transaction = create_supplier_transaction(db, payload, uuid.UUID(current_user.user_id))
        db.commit()
        db.refresh(transaction)
        return transaction
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.get("/suppliers/{supplier_id}/balance")
def get_supplier_balance_route(
    supplier_id: uuid.UUID,
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "purchases.view")
    try:
        balance = get_supplier_balance(
            db,
            organization_id,
            supplier_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    return {
        "supplier_id": supplier_id,
        "balance": balance,
    }


@router.post("/receive", response_model=dict)
def receive_purchase_route(
    payload: PurchaseReceiveRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser=Depends(get_current_user),
):
    try:
        require_organization_permission(db, uuid.UUID(current_user.user_id), payload.organization_id, "purchases.manage")
        return receive_purchase(db, payload.model_copy(update={"received_by_user_id": uuid.UUID(current_user.user_id)}))
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )
