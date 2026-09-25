import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.notifications.schemas import NotificationCreate
from app.notifications.service import (
    create_notification,
    get_unread_count,
    list_notifications,
    mark_notification_read,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.post("")
def create_notification_route(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_notification(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}")
def notifications(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_notifications(
        db,
        organization_id,
        current_user.id,
    )


@router.get("/{organization_id}/unread-count")
def unread_count(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "unread_count": get_unread_count(
            db,
            organization_id,
            current_user.id,
        )
    }


@router.patch("/{organization_id}/{notification_id}/read")
def mark_read(
    organization_id: uuid.UUID,
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return mark_notification_read(
            db,
            organization_id,
            current_user.id,
            notification_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
