import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.organizations.authority import get_membership_for_user
from app.organizations.personnel import create_personnel
from app.organizations.store_tree import get_or_create_store_tree_policy
from app.organizations.store_tree_schemas import (
    PersonnelCreate,
    StoreTreePolicyUpdate,
)


def get_store_tree(
    db: Session,
    organization_id: uuid.UUID,
) -> list[Membership]:
    return list(
        db.scalars(
            select(Membership)
            .where(
                Membership.organization_id == organization_id,
                Membership.is_active.is_(True),
            )
            .order_by(
                Membership.is_owner.desc(),
                Membership.role_name,
                Membership.personnel_id,
            )
        ).all()
    )


def get_store_tree_policy(
    db: Session,
    organization_id: uuid.UUID,
):
    return get_or_create_store_tree_policy(
        db,
        organization_id,
    )


def update_store_tree_policy(
    db: Session,
    organization_id: uuid.UUID,
    update: StoreTreePolicyUpdate,
):
    policy = get_or_create_store_tree_policy(
        db,
        organization_id,
    )

    policy.managers_can_create_staff = update.managers_can_create_staff
    policy.managers_can_create_managers = update.managers_can_create_managers
    policy.managers_can_assign_roles = update.managers_can_assign_roles
    policy.managers_can_modify_permissions = (
        update.managers_can_modify_permissions
    )

    db.flush()

    return policy


def create_store_tree_personnel(
    db: Session,
    organization_id: uuid.UUID,
    creator_user_id: uuid.UUID,
    payload: PersonnelCreate,
):
    creator = get_membership_for_user(
        db,
        organization_id,
        creator_user_id,
    )

    if creator is None:
        raise ValueError("Active organization membership not found")

    return create_personnel(
        db,
        organization_id,
        creator,
        payload.email,
        payload.password,
        payload.role_name,
    )
