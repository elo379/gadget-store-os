from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.inventory.ledger import InventoryMovement
from app.inventory.models import InventoryItem, InventoryLocation
from app.inventory.service import (
    create_inventory_item,
    create_location,
    get_inventory_movements,
    record_movement,
)
from app.models import Organization
from app.products.service import create_product


def build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, Session(engine)


def test_inventory_tables_registered():
    assert "inventory_locations" in Base.metadata.tables
    assert "inventory_items" in Base.metadata.tables
    assert "inventory_movements" in Base.metadata.tables


def test_inventory_item_requires_same_organization_product():
    engine, db = build_session()

    first = Organization(name="Store One", slug="store-one")
    second = Organization(name="Store Two", slug="store-two")

    db.add_all([first, second])
    db.flush()

    product = create_product(
        db=db,
        organization_id=first.id,
        name="Phone",
        sku="PHONE-001",
    )

    try:
        create_inventory_item(
            db=db,
            organization_id=second.id,
            product_id=product.id,
        )
        assert False
    except ValueError as exc:
        assert "Product does not belong" in str(exc)

    db.close()
    engine.dispose()


def test_inventory_movement_updates_quantity_and_creates_ledger():
    engine, db = build_session()

    organization = Organization(
        name="Store",
        slug="store",
    )
    db.add(organization)
    db.flush()

    product = create_product(
        db=db,
        organization_id=organization.id,
        name="Phone",
        sku="PHONE-001",
    )

    item = create_inventory_item(
        db=db,
        organization_id=organization.id,
        product_id=product.id,
        quantity=Decimal("5"),
    )

    movement = record_movement(
        db=db,
        organization_id=organization.id,
        inventory_item_id=item.id,
        movement_type="receive",
        quantity=Decimal("3"),
        reason="Supplier delivery",
    )

    assert item.quantity == Decimal("8")
    assert movement.quantity_before == Decimal("5")
    assert movement.quantity_after == Decimal("8")

    history = get_inventory_movements(
        db=db,
        organization_id=organization.id,
        inventory_item_id=item.id,
    )

    assert len(history) == 2
    assert history[-1].movement_type == "receive"

    db.close()
    engine.dispose()


def test_inventory_cannot_go_negative():
    engine, db = build_session()

    organization = Organization(
        name="Store",
        slug="store",
    )
    db.add(organization)
    db.flush()

    product = create_product(
        db=db,
        organization_id=organization.id,
        name="Phone",
        sku="PHONE-001",
    )

    item = create_inventory_item(
        db=db,
        organization_id=organization.id,
        product_id=product.id,
        quantity=Decimal("2"),
    )

    try:
        record_movement(
            db=db,
            organization_id=organization.id,
            inventory_item_id=item.id,
            movement_type="sale",
            quantity=Decimal("-3"),
        )
        assert False
    except ValueError as exc:
        assert "cannot be negative" in str(exc)

    db.close()
    engine.dispose()
