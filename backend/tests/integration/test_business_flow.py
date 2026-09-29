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
from app.sales.service import add_sale_payment, create_sale
from app.customers.returns import process_return
from app.sales.models import SaleLine
from app.inventory.ledger import InventoryMovement
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction
from app.aftersales.models import Warranty, RepairCase
from app.customers.models import Customer
from app.devices.models import DeviceRecord
from app.products.models import Product


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


def test_duplicate_sale_reference_does_not_deduct_twice(db):
    organization = create_organization(
        db=db, name="Duplicate Store", slug=f"dup-{uuid.uuid4().hex[:8]}",
        owner_email=f"dup-{uuid.uuid4().hex[:8]}@example.com", owner_password="StrongPassword123!",
    )
    product = create_product(db, organization.id, "Cable", f"CAB-{uuid.uuid4().hex[:8]}")
    location = create_location(db, organization.id, "Main")
    inventory = create_inventory_item(db, organization.id, product.id, location.id, 3)
    db.commit()
    reference = f"SALE-{uuid.uuid4().hex[:8]}"
    payload = SaleCreate(
        organization_id=organization.id, reference_number=reference,
        lines=[SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=10)],
    )
    create_sale(db, payload)
    db.commit()
    with pytest.raises(ValueError, match="reference already exists"):
        create_sale(db, payload)
    db.refresh(inventory)
    assert inventory.quantity == 2


def test_invalid_later_line_rolls_back_earlier_stock_deduction(db):
    organization = create_organization(
        db=db, name="Rollback Store", slug=f"rollback-{uuid.uuid4().hex[:8]}",
        owner_email=f"rollback-{uuid.uuid4().hex[:8]}@example.com", owner_password="StrongPassword123!",
    )
    product = create_product(db, organization.id, "Cable", f"CAB-{uuid.uuid4().hex[:8]}")
    location = create_location(db, organization.id, "Main")
    inventory = create_inventory_item(db, organization.id, product.id, location.id, 2)
    db.commit()
    payload = SaleCreate(
        organization_id=organization.id, reference_number=f"SALE-{uuid.uuid4().hex[:8]}",
        lines=[
            SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=10),
            SaleLineCreate(product_id=uuid.uuid4(), location_id=location.id, quantity=1, unit_price=10),
        ],
    )
    with pytest.raises(ValueError, match="Product not found"):
        create_sale(db, payload)
    db.refresh(inventory)
    assert inventory.quantity == 2


def test_sale_payment_state_tracks_partial_and_full_payment(db):
    organization = create_organization(
        db=db, name="Payment Store", slug=f"payment-{uuid.uuid4().hex[:8]}",
        owner_email=f"payment-{uuid.uuid4().hex[:8]}@example.com", owner_password="StrongPassword123!",
    )
    product = create_product(db, organization.id, "Charger", f"CHG-{uuid.uuid4().hex[:8]}")
    location = create_location(db, organization.id, "Main")
    create_inventory_item(db, organization.id, product.id, location.id, 1)
    db.commit()
    sale = create_sale(db, SaleCreate(
        organization_id=organization.id, reference_number=f"SALE-{uuid.uuid4().hex[:8]}",
        lines=[SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=10)],
    ))
    add_sale_payment(db, sale.id, "cash", 4)
    assert sale.payment_status == "partial"
    add_sale_payment(db, sale.id, "cash", 6)
    assert sale.payment_status == "paid"


