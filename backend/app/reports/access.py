import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.user import User
from app.permissions.access import user_has_permission


def require_reports_access(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
):
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user.id,
            Membership.is_active.is_(True),
        )
    )

    if membership is None:
        raise ValueError("Organization access denied")

    if membership.is_owner:
        return membership

    if not user_has_permission(
        db,
        user,
        organization_id,
        "reports.view",
    ):
        raise ValueError("Reports access denied")

    return membership
