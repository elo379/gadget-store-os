import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.permissions.models import Permission, Role, RolePermission
from app.permissions.membership_roles import MembershipRole


def create_permission(
    db: Session,
    key: str,
    description: str,
) -> Permission:
    existing = db.scalar(
        select(Permission).where(Permission.key == key)
    )

    if existing is not None:
        return existing

    permission = Permission(
        key=key,
        description=description,
        is_active=True,
    )

    db.add(permission)
    db.flush()

    return permission


def create_role(
    db: Session,
    organization_id: uuid.UUID,
    name: str,
    description: str = "",
    is_system: bool = False,
) -> Role:
    existing = db.scalar(
        select(Role).where(
            Role.organization_id == organization_id,
            Role.name == name,
        )
    )

    if existing is not None:
        raise ValueError("Role already exists")

    role = Role(
        organization_id=organization_id,
        name=name,
        description=description,
        is_system=is_system,
        is_active=True,
    )

    db.add(role)
    db.flush()

    return role


def assign_permission(
    db: Session,
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
) -> RolePermission:
    existing = db.scalar(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )

    if existing is not None:
        return existing

    assignment = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
    )

    db.add(assignment)
    db.flush()

    return assignment


def assign_role_to_membership(
    db: Session,
    membership_id: uuid.UUID,
    role_id: uuid.UUID,
) -> MembershipRole:
    existing = db.scalar(
        select(MembershipRole).where(
            MembershipRole.membership_id == membership_id,
            MembershipRole.role_id == role_id,
        )
    )

    if existing is not None:
        return existing

    assignment = MembershipRole(
        membership_id=membership_id,
        role_id=role_id,
    )

    db.add(assignment)
    db.flush()

    return assignment
