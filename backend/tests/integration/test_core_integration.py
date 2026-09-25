import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogCreate
from app.audit.service import create_audit_log, list_audit_logs
from app.db.base import Base
from app.organizations.service import create_organization


engine = create_engine("sqlite:///:memory:")


@pytest.fixture
def db():
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_audit_metadata_validation(db):
    organization = create_organization(
        db=db,
        name="Integration Store",
        slug=f"integration-{uuid.uuid4().hex[:8]}",
        owner_email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    payload = AuditLogCreate(
        organization_id=organization.id,
        action="integration.test",
        entity_type="test",
        description="Integration test",
        metadata_json='{"source": "integration"}',
    )

    log = create_audit_log(db, payload)

    assert log.organization_id == organization.id
    assert log.action == "integration.test"
    assert log.metadata_json == '{"source": "integration"}'

    logs = list_audit_logs(
        db,
        organization.id,
    )

    assert len(logs) >= 1


def test_invalid_audit_metadata_rejected(db):
    organization = create_organization(
        db=db,
        name="Invalid Audit Store",
        slug=f"invalid-audit-{uuid.uuid4().hex[:8]}",
        owner_email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        owner_password="StrongPassword123!",
    )

    payload = AuditLogCreate(
        organization_id=organization.id,
        action="integration.test",
        entity_type="test",
        metadata_json="{invalid-json",
    )

    with pytest.raises(
        ValueError,
        match="Invalid audit metadata JSON",
    ):
        create_audit_log(db, payload)
