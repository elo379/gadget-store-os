import uuid

from sqlalchemy.orm import Session

from app.notifications.schemas import NotificationCreate
from app.notifications.service import create_notification


def notify_user(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    message: str,
    reference_type: str = "",
    reference_id: uuid.UUID | None = None,
):
    payload = NotificationCreate(
        organization_id=organization_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
    )

    return create_notification(db, payload)


def notify_low_stock(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    product_name: str,
    quantity,
    inventory_item_id: uuid.UUID,
):
    return notify_user(
        db,
        organization_id,
        user_id,
        "low_stock",
        "Low stock alert",
        f"{product_name} has low stock. Current quantity: {quantity}.",
        "inventory_item",
        inventory_item_id,
    )


def notify_sale_completed(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    sale_id: uuid.UUID,
    reference_number: str,
    total,
):
    return notify_user(
        db,
        organization_id,
        user_id,
        "sale_completed",
        "Sale completed",
        f"Sale {reference_number} was completed. Total: {total}.",
        "sale",
        sale_id,
    )


def notify_inventory_event(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    inventory_item_id: uuid.UUID,
    title: str,
    message: str,
):
    return notify_user(
        db,
        organization_id,
        user_id,
        "inventory_event",
        title,
        message,
        "inventory_item",
        inventory_item_id,
    )
