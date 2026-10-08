import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.audit.models import AuditLog
from app.db.dependencies import get_db
from app.models import Membership
from app.organizations.authority import get_membership_for_user
from app.permissions.access import user_has_permission
from app.permissions.catalog import PERMISSION_CATALOG, permission_keys
from app.permissions.membership_roles import MembershipRole
from app.permissions.models import Permission, Role, RolePermission
from app.permissions.role_assignments import assign_configured_category_role
from app.permissions.service import assign_permission, create_permission

router = APIRouter(prefix="", tags=["role-permissions"])


class RolePermissionUpdate(BaseModel):
    role_name: str = Field(min_length=1, max_length=100)
    permission_keys: list[str] = Field(max_length=27)


def _active_member(db: Session, user: AuthenticatedUser, organization_id: uuid.UUID):
    member = get_membership_for_user(db, organization_id, uuid.UUID(user.user_id))
    if member is None:
        raise HTTPException(status_code=403, detail="Active organization membership required")
    return member


@router.get("/{organization_id}/my-permissions")
def my_permissions(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    member = _active_member(db, user, organization_id)
    if member.is_owner:
        return {"permissions": permission_keys()}
    permissions = db.scalars(
        select(Permission.key)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(MembershipRole, MembershipRole.role_id == Role.id)
        .where(
            MembershipRole.membership_id == member.id,
            Role.organization_id == organization_id,
            Role.is_active.is_(True),
            Permission.is_active.is_(True),
        )
    ).all()
    return {"permissions": sorted(set(permissions))}


@router.get("/{organization_id}/role-permissions")
def get_role_permissions(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    member = _active_member(db, user, organization_id)
    if not member.is_owner and not user_has_permission(db, uuid.UUID(user.user_id), organization_id, "roles.view"):
        raise HTTPException(status_code=403, detail="Role view permission required")
    roles = {}
    for name in ("manager", "staff"):
        role = db.scalar(select(Role).where(Role.organization_id == organization_id, Role.name == name))
        roles[name] = [] if role is None else sorted(db.scalars(
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id, Permission.is_active.is_(True))
        ).all())
    return {"catalog": dict(PERMISSION_CATALOG), "roles": roles, "can_manage": member.is_owner}


@router.put("/{organization_id}/role-permissions")
def save_role_permissions(
    organization_id: uuid.UUID,
    payload: RolePermissionUpdate,
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(get_current_user),
):
    member = _active_member(db, user, organization_id)
    if not member.is_owner:
        raise HTTPException(status_code=403, detail="Owner access required to change role permissions")
    role_name = payload.role_name.strip().lower()
    if role_name not in {"manager", "staff"}:
        raise HTTPException(status_code=422, detail="Only manager and staff permission sets can be configured")
    selected = set(payload.permission_keys)
    if selected - set(PERMISSION_CATALOG):
        raise HTTPException(status_code=422, detail="Unknown permission key")

    role = db.scalar(select(Role).where(Role.organization_id == organization_id, Role.name == role_name))
    if role is None:
        role = Role(organization_id=organization_id, name=role_name, is_system=True, is_active=True)
        db.add(role)
        db.flush()

    db.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
    for key in sorted(selected):
        permission = create_permission(db, key, PERMISSION_CATALOG[key])
        assign_permission(db, role.id, permission.id)

    people = db.scalars(select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.role_name == role_name,
    )).all()
    for person in people:
        assign_configured_category_role(db, person)

    db.add(AuditLog(
        organization_id=organization_id,
        user_id=uuid.UUID(user.user_id),
        action="permissions.role_updated",
        entity_type="role",
        entity_id=role.id,
        description=f"Updated {role_name} permissions",
        metadata_json=f'{{"role_name":"{role_name}","permission_count":{len(selected)}}}',
    ))
    db.commit()
    return {"role_name": role_name, "permission_keys": sorted(selected)}
