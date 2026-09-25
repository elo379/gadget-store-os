import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.customers.models import Customer
from app.expenses.models import Expense
from app.inventory.models import InventoryItem
from app.sales.models import Sale


def get_sales_report(
    db: Session,
    organization_id: uuid.UUID,
):
    sales = db.scalar(
        select(func.count(Sale.id)).where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    ) or 0

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

    revenue = Decimal(str(revenue or 0))
    cogs = Decimal(str(cogs or 0))

    return {
        "organization_id": organization_id,
        "sales_count": sales,
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": revenue - cogs,
    }


def get_expense_report(
    db: Session,
    organization_id: uuid.UUID,
):
    total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id,
            Expense.status.in_(
                ["recorded", "approved", "paid"]
            ),
        )
    )

    paid = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id,
            Expense.status == "paid",
        )
    )

    total = Decimal(str(total or 0))
    paid = Decimal(str(paid or 0))

    return {
        "organization_id": organization_id,
        "total_expenses": total,
        "paid_expenses": paid,
        "outstanding_expenses": total - paid,
    }


def get_inventory_report(
    db: Session,
    organization_id: uuid.UUID,
):
    total_items = db.scalar(
        select(func.count(InventoryItem.id)).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
        )
    ) or 0

    total_quantity = db.scalar(
        select(
            func.coalesce(
                func.sum(InventoryItem.quantity),
                0,
            )
        ).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
        )
    )

    reserved_quantity = db.scalar(
        select(
            func.coalesce(
                func.sum(InventoryItem.reserved_quantity),
                0,
            )
        ).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.status == "active",
        )
    )

    return {
        "organization_id": organization_id,
        "inventory_items": total_items,
        "total_quantity": Decimal(
            str(total_quantity or 0)
        ),
        "reserved_quantity": Decimal(
            str(reserved_quantity or 0)
        ),
    }


def get_customer_report(
    db: Session,
    organization_id: uuid.UUID,
):
    customers = db.scalar(
        select(func.count(Customer.id)).where(
            Customer.organization_id == organization_id,
            Customer.is_active.is_(True),
        )
    ) or 0

    return {
        "organization_id": organization_id,
        "active_customers": customers,
    }


def get_sales_period_report(
    db: Session,
    organization_id: uuid.UUID,
    start_date=None,
    end_date=None,
):
    conditions = [
        Sale.organization_id == organization_id,
        Sale.status == "completed",
    ]

    if start_date is not None:
        conditions.append(Sale.created_at >= start_date)

    if end_date is not None:
        conditions.append(Sale.created_at <= end_date)

    sales_count = db.scalar(
        select(func.count(Sale.id)).where(*conditions)
    ) or 0

    revenue = db.scalar(
        select(
            func.coalesce(func.sum(Sale.total), 0)
        ).where(*conditions)
    )

    cogs = db.scalar(
        select(
            func.coalesce(func.sum(Sale.cogs), 0)
        ).where(*conditions)
    )

    revenue = Decimal(str(revenue or 0))
    cogs = Decimal(str(cogs or 0))

    return {
        "organization_id": organization_id,
        "start_date": start_date,
        "end_date": end_date,
        "sales_count": sales_count,
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": revenue - cogs,
    }


def get_product_sales_report(
    db: Session,
    organization_id: uuid.UUID,
):
    from app.sales.models import SaleLine

    rows = db.execute(
        select(
            SaleLine.product_id,
            func.sum(SaleLine.quantity).label("quantity_sold"),
            func.sum(SaleLine.line_total).label("revenue"),
            func.sum(SaleLine.line_cogs).label("cogs"),
        )
        .join(Sale)
        .where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
        .group_by(SaleLine.product_id)
        .order_by(
            func.sum(SaleLine.line_total).desc()
        )
    ).all()

    return [
        {
            "product_id": row.product_id,
            "quantity_sold": Decimal(
                str(row.quantity_sold or 0)
            ),
            "revenue": Decimal(
                str(row.revenue or 0)
            ),
            "cogs": Decimal(
                str(row.cogs or 0)
            ),
            "gross_profit": (
                Decimal(str(row.revenue or 0))
                - Decimal(str(row.cogs or 0))
            ),
        }
        for row in rows
    ]


def get_staff_sales_report(
    db: Session,
    organization_id: uuid.UUID,
):
    rows = db.execute(
        select(
            Sale.sold_by_user_id,
            func.count(Sale.id).label("sales_count"),
            func.sum(Sale.total).label("revenue"),
            func.sum(Sale.cogs).label("cogs"),
        )
        .where(
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
        .group_by(Sale.sold_by_user_id)
        .order_by(
            func.sum(Sale.total).desc()
        )
    ).all()

    return [
        {
            "user_id": row.sold_by_user_id,
            "sales_count": row.sales_count,
            "revenue": Decimal(
                str(row.revenue or 0)
            ),
            "cogs": Decimal(
                str(row.cogs or 0)
            ),
            "gross_profit": (
                Decimal(str(row.revenue or 0))
                - Decimal(str(row.cogs or 0))
            ),
        }
        for row in rows
    ]
