import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.permissions.membership_roles import MembershipRole
from app.permissions.models import Permission, RolePermission


def is_owner(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
            Membership.is_active.is_(True),
        )
    )

    return bool(membership and membership.is_owner)


def user_has_permission(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    permission_key: str,
) -> bool:
    if is_owner(db, organization_id, user_id):
        return True

    statement = (
        select(Permission.id)
        .join(
            RolePermission,
            RolePermission.permission_id == Permission.id,
        )
        .join(
            MembershipRole,
            MembershipRole.role_id == RolePermission.role_id,
        )
        .join(
            Membership,
            Membership.id == MembershipRole.membership_id,
        )
        .join(
            RolePermission,
            RolePermission.role_id == MembershipRole.role_id,
        )
        .where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
            Membership.is_active.is_(True),
            Permission.key == permission_key,
            Permission.is_active.is_(True),
        )
    )

    return db.scalar(statement) is not None
