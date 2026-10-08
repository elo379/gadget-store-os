from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.models import Membership, User
from app.organizations.authority import require_personnel_creation_authority
from app.permissions.role_assignments import assign_configured_category_role


def get_next_personnel_id(
    db: Session,
    organization_id: UUID,
    role_name: str,
) -> str:
    prefixes = {
        "manager": "GSOS-MGR",
        "staff": "GSOS-STF",
    }

    prefix = prefixes.get(role_name.lower())

    if prefix is None:
        raise ValueError("Unsupported personnel role")

    members = db.scalars(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.personnel_id.like(f"{prefix}-%"),
        )
    ).all()

    highest = 0

    for member in members:
        try:
            number = int(member.personnel_id.rsplit("-", 1)[1])
            highest = max(highest, number)
        except (AttributeError, ValueError):
            continue

    return f"{prefix}-{highest + 1:03d}"


def create_personnel(
    db: Session,
    organization_id: UUID,
    creator_membership: Membership,
    email: str,
    password: str,
    role_name: str,
) -> Membership:
    role = role_name.lower()

    if role not in {"manager", "staff"}:
        raise ValueError("Only manager or staff accounts can be created")

    if creator_membership.organization_id != organization_id:
        raise ValueError("Creator does not belong to organization")

    if not creator_membership.is_active:
        raise ValueError("Creator membership is inactive")

    require_personnel_creation_authority(
        db,
        creator_membership,
        organization_id,
        role,
    )

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise ValueError("User email already exists")

    user = User(
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )

    personnel_id = get_next_personnel_id(
        db,
        organization_id,
        role,
    )

    membership = Membership(
        organization_id=organization_id,
        user=user,
        role_name=role,
        personnel_id=personnel_id,
        parent_membership_id=creator_membership.id,
        created_by_membership_id=creator_membership.id,
        account_status="active",
        is_owner=False,
        is_active=True,
    )

    db.add(user)
    db.add(membership)
    db.flush()
    assign_configured_category_role(db, membership)

    return membership
