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
from app.customers.models import Customer
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction
from app.aftersales.models import Warranty
from datetime import date, timedelta
from app.notifications.models import Notification


def _create_sale(db: Session, payload: SaleCreate):
    existing = db.scalar(
        select(Sale).where(
            Sale.organization_id == payload.organization_id,
            Sale.reference_number == payload.reference_number,
        )
    )
    if existing is not None:
        raise ValueError("Sale reference already exists")

    if payload.customer_id is not None and db.scalar(select(Customer).where(
        Customer.id == payload.customer_id,
        Customer.organization_id == payload.organization_id,
        Customer.is_active.is_(True),
    )) is None:
        raise ValueError("Customer not found")

    subtotal = Decimal("0")
    cogs = Decimal("0")
    lines = []
    stock_movements = []

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

        inventories = list(db.scalars(inventory_query.with_for_update()).all())

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

            if device.status not in {"in_stock", "received", "active"}:
                raise ValueError("Device is not available for sale")
            if device.location_id is not None and device.location_id != inventory.location_id:
                raise ValueError("Device is not at the selected inventory location")

            unit_cost = device.acquisition_cost or Decimal("0")
            device.status = "sold"

        else:
            if item.device_id is not None:
                raise ValueError("Non-serialized products cannot use device_id")

            unit_cost = inventory.average_unit_cost

        line_total = Decimal(item.unit_price) * quantity
        line_cogs = unit_cost * quantity

        stock_movements.append(record_movement(
            db=db,
            organization_id=payload.organization_id,
            inventory_item_id=inventory.id,
            movement_type=MOVEMENT_SALE,
            quantity=-quantity,
            reason=f"Sale {payload.reference_number}",
            reference_type="sale",
            reference_id=None,
            performed_by_user_id=payload.sold_by_user_id,
        ))

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

    taxable = subtotal - discount
    total = taxable + Decimal(payload.tax) + Decimal(payload.fees)
    gross_profit = taxable - cogs

    sale = Sale(
        organization_id=payload.organization_id,
        customer_id=payload.customer_id,
        sold_by_user_id=payload.sold_by_user_id,
        reference_number=payload.reference_number,
        status="completed",
        payment_status="unpaid",
        subtotal=subtotal,
        discount=discount,
        tax=payload.tax,
        fees=payload.fees,
        total=total,
        cogs=cogs,
        gross_profit=gross_profit,
        notes=payload.notes,
    )

    sale.lines = lines
    db.add(sale)
    try:
        db.flush()
        if payload.amount_paid:
            if not payload.payment_method or payload.amount_paid > sale.total:
                raise ValueError("A valid payment method and amount are required")
            payment = SalePayment(
                sale_id=sale.id, payment_method=payload.payment_method.strip(),
                amount=payload.amount_paid, reference=payload.payment_reference.strip(),
            )
            db.add(payment)
            sale.payment_status = "paid" if payload.amount_paid == sale.total else "partial"
            db.flush()
            db.add(FinancialTransaction(
                organization_id=sale.organization_id, transaction_type="payment", direction="credit",
                amount=payment.amount, reference_type="payment", reference_id=payment.id,
                description=f"Payment for sale {sale.reference_number}", actor_id=payload.sold_by_user_id,
            ))
            db.add(AuditLog(
                organization_id=sale.organization_id, user_id=payload.sold_by_user_id,
                action="sale.payment_added", entity_type="sale_payment", entity_id=payment.id,
                description=f"Payment received for sale {sale.reference_number}", metadata_json="{}",
            ))
        elif payload.payment_method:
            raise ValueError("Payment method requires a positive amount")
        db.add_all([
            FinancialTransaction(
                organization_id=sale.organization_id, transaction_type="sale", direction="credit",
                amount=sale.total, reference_type="sale", reference_id=sale.id,
                description=f"Revenue from sale {sale.reference_number}", actor_id=payload.sold_by_user_id,
            ),
            FinancialTransaction(
                organization_id=sale.organization_id, transaction_type="cogs", direction="debit",
                amount=sale.cogs, reference_type="sale", reference_id=sale.id,
                description=f"COGS from sale {sale.reference_number}", actor_id=payload.sold_by_user_id,
            ),
        ])
        for line in lines:
            if line.device_id:
                db.add(Warranty(
                    organization_id=sale.organization_id, device_id=line.device_id,
                    customer_id=sale.customer_id, sale_id=sale.id,
                    starts_at=date.today(),
                    ends_at=date.today() + timedelta(days=365),
                    coverage="manufacturer", status="active",
                ))
        for movement in stock_movements:
            movement.reference_id = sale.id
        db.add(AuditLog(
            organization_id=payload.organization_id,
            user_id=payload.sold_by_user_id,
            action="sale.completed",
            entity_type="sale",
            entity_id=sale.id,
            description=f"Sale {sale.reference_number} completed",
            metadata_json="{}",
        ))
        if payload.sold_by_user_id is not None:
            db.add(Notification(
                organization_id=sale.organization_id, user_id=payload.sold_by_user_id,
                notification_type="sale.completed", title="Sale completed",
                message=f"Sale {sale.reference_number} completed for {sale.total}.",
                reference_type="sale", reference_id=sale.id,
            ))
        db.flush()
        db.refresh(sale)
        return sale
    except Exception:
        db.rollback()
        raise


def add_sale_payment(
    db: Session,
    sale_id: uuid.UUID,
    payment_method: str,
    amount: Decimal,
    reference: str = "",
    notes: str = "",
    performed_by_user_id: uuid.UUID | None = None,
):
    sale = db.scalar(select(Sale).where(Sale.id == sale_id).with_for_update())
    if sale is None:
        raise ValueError("Sale not found")

    if sale.status != "completed":
        raise ValueError("Sale is not payable")

    if amount <= 0:
        raise ValueError("Payment amount must be greater than zero")

    if reference.strip() and db.scalar(select(SalePayment.id).where(
        SalePayment.sale_id == sale.id,
        SalePayment.reference == reference.strip(),
    )) is not None:
        raise ValueError("Payment reference already exists for this sale")

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
    db.flush()
    sale.payment_status = "paid" if paid + amount == sale.total else "partial"
    db.add(FinancialTransaction(
        organization_id=sale.organization_id, transaction_type="payment", direction="credit",
        amount=payment.amount, reference_type="payment", reference_id=payment.id,
        description=f"Payment for sale {sale.reference_number}", actor_id=performed_by_user_id,
    ))
    db.add(AuditLog(
        organization_id=sale.organization_id,
        user_id=performed_by_user_id,
        action="sale.payment_added",
        entity_type="sale_payment",
        entity_id=payment.id,
        description=f"Payment added to sale {sale.reference_number}",
        metadata_json="{}",
    ))
    db.flush()
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
        "revenue": Decimal(result[0] or 0),
        "cogs": Decimal(result[1] or 0),
        "sales_count": int(result[3] or 0),
        "gross_profit": Decimal(result[2] or 0),
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


def create_sale(db: Session, payload: SaleCreate):
    """Create a sale atomically; any validation or persistence failure rolls back stock and devices."""
    try:
        return _create_sale(db, payload)
    except Exception:
        db.rollback()
        raise

def list_sales(
    db: Session,
    organization_id: uuid.UUID,
):
    return db.scalars(
        select(Sale)
        .where(Sale.organization_id == organization_id)
        .order_by(Sale.created_at.desc())
    ).all()
