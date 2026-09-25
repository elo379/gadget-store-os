import uuid

from app.auth.passwords import verify_password
from app.models import Membership, Organization, User
from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
)
from app.organizations.service import create_organization


def test_organization_schema():
    data = OrganizationCreate(
        name="Elo Gadgets",
        slug="elo-gadgets",
    )

    assert data.name == "Elo Gadgets"
    assert data.slug == "elo-gadgets"


def test_organization_response_schema():
    organization = Organization(
        id=uuid.uuid4(),
        name="Elo Gadgets",
        slug="elo-gadgets",
        is_active=True,
    )

    response = OrganizationResponse.model_validate(organization)

    assert response.name == "Elo Gadgets"
    assert response.is_active is True


def test_organization_models_have_expected_tables():
    assert Organization.__tablename__ == "organizations"
    assert User.__tablename__ == "users"
    assert Membership.__tablename__ == "memberships"


def test_membership_owner_defaults():
    membership = Membership(
        organization_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        role_name="owner",
        is_owner=True,
        is_active=True,
    )

    assert membership.role_name == "owner"
    assert membership.is_owner is True
    assert membership.is_active is True


def test_owner_password_is_hashed():
    password = "OwnerPassword123!"

    from app.auth.passwords import hash_password

    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
