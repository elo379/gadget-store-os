from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.models import Membership, Organization, User


def create_organization(
    db: Session,
    name: str,
    slug: str,
    owner_email: str,
    owner_password: str,
) -> Organization:
    existing_organization = db.scalar(
        select(Organization).where(Organization.slug == slug)
    )
    if existing_organization is not None:
        raise ValueError("Organization slug already exists")

    existing_user = db.scalar(
        select(User).where(User.email == owner_email)
    )
    if existing_user is not None:
        raise ValueError("User email already exists")

    organization = Organization(
        name=name,
        slug=slug,
        is_active=True,
    )

    owner = User(
        email=owner_email,
        password_hash=hash_password(owner_password),
        is_active=True,
    )

    membership = Membership(
        organization=organization,
        user=owner,
        role_name="owner",
        personnel_id="GSOS-OWN-001",
        account_status="active",
        is_owner=True,
        is_active=True,
    )

    db.add(organization)
    db.add(owner)
    db.add(membership)
    db.flush()

    return organization


def get_organization(
    db: Session,
    organization_id: UUID,
) -> Organization | None:
    return db.scalar(
        select(Organization).where(
            Organization.id == organization_id
        )
    )


def get_membership(
    db: Session,
    organization_id: UUID,
    user_id: UUID,
) -> Membership | None:
    return db.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user_id,
        )
    )
