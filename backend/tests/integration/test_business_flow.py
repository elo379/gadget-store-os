import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.organizations.service import create_organization
from app.products.service import create_product
from app.inventory.service import create_location
from app.inventory.service import create_inventory_item
from app.sales.schemas import SaleCreate, SaleLineCreate
from app.sales.service import create_sale


engine = create_engine("sqlite:///:memory:")


@pytest.fixture
def db():
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_product_inventory_sales_flow(db):
    organization = create_organization(
        db=db,
        name="Flow Store",
        slug=f"flow-{uuid.uuid4().hex[:8]}",
        owner_email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    owner = organization.memberships[0].user

    product = create_product(
        db=db,
        organization_id=organization.id,
        name="Integration Phone",
        sku=f"PHONE-{uuid.uuid4().hex[:8]}",
        brand="Test",
        model="Integration",
        is_serialized=False,
    )

    location = create_location(
        db=db,
        organization_id=organization.id,
        name="Main Store",
    )

    inventory = create_inventory_item(
        db=db,
        organization_id=organization.id,
        product_id=product.id,
        location_id=location.id,
        quantity=5,
    )

    sale = create_sale(
        db=db,
        payload=SaleCreate(
            organization_id=organization.id,
            sold_by_user_id=owner.id,
            reference_number=f"SALE-{uuid.uuid4().hex[:8]}",
            discount=0,
            lines=[
                SaleLineCreate(
                    product_id=product.id,
                    quantity=1,
                    unit_price=150000,
                )
            ],
        ),
    )

    db.refresh(inventory)
    db.refresh(sale)

    assert sale.total == 150000
    assert sale.cogs == 0
    assert sale.gross_profit == 150000
    assert inventory.quantity == 4
