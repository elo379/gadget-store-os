import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.organizations.authority import get_membership_for_user


def get_personnel(
    db: Session,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.organization_id == organization_id,
        )
    )


def can_manage_personnel(
    db: Session,
    actor: Membership,
    target: Membership,
) -> bool:
    if actor.organization_id != target.organization_id:
        return False

    if not actor.is_active or not target.is_active:
        return False

    if actor.is_owner:
        return not target.is_owner

    if actor.role_name.lower() != "manager":
        return False

    return target.parent_membership_id == actor.id


def suspend_personnel(
    db: Session,
    actor: Membership,
    target: Membership,
) -> Membership:
    if not can_manage_personnel(db, actor, target):
        raise ValueError(
            "You are not authorized to suspend this personnel"
        )

    if target.account_status != "active":
        raise ValueError(
            "Only active personnel can be suspended"
        )

    target.account_status = "suspended"
    target.is_active = False
    db.flush()

    return target


def reactivate_personnel(
    db: Session,
    actor: Membership,
    target: Membership,
) -> Membership:
    if actor.organization_id != target.organization_id:
        raise ValueError(
            "Personnel belongs to another organization"
        )

    if not actor.is_active:
        raise ValueError(
            "Actor membership is inactive"
        )

    if not actor.is_owner:
        if actor.role_name.lower() != "manager":
            raise ValueError(
                "Only owners or managers can reactivate personnel"
            )

        if target.parent_membership_id != actor.id:
            raise ValueError(
                "Manager can only reactivate direct personnel"
            )

    if target.account_status != "suspended":
        raise ValueError(
            "Only suspended personnel can be reactivated"
        )

    target.account_status = "active"
    target.is_active = True
    db.flush()

    return target


def revoke_personnel(
    db: Session,
    actor: Membership,
    target: Membership,
) -> Membership:
    if not actor.is_owner:
        raise ValueError(
            "Only the owner can revoke personnel"
        )

    if actor.organization_id != target.organization_id:
        raise ValueError(
            "Personnel belongs to another organization"
        )

    if target.is_owner:
        raise ValueError(
            "The owner account cannot be revoked"
        )

    if target.account_status == "revoked":
        raise ValueError(
            "Personnel is already revoked"
        )

    target.account_status = "revoked"
    target.is_active = False
    db.flush()

    return target
