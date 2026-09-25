import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.organizations.service import create_organization


engine = create_engine("sqlite:///:memory:")


@pytest.fixture
def db():
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


def test_create_organization_creates_owner(db):
    organization = create_organization(
        db=db,
        name="Elo Gadgets",
        slug="elo-gadgets",
        owner_email="owner@example.com",
        owner_password="OwnerPassword123!",
    )

    db.commit()

    assert organization.name == "Elo Gadgets"
    assert organization.slug == "elo-gadgets"
    assert organization.is_active is True

    assert len(organization.memberships) == 1

    membership = organization.memberships[0]

    assert membership.role_name == "owner"
    assert membership.is_owner is True
    assert membership.is_active is True


def test_duplicate_organization_slug_is_rejected(db):
    create_organization(
        db=db,
        name="Elo Gadgets",
        slug="elo-gadgets",
        owner_email="owner1@example.com",
        owner_password="OwnerPassword123!",
    )

    db.commit()

    with pytest.raises(ValueError, match="Organization slug already exists"):
        create_organization(
            db=db,
            name="Another Store",
            slug="elo-gadgets",
            owner_email="owner2@example.com",
            owner_password="OwnerPassword123!",
        )


def test_duplicate_owner_email_is_rejected(db):
    create_organization(
        db=db,
        name="Elo Gadgets",
        slug="elo-gadgets",
        owner_email="owner@example.com",
        owner_password="OwnerPassword123!",
    )

    db.commit()

    with pytest.raises(ValueError, match="User email already exists"):
        create_organization(
            db=db,
            name="Another Store",
            slug="another-store",
            owner_email="owner@example.com",
            owner_password="OwnerPassword123!",
        )


def test_owner_password_is_not_stored_plaintext(db):
    from app.models import User
    from app.auth.passwords import verify_password

    password = "OwnerPassword123!"

    create_organization(
        db=db,
        name="Secure Store",
        slug="secure-store",
        owner_email="secure@example.com",
        owner_password=password,
    )

    db.commit()

    user = db.query(User).filter_by(
        email="secure@example.com"
    ).first()

    assert user is not None
    assert user.password_hash != password
    assert verify_password(password, user.password_hash)
