import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.user import User
from app.notifications.models import Notification
from app.notifications.schemas import NotificationCreate


def create_notification(
    db: Session,
    payload: NotificationCreate,
):
    user = db.scalar(
        select(User).where(
            User.id == payload.user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise ValueError("User not found")

    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.user_id == payload.user_id,
            Membership.is_active.is_(True),
        )
    )

    if membership is None:
        raise ValueError("User does not belong to organization")

    notification = Notification(
        organization_id=payload.organization_id,
        user_id=payload.user_id,
        notification_type=payload.notification_type.strip(),
        title=payload.title.strip(),
        message=payload.message.strip(),
        reference_type=payload.reference_type.strip(),
        reference_id=payload.reference_id,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(Notification).where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.is_active.is_(True),
            ).order_by(
                Notification.created_at.desc()
            )
        ).all()
    )


def get_unread_count(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
):
    return db.scalar(
        select(
            __import__("sqlalchemy").func.count(Notification.id)
        ).where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.is_active.is_(True),
            Notification.is_read.is_(False),
        )
    ) or 0


def mark_notification_read(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
):
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.is_active.is_(True),
        )
    )

    if notification is None:
        raise ValueError("Notification not found")

    notification.is_read = True

    db.commit()
    db.refresh(notification)
    return notification
