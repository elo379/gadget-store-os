import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.audit.access import can_view_audit
from app.audit.schemas import AuditLogCreate
from app.audit.service import create_audit_log
from app.db.base import Base
from app.organizations.service import create_organization
from app.permissions.access import is_owner, user_has_permission


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
