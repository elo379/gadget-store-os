import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Membership, Organization, User
from app.organizations.authority import can_create_personnel
from app.organizations.invitation_model import PersonnelInvitation
from app.organizations.invitations import accept_invitation, create_invitation
from app.organizations.personnel import create_personnel
from app.organizations.personnel_lifecycle import (
    reactivate_personnel,
    revoke_personnel,
    suspend_personnel,
)
from app.organizations.store_tree import get_or_create_store_tree_policy


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def create_owner(db):
    organization = Organization(
        name="Tree Test Store",
        slug=f"tree-{uuid.uuid4().hex[:8]}",
        is_active=True,
    )

    user = User(
        email=f"owner-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="test-hash",
        is_active=True,
    )

    membership = Membership(
        organization=organization,
        user=user,
        role_name="owner",
        personnel_id="GSOS-OWN-001",
        account_status="active",
        is_owner=True,
        is_active=True,
    )

    db.add(organization)
    db.add(user)
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return organization, membership


def test_owner_is_root_and_can_create_manager(db):
    organization, owner = create_owner(db)

    assert owner.personnel_id == "GSOS-OWN-001"
    assert owner.is_owner is True

    assert can_create_personnel(
        db,
        owner,
        organization.id,
        "manager",
    )

    manager = create_personnel(
        db,
        organization.id,
        owner,
        f"manager-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    db.commit()

    assert manager.personnel_id == "GSOS-MGR-001"
    assert manager.parent_membership_id == owner.id
    assert manager.created_by_membership_id == owner.id


def test_manager_creation_is_blocked_by_default(db):
    organization, owner = create_owner(db)

    manager = create_personnel(
        db,
        organization.id,
        owner,
        f"manager-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    db.commit()

    assert can_create_personnel(
        db,
        manager,
        organization.id,
        "staff",
    ) is False

    assert can_create_personnel(
        db,
        manager,
        organization.id,
        "manager",
    ) is False


def test_owner_can_enable_manager_staff_creation(db):
    organization, owner = create_owner(db)

    manager = create_personnel(
        db,
        organization.id,
        owner,
        f"manager-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    db.commit()

    policy = get_or_create_store_tree_policy(
        db,
        organization.id,
    )

    policy.managers_can_create_staff = True
    db.commit()

    assert can_create_personnel(
        db,
        manager,
        organization.id,
        "staff",
    ) is True


def test_invitation_token_is_hashed_and_acceptance_creates_staff(db):
    organization, owner = create_owner(db)

    token = None

    invitation, token = create_invitation(
        db,
        organization.id,
        owner,
        f"staff-{uuid.uuid4().hex[:8]}@example.com",
        "staff",
    )

    db.commit()

    assert token
    assert invitation.token_hash != token
    assert len(invitation.token_hash) == 64
    assert invitation.status == "pending"

    staff = accept_invitation(
        db,
        token,
        "Password123!",
    )

    db.commit()

    assert staff.personnel_id == "GSOS-STF-001"
    assert staff.account_status == "active"
    assert staff.is_active is True
    assert staff.parent_membership_id == owner.id
    assert staff.created_by_membership_id == owner.id
    assert invitation.status == "accepted"
    assert invitation.accepted_at is not None


def test_suspension_reactivation_and_revoke(db):
    organization, owner = create_owner(db)

    manager = create_personnel(
        db,
        organization.id,
        owner,
        f"manager-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    db.commit()

    suspend_personnel(
        db,
        owner,
        manager,
    )
    db.commit()

    assert manager.account_status == "suspended"
    assert manager.is_active is False

    reactivate_personnel(
        db,
        owner,
        manager,
    )
    db.commit()

    assert manager.account_status == "active"
    assert manager.is_active is True

    revoke_personnel(
        db,
        owner,
        manager,
    )
    db.commit()

    assert manager.account_status == "revoked"
    assert manager.is_active is False


def test_manager_cannot_manage_personnel_outside_its_tree(db):
    organization, owner = create_owner(db)

    manager_one = create_personnel(
        db,
        organization.id,
        owner,
        f"manager1-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    manager_two = create_personnel(
        db,
        organization.id,
        owner,
        f"manager2-{uuid.uuid4().hex[:8]}@example.com",
        "Password123!",
        "manager",
    )

    db.commit()

    with pytest.raises(ValueError):
        suspend_personnel(
            db,
            manager_one,
            manager_two,
        )

    assert manager_two.account_status == "active"
