import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.inventory.constants import MOVEMENT_RECEIVE
from app.inventory.models import InventoryItem
from app.inventory.service import (
    create_inventory_item,
    create_location,
    record_movement,
    release_stock,
    reserve_stock,
    transfer_stock,
)
from app.products.models import Product


def setup_database():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def create_product(db, organization_id, sku):
    product = Product(
        organization_id=organization_id,
        name="Test Phone",
        sku=sku,
        brand="Test",
        model="Model 1",
        description="",
        is_serialized=False,
        is_active=True,
    )
    db.add(product)
    db.flush()
    return product


def test_inventory_creation_starts_at_zero():
    engine = setup_database()
    organization_id = uuid.uuid4()

    with Session(engine) as db:
        product = create_product(
            db,
            organization_id,
            "SKU-001",
        )

        item = create_inventory_item(
            db,
            organization_id,
            product.id,
        )

        assert item.quantity == Decimal("0")
        assert item.reserved_quantity == Decimal("0")


def test_invalid_movement_type_rejected():
    engine = setup_database()
    organization_id = uuid.uuid4()

    with Session(engine) as db:
        product = create_product(
            db,
            organization_id,
            "SKU-002",
        )

        item = create_inventory_item(
            db,
            organization_id,
            product.id,
        )

        with pytest.raises(
            ValueError,
            match="Invalid inventory movement",
        ):
            record_movement(
                db,
                organization_id,
                item.id,
                "unknown_type",
                1,
            )


def test_transfer_moves_stock_between_locations():
    engine = setup_database()
    organization_id = uuid.uuid4()

    with Session(engine) as db:
        product = create_product(
            db,
            organization_id,
            "SKU-003",
        )

        source = create_location(
            db,
            organization_id,
            "Main Store",
        )

        destination = create_location(
            db,
            organization_id,
            "Back Store",
        )

        item = create_inventory_item(
            db,
            organization_id,
            product.id,
            source.id,
        )

        record_movement(
            db,
            organization_id,
            item.id,
            MOVEMENT_RECEIVE,
            10,
        )

        outbound, inbound = transfer_stock(
            db,
            organization_id,
            item.id,
            destination.id,
            4,
        )

        assert outbound.quantity == Decimal("-4")
        assert inbound.quantity == Decimal("4")
        assert item.quantity == Decimal("6")

        destination_record = db.get(
            InventoryItem,
            inbound.inventory_item_id,
        )

        assert destination_record.quantity == Decimal("4")


def test_reservation_and_release():
    engine = setup_database()
    organization_id = uuid.uuid4()

    with Session(engine) as db:
        product = create_product(
            db,
            organization_id,
            "SKU-004",
        )

        item = create_inventory_item(
            db,
            organization_id,
            product.id,
        )

        record_movement(
            db,
            organization_id,
            item.id,
            MOVEMENT_RECEIVE,
            10,
        )

        reserve_stock(
            db,
            organization_id,
            item.id,
            3,
        )

        assert item.reserved_quantity == Decimal("3")

        release_stock(
            db,
            organization_id,
            item.id,
            2,
        )

        assert item.reserved_quantity == Decimal("1")


def test_over_reservation_rejected():
    engine = setup_database()
    organization_id = uuid.uuid4()

    with Session(engine) as db:
        product = create_product(
            db,
            organization_id,
            "SKU-005",
        )

        item = create_inventory_item(
            db,
            organization_id,
            product.id,
        )

        record_movement(
            db,
            organization_id,
            item.id,
            MOVEMENT_RECEIVE,
            5,
        )

        with pytest.raises(
            ValueError,
            match="Insufficient available",
        ):
            reserve_stock(
                db,
                organization_id,
                item.id,
                6,
            )
