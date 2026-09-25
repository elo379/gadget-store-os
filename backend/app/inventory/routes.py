import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.inventory.schemas import (
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryLocationCreate,
    InventoryLocationResponse,
    InventoryMovementResponse,
)
from app.inventory.service import (
    create_inventory_item,
    create_location,
    get_inventory_item,
    get_inventory_movements,
    list_inventory,
    record_movement,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "/locations",
    response_model=InventoryLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_location(
    organization_id: uuid.UUID,
    payload: InventoryLocationCreate,
    db: Session = Depends(get_db),
):
    return create_location(
        db=db,
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
    )


@router.post(
    "/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory_record(
    organization_id: uuid.UUID,
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_inventory_item(
            db=db,
            organization_id=organization_id,
            product_id=payload.product_id,
            location_id=payload.location_id,
            quantity=payload.quantity,
            notes=payload.notes,
        )
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
    db: Session = Depends(get_db),
):
    try:
        return record_movement(
            db=db,
            organization_id=organization_id,
            inventory_item_id=inventory_item_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
        )
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
    db: Session = Depends(get_db),
):
    return get_inventory_movements(
        db=db,
        organization_id=organization_id,
        inventory_item_id=inventory_item_id,
    )
