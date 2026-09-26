import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.devices.models import DeviceRecord
from app.inventory.constants import MOVEMENT_SALE
from app.inventory.models import InventoryItem
from app.inventory.service import record_movement
from app.products.models import Product
from app.sales.models import Sale, SaleLine, SalePayment
from app.sales.schemas import SaleCreate


def create_sale(db: Session, payload: SaleCreate):
    existing = db.scalar(
        select(Sale).where(
            Sale.organization_id == payload.organization_id,
            Sale.reference_number == payload.reference_number,
        )
    )
    if existing is not None:
        raise ValueError("Sale reference already exists")

    subtotal = Decimal("0")
    cogs = Decimal("0")
    lines = []

    for item in payload.lines:
        product = db.scalar(
            select(Product).where(
                Product.id == item.product_id,
                Product.organization_id == payload.organization_id,
                Product.is_active.is_(True),
            )
        )
        if product is None:
            raise ValueError("Product not found")

        inventory_query = select(InventoryItem).where(
            InventoryItem.organization_id == payload.organization_id,
            InventoryItem.product_id == product.id,
            InventoryItem.status == "active",
        )

        if item.location_id is not None:
            inventory_query = inventory_query.where(
                InventoryItem.location_id == item.location_id
            )

        inventories = list(db.scalars(inventory_query).all())

        if not inventories:
            raise ValueError("Inventory not found")

        if item.location_id is None and len(inventories) > 1:
            raise ValueError("Inventory location required")

        inventory = inventories[0]

        quantity = Decimal(item.quantity)

        if inventory.quantity - inventory.reserved_quantity < quantity:
            raise ValueError("Insufficient inventory")

        device = None
        if product.is_serialized:
            if item.device_id is None:
                raise ValueError("Serialized products require device_id")

            if quantity != Decimal("1"):
                raise ValueError("Serialized products require quantity of 1")

            device = db.scalar(
                select(DeviceRecord).where(
                    DeviceRecord.id == item.device_id,
                    DeviceRecord.organization_id == payload.organization_id,
                    DeviceRecord.product_id == product.id,
                    DeviceRecord.is_active.is_(True),
                )
            )

            if device is None:
                raise ValueError("Device not found")

            if device.status not in {"received", "active"}:
                raise ValueError("Device is not available for sale")

            unit_cost = device.acquisition_cost or Decimal("0")
            device.status = "sold"

        else:
            if item.device_id is not None:
                raise ValueError("Non-serialized products cannot use device_id")

            unit_cost = inventory.average_unit_cost

        line_total = Decimal(item.unit_price) * quantity
        line_cogs = unit_cost * quantity

        record_movement(
            db=db,
            organization_id=payload.organization_id,
            inventory_item_id=inventory.id,
            movement_type=MOVEMENT_SALE,
            quantity=-quantity,
            reason=f"Sale {payload.reference_number}",
            performed_by_user_id=payload.sold_by_user_id,
        )

        lines.append(
            SaleLine(
                product_id=product.id,
                device_id=device.id if device else None,
                quantity=quantity,
                unit_price=item.unit_price,
                unit_cost=unit_cost,
                line_total=line_total,
                line_cogs=line_cogs,
            )
        )

        subtotal += line_total
        cogs += line_cogs

    discount = Decimal(payload.discount)
    if discount < 0 or discount > subtotal:
        raise ValueError("Invalid discount")

    total = subtotal - discount
    gross_profit = total - cogs

    sale = Sale(
        organization_id=payload.organization_id,
        customer_id=payload.customer_id,
        sold_by_user_id=payload.sold_by_user_id,
        reference_number=payload.reference_number,
        status="completed",
        subtotal=subtotal,
        discount=discount,
        total=total,
        cogs=cogs,
        gross_profit=gross_profit,
        notes=payload.notes,
    )

    sale.lines = lines
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def add_sale_payment(
    db: Session,
    sale_id: uuid.UUID,
    payment_method: str,
    amount: Decimal,
    reference: str = "",
    notes: str = "",
):
    sale = db.get(Sale, sale_id)
    if sale is None:
        raise ValueError("Sale not found")

    if sale.status != "completed":
        raise ValueError("Sale is not payable")

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")

    paid = db.scalar(
        select(func.coalesce(func.sum(SalePayment.amount), 0)).where(
            SalePayment.sale_id == sale.id
        )
    )
    paid = Decimal(paid or 0)

    if paid + amount > sale.total:
        raise ValueError("Payment exceeds sale total")

    payment = SalePayment(
        sale_id=sale.id,
        payment_method=payment_method.strip(),
        amount=amount,
        reference=reference.strip(),
        notes=notes.strip(),
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_sales_summary(db: Session, organization_id: uuid.UUID):
    result = db.execute(
        select(
            func.coalesce(func.sum(Sale.total), 0),
            func.coalesce(func.sum(Sale.cogs), 0),
            func.coalesce(func.sum(Sale.gross_profit), 0),
            func.count(Sale.id),
        ).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    ).one()

    return {
        "total_sales": Decimal(result[0] or 0),
        "total_cogs": Decimal(result[1] or 0),
        "gross_profit": Decimal(result[2] or 0),
        "sale_count": int(result[3] or 0),
    }

def get_sale(
    db: Session,
    organization_id: uuid.UUID,
    sale_id: uuid.UUID,
):
    sale = db.scalar(
        select(Sale).where(
            Sale.id == sale_id,
            Sale.organization_id == organization_id,
        )
    )

    if sale is None:
        raise ValueError("Sale not found")

    return sale

def list_sales(
    db: Session,
    organization_id: uuid.UUID,
):
    return db.scalars(
        select(Sale)
        .where(Sale.organization_id == organization_id)
        .order_by(Sale.created_at.desc())
    ).all()
