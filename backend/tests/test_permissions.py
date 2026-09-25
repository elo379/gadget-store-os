import uuid

from app.db.base import Base
from app.permissions import (
    MembershipRole,
    Permission,
    Role,
    RolePermission,
)


def test_rbac_tables_registered():
    tables = set(Base.metadata.tables.keys())

    assert "permissions" in tables
    assert "roles" in tables
    assert "role_permissions" in tables
    assert "membership_roles" in tables


def test_rbac_models_have_expected_names():
    assert Permission.__tablename__ == "permissions"
    assert Role.__tablename__ == "roles"
    assert RolePermission.__tablename__ == "role_permissions"
    assert MembershipRole.__tablename__ == "membership_roles"


def test_membership_role_requires_membership_and_role():
    assignment = MembershipRole(
        membership_id=uuid.uuid4(),
        role_id=uuid.uuid4(),
    )

    assert assignment.membership_id is not None
    assert assignment.role_id is not None
