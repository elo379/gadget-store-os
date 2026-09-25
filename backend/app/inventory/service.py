from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.inventory.constants import VALID_MOVEMENT_TYPES
from app.inventory.ledger import InventoryMovement
from app.inventory.models import InventoryItem, InventoryLocation
from app.products.models import Product


def create_location(
    db: Session,
    organization_id,
    name: str,
    description: str = "",
):
    location = InventoryLocation(
        organization_id=organization_id,
        name=name,
        description=description,
    )
    db.add(location)
    db.flush()
    return location


def create_inventory_item(
    db: Session,
    organization_id,
    product_id,
    location_id=None,
    quantity=0,
):
    product = db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.organization_id == organization_id,
            Product.is_active.is_(True),
        )
    )

    if product is None:
        raise ValueError("Product does not belong to organization")

    if location_id is not None:
        location = db.scalar(
            select(InventoryLocation).where(
                InventoryLocation.id == location_id,
                InventoryLocation.organization_id == organization_id,
                InventoryLocation.is_active.is_(True),
            )
        )

        if location is None:
            raise ValueError("Inventory location not found")

    initial_quantity = Decimal(str(quantity))

    if initial_quantity < 0:
        raise ValueError("Inventory quantity cannot be negative")

    item = InventoryItem(
        organization_id=organization_id,
        product_id=product_id,
        location_id=location_id,
        quantity=Decimal("0"),
        reserved_quantity=Decimal("0"),
        status="active",
    )

    db.add(item)
    db.flush()

    if initial_quantity > 0:
        record_movement(
            db=db,
            organization_id=organization_id,
            inventory_item_id=item.id,
            movement_type="opening_balance",
            quantity=initial_quantity,
            reason="Opening inventory balance",
        )

    return item


def get_inventory_item(
    db: Session,
    organization_id,
    inventory_item_id,
):
    return db.scalar(
        select(InventoryItem).where(
            InventoryItem.id == inventory_item_id,
            InventoryItem.organization_id == organization_id,
        )
    )


def list_inventory(db: Session, organization_id):
    return list(
        db.scalars(
            select(InventoryItem)
            .where(
                InventoryItem.organization_id == organization_id
            )
            .order_by(InventoryItem.created_at)
        ).all()
    )


def record_movement(
    db: Session,
    organization_id,
    inventory_item_id,
    movement_type: str,
    quantity,
    reason: str = "",
    reference_type=None,
    reference_id=None,
    performed_by_user_id=None,
):
    if movement_type not in VALID_MOVEMENT_TYPES:
        raise ValueError("Invalid inventory movement type")

    item = get_inventory_item(
        db,
        organization_id,
        inventory_item_id,
    )

    if item is None:
        raise ValueError("Inventory item not found")

    quantity = Decimal(str(quantity))

    quantity_before = Decimal(str(item.quantity))
    quantity_after = quantity_before + quantity

    if quantity_after < 0:
        raise ValueError("Inventory quantity cannot be negative")

    item.quantity = quantity_after

    movement = InventoryMovement(
        organization_id=organization_id,
        inventory_item_id=inventory_item_id,
        movement_type=movement_type,
        quantity=quantity,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
        performed_by_user_id=performed_by_user_id,
    )

    db.add(movement)
    db.flush()

    return movement


def get_inventory_movements(
    db: Session,
    organization_id,
    inventory_item_id,
):
    return list(
        db.scalars(
            select(InventoryMovement)
            .where(
                InventoryMovement.organization_id == organization_id,
                InventoryMovement.inventory_item_id == inventory_item_id,
            )
            .order_by(InventoryMovement.created_at)
        ).all()
    )


def transfer_stock(
    db: Session,
    organization_id,
    inventory_item_id,
    destination_location_id,
    quantity,
    reason: str = "",
    performed_by_user_id=None,
):
    source_item = get_inventory_item(
        db,
        organization_id,
        inventory_item_id,
    )

    if source_item is None:
        raise ValueError("Source inventory item not found")

    if source_item.location_id == destination_location_id:
        raise ValueError(
            "Source and destination locations must differ"
        )

    destination = db.scalar(
        select(InventoryLocation).where(
            InventoryLocation.id == destination_location_id,
            InventoryLocation.organization_id == organization_id,
            InventoryLocation.is_active.is_(True),
        )
    )

    if destination is None:
        raise ValueError(
            "Destination inventory location not found"
        )

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError(
            "Transfer quantity must be greater than zero"
        )

    destination_item = db.scalar(
        select(InventoryItem).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.product_id == source_item.product_id,
            InventoryItem.location_id == destination_location_id,
        )
    )

    if destination_item is None:
        destination_item = InventoryItem(
            organization_id=organization_id,
            product_id=source_item.product_id,
            location_id=destination_location_id,
            quantity=Decimal("0"),
            reserved_quantity=Decimal("0"),
            status="active",
        )
        db.add(destination_item)
        db.flush()

    transfer_reference = source_item.id

    outbound = record_movement(
        db=db,
        organization_id=organization_id,
        inventory_item_id=source_item.id,
        movement_type="transfer_out",
        quantity=-quantity,
        reason=reason,
        reference_type="inventory_transfer",
        reference_id=transfer_reference,
        performed_by_user_id=performed_by_user_id,
    )

    inbound = record_movement(
        db=db,
        organization_id=organization_id,
        inventory_item_id=destination_item.id,
        movement_type="transfer_in",
        quantity=quantity,
        reason=reason,
        reference_type="inventory_transfer",
        reference_id=transfer_reference,
        performed_by_user_id=performed_by_user_id,
    )

    return outbound, inbound


def reserve_stock(
    db: Session,
    organization_id,
    inventory_item_id,
    quantity,
):
    item = get_inventory_item(
        db,
        organization_id,
        inventory_item_id,
    )

    if item is None:
        raise ValueError("Inventory item not found")

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError(
            "Reservation quantity must be greater than zero"
        )

    available = (
        Decimal(str(item.quantity))
        - Decimal(str(item.reserved_quantity))
    )

    if quantity > available:
        raise ValueError(
            "Insufficient available inventory"
        )

    item.reserved_quantity = (
        Decimal(str(item.reserved_quantity))
        + quantity
    )

    db.flush()

    return item


def release_stock(
    db: Session,
    organization_id,
    inventory_item_id,
    quantity,
):
    item = get_inventory_item(
        db,
        organization_id,
        inventory_item_id,
    )

    if item is None:
        raise ValueError("Inventory item not found")

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise ValueError(
            "Release quantity must be greater than zero"
        )

    reserved = Decimal(str(item.reserved_quantity))

    if quantity > reserved:
        raise ValueError(
            "Cannot release more stock than reserved"
        )

    item.reserved_quantity = reserved - quantity

    db.flush()

    return item
