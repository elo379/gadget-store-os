import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.customers.models import Customer
from app.devices.models import DeviceRecord
from app.expenses.models import Expense
from app.inventory.models import InventoryItem
from app.products.models import Product
from app.sales.models import Sale, SalePayment
from app.staff.models import StaffProfile


def get_dashboard_summary(
    db: Session,
    organization_id: uuid.UUID,
):
    today = datetime.now(timezone.utc).date().isoformat()
    revenue = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    cogs = db.scalar(
        select(func.coalesce(func.sum(Sale.cogs), 0)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id,
            Expense.status.in_(["recorded", "approved", "paid"]),
        )
    )

    product_count = db.scalar(
        select(func.count(Product.id)).where(
            Product.organization_id == organization_id,
            Product.is_active.is_(True),
        )
    )

    customer_count = db.scalar(
        select(func.count(Customer.id)).where(
            Customer.organization_id == organization_id,
            Customer.is_active.is_(True),
        )
    )

    staff_count = db.scalar(
        select(func.count(StaffProfile.id)).where(
            StaffProfile.organization_id == organization_id,
            StaffProfile.is_active.is_(True),
        )
    )

    device_count = db.scalar(
        select(func.count(DeviceRecord.id)).where(
            DeviceRecord.organization_id == organization_id,
            DeviceRecord.is_active.is_(True),
        )
    )

    inventory_quantity = db.scalar(
        select(
            func.coalesce(func.sum(InventoryItem.quantity), 0)
        ).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
        )
    )

    revenue = Decimal(str(revenue or 0))
    cogs = Decimal(str(cogs or 0))
    expenses = Decimal(str(expenses or 0))

    gross_profit = revenue - cogs
    operating_result = gross_profit - expenses

    today_sales = db.scalars(
        select(Sale).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
            func.date(Sale.created_at) == today,
        )
    ).all()
    today_revenue = sum((Decimal(str(sale.total or 0)) for sale in today_sales), Decimal("0"))
    today_gross_profit = sum((Decimal(str(sale.gross_profit or 0)) for sale in today_sales), Decimal("0"))
    payments_by_sale = (
        select(SalePayment.sale_id, func.sum(SalePayment.amount).label("paid"))
        .group_by(SalePayment.sale_id)
        .subquery()
    )
    outstanding = db.scalar(
        select(func.coalesce(func.sum(Sale.total - func.coalesce(payments_by_sale.c.paid, 0)), 0))
        .outerjoin(payments_by_sale, payments_by_sale.c.sale_id == Sale.id)
        .where(Sale.organization_id == organization_id, Sale.status == "completed")
    )

    return {
        "organization_id": organization_id,
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "expenses": expenses,
        "operating_result": operating_result,
        "today_revenue": today_revenue,
        "today_sales_count": len(today_sales),
        "today_gross_profit": today_gross_profit,
        "outstanding": Decimal(str(outstanding or 0)),
        "product_count": product_count or 0,
        "customer_count": customer_count or 0,
        "staff_count": staff_count or 0,
        "device_count": device_count or 0,
        "inventory_quantity": Decimal(
            str(inventory_quantity or 0)
        ),
    }


def get_operational_metrics(
    db: Session,
    organization_id: uuid.UUID,
):
    sales_count = db.scalar(
        select(func.count(Sale.id)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    sales_total = db.scalar(
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    active_inventory = db.scalar(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
            InventoryItem.quantity > 0,
        )
    )

    out_of_stock = db.scalar(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
            InventoryItem.quantity <= 0,
        )
    )

    active_devices = db.scalar(
        select(func.count(DeviceRecord.id)).where(
            DeviceRecord.organization_id == organization_id,
            DeviceRecord.is_active.is_(True),
            DeviceRecord.status.in_(["received", "active"]),
        )
    )

    active_staff = db.scalar(
        select(func.count(StaffProfile.id)).where(
            StaffProfile.organization_id == organization_id,
            StaffProfile.is_active.is_(True),
        )
    )

    active_customers = db.scalar(
        select(func.count(Customer.id)).where(
            Customer.organization_id == organization_id,
            Customer.is_active.is_(True),
        )
    )

    return {
        "organization_id": organization_id,
        "sales_count": sales_count or 0,
        "sales_total": Decimal(str(sales_total or 0)),
        "active_inventory_items": active_inventory or 0,
        "out_of_stock_items": out_of_stock or 0,
        "active_devices": active_devices or 0,
        "active_staff": active_staff or 0,
        "active_customers": active_customers or 0,
    }


def get_low_stock_inventory(
    db: Session,
    organization_id: uuid.UUID,
    threshold: Decimal | None = None,
):
    rows = db.execute(
        select(InventoryItem, Product).join(Product, Product.id == InventoryItem.product_id).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
        ).order_by(InventoryItem.quantity.asc())
    ).all()

    result = []
    for item, product in rows:
        reorder_at = Decimal(str(threshold)) if threshold is not None else max(
            Decimal(str(item.reorder_threshold or 0)), Decimal(str(product.reorder_threshold or 0))
        )
        quantity = Decimal(str(item.quantity))
        if quantity > reorder_at or (reorder_at <= 0 and quantity > 0):
            continue
        result.append({
            "inventory_item_id": item.id,
            "product_id": item.product_id,
            "location_id": item.location_id,
            "quantity": quantity,
            "reorder_threshold": reorder_at,
            "stock_status": "out_of_stock" if quantity <= 0 else "low_stock",
        })
    return result
