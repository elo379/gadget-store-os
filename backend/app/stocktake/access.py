import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.user import User
from app.permissions.access import user_has_permission


def require_stocktake_access(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
    *,
    manage: bool = False,
):
    user_id = uuid.UUID(str(getattr(user, "user_id", getattr(user, "id", ""))))
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )
    )

    if membership is None:
        raise ValueError("Organization access denied")

    if membership.is_owner:
        return membership

    permission = "inventory.manage" if manage else "inventory.view"
    if not user_has_permission(
        db,
        user_id,
        organization_id,
        permission,
    ):
        raise ValueError("Stocktake management permission required" if manage else "Stocktake access denied")

    return membership
