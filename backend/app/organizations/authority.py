import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.organizations.store_tree import get_or_create_store_tree_policy


def can_create_personnel(
    db: Session,
    creator_membership: Membership,
    organization_id: uuid.UUID,
    target_role: str,
) -> bool:
    if creator_membership.organization_id != organization_id:
        return False

    if not creator_membership.is_active:
        return False

    role = target_role.lower()

    if role not in {"manager", "staff"}:
        return False

    if creator_membership.is_owner:
        return True

    if creator_membership.role_name.lower() != "manager":
        return False

    policy = get_or_create_store_tree_policy(
        db,
        organization_id,
    )

    if role == "manager":
        return policy.managers_can_create_managers

    return policy.managers_can_create_staff


def require_personnel_creation_authority(
    db: Session,
    creator_membership: Membership,
    organization_id: uuid.UUID,
    target_role: str,
) -> None:
    if not can_create_personnel(
        db,
        creator_membership,
        organization_id,
        target_role,
    ):
        raise ValueError(
            "Creator is not authorized to create this personnel role"
        )


def get_membership_for_user(
    db: Session,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )
    )
