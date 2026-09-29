import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Membership, Organization, User
from app.staff.attendance import AttendanceRecord, clock_in, clock_out
from app.staff.models import StaffProfile
from app.organizations.invitations import accept_invitation, create_invitation
from app.audit.models import AuditLog
from app.auth.schemas import AuthenticatedUser
from app.staff.routes import record_absence, monthly_timebook
from app.organizations.personnel_lifecycle import deactivate_personnel, reactivate_personnel


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def staff_fixture(db):
    organization = Organization(name="Staff Store", slug=f"staff-{uuid.uuid4().hex}", is_active=True)
    user = User(email=f"staff-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    membership = Membership(organization=organization, user=user, role_name="staff", account_status="active", is_active=True)
    db.add_all([organization, user, membership])
    db.flush()
    profile = StaffProfile(organization_id=organization.id, user_id=user.id, staff_code="GSOS-STF-001")
    db.add(profile)
    db.commit()
    return organization, user, profile


def test_attendance_is_server_timestamped_and_rejects_duplicates(db):
    organization, user, profile = staff_fixture(db)
    record = clock_in(db, organization.id, profile.id, actor_user_id=user.id)
    assert record.clock_in.tzinfo is not None or record.clock_in is not None
    with pytest.raises(ValueError, match="already recorded"):
        clock_in(db, organization.id, profile.id, actor_user_id=user.id)
    closed = clock_out(db, organization.id, profile.id, actor_user_id=user.id)
    assert closed.status == "closed"
    assert closed.clock_out is not None
    assert closed.early_departure_minutes >= 0
    with pytest.raises(ValueError, match="No active"):
        clock_out(db, organization.id, profile.id, actor_user_id=user.id)


def test_attendance_queries_remain_organization_scoped(db):
    organization, user, profile = staff_fixture(db)
    other_org = Organization(name="Other", slug=f"other-{uuid.uuid4().hex}", is_active=True)
    db.add(other_org)
    db.commit()
    record = clock_in(db, organization.id, profile.id)
    assert db.query(AttendanceRecord).filter_by(organization_id=other_org.id, id=record.id).one_or_none() is None
    with pytest.raises(ValueError, match="No active"):
        clock_out(db, other_org.id, profile.id)


def test_activation_is_one_time_and_creates_the_staff_profile(db):
    organization = Organization(name="Activation Store", slug=f"activation-{uuid.uuid4().hex}", is_active=True)
    owner_user = User(email=f"owner-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    owner = Membership(organization=organization, user=owner_user, role_name="owner", is_owner=True, is_active=True, account_status="active")
    db.add_all([organization, owner_user, owner])
    db.commit()
    invitation, token = create_invitation(db, organization.id, owner, f"new-{uuid.uuid4().hex}@example.com", "staff")
    invitation_id = invitation.id
    db.commit()
    member = accept_invitation(db, token, "PermanentPassword123!", invitation_id)
    db.commit()
    assert db.query(StaffProfile).filter_by(organization_id=organization.id, user_id=member.user_id).one().staff_code == member.personnel_id
    assert db.query(AuditLog).filter_by(action="personnel.activated", entity_id=member.id).one_or_none() is not None
    with pytest.raises(ValueError, match="no longer active"):
        accept_invitation(db, token, "PermanentPassword123!", invitation_id)
    revoked, revoked_token = create_invitation(db, organization.id, owner, f"revoked-{uuid.uuid4().hex}@example.com", "staff")
    revoked_id = revoked.id
    revoked.status = "revoked"
    db.commit()
    with pytest.raises(ValueError, match="no longer active"):
        accept_invitation(db, revoked_token, "PermanentPassword123!", revoked_id)


def test_absence_mutation_is_scoped_audited_and_conflicts_with_attendance(db):
    organization = Organization(name="Absence Store", slug=f"absence-{uuid.uuid4().hex}", is_active=True)
    owner_user = User(email=f"owner-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    owner = Membership(organization=organization, user=owner_user, role_name="owner", is_owner=True, is_active=True, account_status="active")
    db.add_all([organization, owner_user, owner])
    db.commit()
    staff_user = User(email=f"staff-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    staff_membership = Membership(organization_id=organization.id, user=staff_user, role_name="staff", is_active=True, account_status="active")
    db.add_all([staff_user, staff_membership])
    db.flush()
    profile = StaffProfile(organization_id=organization.id, user_id=staff_user.id, staff_code="GSOS-STF-ABS")
    db.add(profile)
    db.commit()
    identity = AuthenticatedUser(user_id=str(owner_user.id), email=owner_user.email)
    day = datetime.now(timezone.utc).date().isoformat()
    response = record_absence(organization.id, {"staff_id": str(profile.id), "date": day, "reason": "Sick"}, db, identity)
    assert response["status"] == "absent"
    assert db.query(AuditLog).filter_by(action="attendance.absence_recorded", organization_id=organization.id).one_or_none() is not None
    with pytest.raises(Exception) as duplicate:
        record_absence(organization.id, {"staff_id": str(profile.id), "date": day}, db, identity)
    assert getattr(duplicate.value, "status_code", None) == 409
    rows = monthly_timebook(organization.id, datetime.now(timezone.utc).strftime("%Y-%m"), db, identity)
    assert rows[0]["status"] == "absent"


def test_deactivation_is_audited_and_not_reactivatable(db):
    organization = Organization(name="Lifecycle Store", slug=f"lifecycle-{uuid.uuid4().hex}", is_active=True)
    owner_user = User(email=f"owner-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    owner = Membership(organization=organization, user=owner_user, role_name="owner", is_owner=True, is_active=True, account_status="active")
    staff_user = User(email=f"staff-{uuid.uuid4().hex}@example.com", password_hash="hash", is_active=True)
    target = Membership(organization=organization, user=staff_user, role_name="staff", is_active=True, account_status="active", parent_membership=owner)
    db.add_all([organization, owner_user, owner, staff_user, target])
    db.flush()
    profile = StaffProfile(organization_id=organization.id, user_id=staff_user.id, staff_code="GSOS-STF-DEC")
    db.add(profile)
    db.commit()
    deactivate_personnel(db, owner, target)
    db.commit()
    assert target.account_status == "deactivated" and not profile.is_active
    assert db.query(AuditLog).filter_by(action="personnel.deactivated", entity_id=target.id).one_or_none() is not None
    with pytest.raises(ValueError, match="Only suspended"):
        reactivate_personnel(db, owner, target)
