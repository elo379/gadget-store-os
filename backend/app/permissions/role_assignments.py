from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.permissions.membership_roles import MembershipRole
from app.permissions.models import Role


def assign_configured_category_role(db: Session, membership: Membership) -> None:
    role = db.scalar(select(Role).where(
        Role.organization_id == membership.organization_id,
        Role.name == membership.role_name.lower(),
        Role.is_active.is_(True),
    ))
    if role is None:
        return
    existing = db.scalar(select(MembershipRole).where(
        MembershipRole.membership_id == membership.id,
        MembershipRole.role_id == role.id,
    ))
    if existing is None:
        db.add(MembershipRole(membership_id=membership.id, role_id=role.id))
        db.flush()