def test_return_restores_stock_and_rejects_cumulative_over_return(db):
    organization = create_organization(
        db=db, name="Return Store", slug=f"return-{uuid.uuid4().hex[:8]}",
        owner_email=f"return-{uuid.uuid4().hex[:8]}@example.com", owner_password="StrongPassword123!",
    )
    product = create_product(db, organization.id, "Cable", f"RET-{uuid.uuid4().hex[:8]}")
    location = create_location(db, organization.id, "Main")
    inventory = create_inventory_item(db, organization.id, product.id, location.id, 2)
    db.commit()
    sale = create_sale(db, SaleCreate(
        organization_id=organization.id,
        reference_number=f"SALE-{uuid.uuid4().hex[:8]}",
        lines=[SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=10)],
    ))
    db.commit()
    sale_line = db.query(SaleLine).filter_by(sale_id=sale.id).one()
    args = dict(
        organization_id=organization.id,
        sale_id=sale.id,
        lines=[{"sale_line_id": sale_line.id, "quantity": 1, "location_id": location.id}],
    )
    result = process_return(db, reference_number=f"RET-{uuid.uuid4().hex[:8]}", **args)
    db.commit()
    db.refresh(inventory)
    assert inventory.quantity == 2
    movement = db.query(InventoryMovement).filter_by(movement_type="return").one()
    assert movement.reference_id == result.id
    assert db.query(AuditLog).filter_by(entity_id=result.id, action="customer_return.completed").one()
    with pytest.raises(ValueError, match="Invalid return quantity"):
        process_return(db, reference_number=f"RET-{uuid.uuid4().hex[:8]}", **args)
    db.refresh(inventory)
    assert inventory.quantity == 2


def test_serialized_sale_payment_warranty_return_repair_lifecycle(db):
    organization = create_organization(db, "Lifecycle Store", f"life-{uuid.uuid4().hex[:8]}", f"life-{uuid.uuid4().hex[:8]}@example.com", "StrongPassword123!")
    owner = organization.memberships[0].user
    customer = Customer(organization_id=organization.id, name="Lifecycle Customer")
    product = create_product(db, organization.id, "Lifecycle Phone", f"LIFE-{uuid.uuid4().hex[:8]}", is_serialized=True)
    location = create_location(db, organization.id, "Main")
    inventory = create_inventory_item(db, organization.id, product.id, location.id, 1)
    device = DeviceRecord(organization_id=organization.id, product_id=product.id, imei="123456789012345", status="received", acquisition_cost=50, location_id=location.id)
    db.add_all([customer, device])
    db.flush()
    sale = create_sale(db, SaleCreate(
        organization_id=organization.id, customer_id=customer.id, reference_number=f"LIFE-{uuid.uuid4().hex[:8]}",
        lines=[SaleLineCreate(product_id=product.id, location_id=location.id, quantity=1, unit_price=100, device_id=device.id)],
        payment_method="cash", amount_paid=100,
    ))
    db.flush()
    db.refresh(inventory)
    assert inventory.quantity == 0
    assert device.status == "sold"
    assert sale.payment_status == "paid"
    assert sale.customer_id == customer.id
    assert db.query(Warranty).filter_by(sale_id=sale.id, device_id=device.id).one()
    tx = db.query(FinancialTransaction).filter_by(reference_type="sale", reference_id=sale.id).all()
    assert {record.transaction_type for record in tx} == {"sale", "cogs"}
    assert sale.cogs == 50 and sale.gross_profit == 50
    sale_line = db.query(SaleLine).filter_by(sale_id=sale.id).one()
    ret = process_return(db, organization.id, sale.id, f"RET-{uuid.uuid4().hex[:8]}", [{"sale_line_id": sale_line.id, "quantity": 1, "location_id": location.id, "disposition": "SERVICE", "condition": "faulty"}], performed_by_user_id=owner.id)
    db.flush()
    assert ret.lines[0].original_cost == 50
    assert ret.lines[0].disposition == "SERVICE"
    assert device.status == "service"
    assert db.query(FinancialTransaction).filter_by(reference_type="customer_return", reference_id=ret.id, transaction_type="refund").one()
    repair = RepairCase(organization_id=organization.id, device_id=device.id, customer_id=customer.id, reference_number=f"REP-{uuid.uuid4().hex[:8]}")
    db.add(repair)
    db.flush()
    assert repair.device_id == device.id and repair.customer_id == customer.id
