import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.audit.access import can_view_audit
from app.audit.schemas import AuditLogCreate
from app.audit.service import create_audit_log
from app.db.base import Base
from app.organizations.service import create_organization
from app.permissions.access import is_owner, user_has_permission
from app.permissions.access import require_organization_permission
from app.permissions.models import Permission, Role, RolePermission
from app.permissions.membership_roles import MembershipRole
from app.models import Membership, User


engine = create_engine("sqlite:///:memory:")


@pytest.fixture
def db():
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_organization_isolation(db):
    first = create_organization(
        db=db,
        name="First Store",
        slug=f"first-{uuid.uuid4().hex[:8]}",
        owner_email=f"first-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    second = create_organization(
        db=db,
        name="Second Store",
        slug=f"second-{uuid.uuid4().hex[:8]}",
        owner_email=f"second-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    first_owner = first.memberships[0].user
    second_owner = second.memberships[0].user

    assert is_owner(
        db,
        first_owner.id,
        first.id,
    )

    assert not is_owner(
        db,
        first_owner.id,
        second.id,
    )

    assert not user_has_permission(
        db,
        first_owner.id,
        second.id,
        "audit.view",
    )

    assert not can_view_audit(
        db,
        first_owner.id,
        second.id,
    )

    assert is_owner(
        db,
        second_owner.id,
        second.id,
    )


def test_audit_logs_are_organization_scoped(db):
    first = create_organization(
        db=db,
        name="Audit First",
        slug=f"audit-first-{uuid.uuid4().hex[:8]}",
        owner_email=f"first-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    second = create_organization(
        db=db,
        name="Audit Second",
        slug=f"audit-second-{uuid.uuid4().hex[:8]}",
        owner_email=f"second-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    create_audit_log(
        db,
        AuditLogCreate(
            organization_id=first.id,
            user_id=first.memberships[0].user.id,
            action="test.first",
            entity_type="test",
        ),
    )

    create_audit_log(
        db,
        AuditLogCreate(
            organization_id=second.id,
            user_id=second.memberships[0].user.id,
            action="test.second",
            entity_type="test",
        ),
    )

    from app.audit.service import list_audit_logs

    first_logs = list_audit_logs(db, first.id)
    second_logs = list_audit_logs(db, second.id)

    assert len(first_logs) == 1
    assert first_logs[0].action == "test.first"

    assert len(second_logs) == 1
    assert second_logs[0].action == "test.second"


def test_audit_access_requires_membership(db):
    organization = create_organization(
        db=db,
        name="Protected Store",
        slug=f"protected-{uuid.uuid4().hex[:8]}",
        owner_email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    outsider = uuid.uuid4()

    assert not can_view_audit(
        db,
        outsider,
        organization.id,
    )


def test_tenant_permission_rejects_cross_organization_access(db):
    first = create_organization(
        db, "Tenant One", f"tenant-one-{uuid.uuid4().hex}",
        f"owner-one-{uuid.uuid4().hex}@example.com", "StrongPassword123!",
    )
    second = create_organization(
        db, "Tenant Two", f"tenant-two-{uuid.uuid4().hex}",
        f"owner-two-{uuid.uuid4().hex}@example.com", "StrongPassword123!",
    )
    with pytest.raises(HTTPException) as denied:
        require_organization_permission(
            db, first.memberships[0].user_id, second.id, "products.view"
        )
    assert denied.value.status_code == 404


def test_owner_manager_and_staff_follow_assigned_permissions(db):
    organization = create_organization(
        db, "RBAC Store", f"rbac-{uuid.uuid4().hex}",
        f"rbac-owner-{uuid.uuid4().hex}@example.com", "StrongPassword123!",
    )
    owner = organization.memberships[0]
    manager_user = User(email=f"mgr-{uuid.uuid4().hex}@example.com", password_hash="hash")
    staff_user = User(email=f"stf-{uuid.uuid4().hex}@example.com", password_hash="hash")
    manager = Membership(organization_id=organization.id, user=manager_user, role_name="manager", parent_membership_id=owner.id, account_status="active", is_active=True)
    db.add(manager)
    db.flush()
    staff = Membership(organization_id=organization.id, user=staff_user, role_name="staff", parent_membership_id=manager.id, account_status="active", is_active=True)
    view = Permission(key="products.view", description="view", is_active=True)
    manage = Permission(key="products.manage", description="manage", is_active=True)
    manager_role = Role(organization_id=organization.id, name="Manager test", is_active=True)
    staff_role = Role(organization_id=organization.id, name="Staff test", is_active=True)
    db.add_all([staff, view, manage, manager_role, staff_role])
    db.flush()
    db.add_all([
        RolePermission(role_id=manager_role.id, permission_id=view.id),
        RolePermission(role_id=staff_role.id, permission_id=view.id),
        MembershipRole(membership_id=manager.id, role_id=manager_role.id),
        MembershipRole(membership_id=staff.id, role_id=staff_role.id),
    ])
    db.commit()

    assert require_organization_permission(db, owner.user_id, organization.id, "products.manage") is owner
    assert require_organization_permission(db, manager.user_id, organization.id, "products.view") is manager
    assert require_organization_permission(db, staff.user_id, organization.id, "products.view") is staff
    for user_id in (manager.user_id, staff.user_id):
        with pytest.raises(HTTPException) as denied:
            require_organization_permission(db, user_id, organization.id, "products.manage")
        assert denied.value.status_code == 403
