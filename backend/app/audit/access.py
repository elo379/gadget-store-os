import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.permissions.access import user_has_permission


def can_view_audit(
    db: Session,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> bool:
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
        )
    )

    if membership is None:
        return False

    if membership.is_owner:
        return True

    return user_has_permission(
        db,
        user_id,
        organization_id,
        "audit.view",
    )
