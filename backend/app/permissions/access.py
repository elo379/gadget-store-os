import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.permissions.membership_roles import MembershipRole
from app.permissions.models import Permission, Role, RolePermission


def is_owner(
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

    return bool(membership and membership.is_owner)


def user_has_permission(
    db: Session,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    permission_name: str,
) -> bool:
    if is_owner(db, user_id, organization_id):
        return True

    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.is_active.is_(True),
        )
    )

    if membership is None:
        return False

    permission = db.scalar(
        select(Permission).where(
            Permission.key == permission_name,
            Permission.is_active.is_(True),
        )
    )

    if permission is None:
        return False

    assignment = db.scalar(
        select(MembershipRole)
        .join(
            Role,
            MembershipRole.role_id == Role.id,
        )
        .join(
            RolePermission,
            RolePermission.role_id == Role.id,
        )
        .where(
            MembershipRole.membership_id == membership.id,
            Role.organization_id == organization_id,
            Role.is_active.is_(True),
            RolePermission.permission_id == permission.id,
        )
    )

    return assignment is not None
