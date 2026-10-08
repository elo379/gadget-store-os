import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.inventory.schemas import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryLocationCreate,
    InventoryLocationResponse,
    InventoryMovementResponse,
    InventoryTransferCreate,
)
from app.inventory.service import (
    create_inventory_item,
    create_location,
    get_inventory_item,
    get_inventory_movements,
    list_inventory,
    record_movement,
    transfer_stock,
)
from app.inventory.models import InventoryLocation
from app.permissions.dependencies import require_permission

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/locations", response_model=list[InventoryLocationResponse])
def list_inventory_locations(
    organization_id: uuid.UUID,
    _current_user=Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(InventoryLocation)
            .where(
                InventoryLocation.organization_id == organization_id,
                InventoryLocation.is_active.is_(True),
            )
            .order_by(InventoryLocation.name)
        ).all()
    )


@router.post(
    "/locations",
    response_model=InventoryLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_location(
    organization_id: uuid.UUID,
    payload: InventoryLocationCreate,
    current_user=Depends(require_permission("branches.manage")),
    db: Session = Depends(get_db),
):
    location = create_location(
        db=db,
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
    )
    db.commit()
    db.refresh(location)
    return location


@router.post(
    "/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_record(
    organization_id: uuid.UUID,
    payload: InventoryItemCreate,
    current_user=Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db),
):
    try:
        item = create_inventory_item(
            db=db,
            organization_id=organization_id,
            product_id=payload.product_id,
            location_id=payload.location_id,
            quantity=payload.quantity,
            notes=payload.notes,
        )
        db.commit()
        db.refresh(item)
        return item
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[InventoryItemResponse],
)
def list_inventory_items(
    organization_id: uuid.UUID,
    _current_user=Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
):
    return list_inventory(
        db=db,
        organization_id=organization_id,
    )


@router.get(
    "/{inventory_item_id}",
    response_model=InventoryItemResponse,
)
def get_inventory_record(
    organization_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    _current_user=Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
):
    item = get_inventory_item(
        db=db,
        organization_id=organization_id,
        inventory_item_id=inventory_item_id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found",
        )

    return item


@router.post(
    "/{inventory_item_id}/movements",
    response_model=InventoryMovementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_movement(
    organization_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    movement_type: str,
    quantity: Decimal,
    reason: str = "",
    current_user=Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db),
):
    try:
        movement = record_movement(
            db=db,
            organization_id=organization_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            performed_by_user_id=uuid.UUID(current_user.user_id),
        )
        db.commit()
        db.refresh(movement)
        return movement
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/{inventory_item_id}/movements",
    response_model=list[InventoryMovementResponse],
)
def list_inventory_movement_history(
    organization_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    _current_user=Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
):
    return get_inventory_movements(
        db=db,
        organization_id=organization_id,
        inventory_item_id=inventory_item_id,
    )


@router.post("/transfer", response_model=list[InventoryMovementResponse], status_code=201)
def transfer_inventory(
    organization_id: uuid.UUID,
    payload: InventoryTransferCreate,
    current_user=Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db),
):
    try:
        movements = transfer_stock(
            db, organization_id, payload.inventory_item_id,
            payload.destination_location_id, payload.quantity, payload.reason,
            uuid.UUID(current_user.user_id),
        )
        db.commit()
        return list(movements)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
