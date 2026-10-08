import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.passwords import hash_password
from app.models import Membership, User


INVITATION_EXPIRY_HOURS = 72


def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_invitation(
    db: Session,
    organization_id: uuid.UUID,
    creator_membership: Membership,
    email: str,
    role_name: str,
) -> tuple["PersonnelInvitation", str]:
    from app.organizations.invitation_model import PersonnelInvitation
    from app.organizations.authority import require_personnel_creation_authority

    role = role_name.lower()

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

    pending = db.scalar(
        select(PersonnelInvitation).where(
            PersonnelInvitation.organization_id == organization_id,
            PersonnelInvitation.email == email,
            PersonnelInvitation.status == "pending",
        )
    )

    if pending is not None:
        raise ValueError("A pending invitation already exists")

    token = secrets.token_urlsafe(32)

    invitation = PersonnelInvitation(
        organization_id=organization_id,
        email=email,
        role_name=role,
        token_hash=hash_invitation_token(token),
        parent_membership_id=creator_membership.id,
        created_by_membership_id=creator_membership.id,
        status="pending",
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=INVITATION_EXPIRY_HOURS),
    )

    db.add(invitation)
    db.flush()
    db.add(AuditLog(
        organization_id=organization_id,
        user_id=creator_membership.user_id,
        action="personnel.invitation_created",
        entity_type="personnel_invitation",
        entity_id=invitation.id,
        description="Personnel activation invitation created",
        metadata_json=json.dumps({"role_name": role, "status": "pending"}),
    ))

    return invitation, token


def accept_invitation(
    db: Session,
    token: str,
    password: str,
    activation_id: uuid.UUID | None = None,
) -> Membership:
    from app.organizations.invitation_model import PersonnelInvitation

    token_hash = hash_invitation_token(token)

    invitation = db.scalar(
        select(PersonnelInvitation).where(
            PersonnelInvitation.token_hash == token_hash,
            *([PersonnelInvitation.id == activation_id] if activation_id else []),
        )
    )

    if invitation is None:
        raise ValueError("Invitation is invalid")

    if invitation.status != "pending":
        raise ValueError("Invitation is no longer active")

    now = datetime.now(timezone.utc)

    expires_at = invitation.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        invitation.status = "expired"
        db.add(AuditLog(
            organization_id=invitation.organization_id,
            user_id=None,
            action="personnel.invitation_expired",
            entity_type="personnel_invitation",
            entity_id=invitation.id,
            description="Personnel activation invitation expired",
            metadata_json=json.dumps({"status": "expired"}),
        ))
        db.flush()
        raise ValueError("Invitation has expired")

    existing_user = db.scalar(
        select(User).where(User.email == invitation.email)
    )

    if existing_user is not None:
        raise ValueError("User email already exists")

    user = User(
        email=invitation.email,
        password_hash=hash_password(password),
        is_active=True,
    )

    personnel_id = _next_personnel_id(
        db,
        invitation.organization_id,
        invitation.role_name,
    )

    membership = Membership(
        organization_id=invitation.organization_id,
        user=user,
        role_name=invitation.role_name,
        personnel_id=personnel_id,
        parent_membership_id=invitation.parent_membership_id,
        created_by_membership_id=invitation.created_by_membership_id,
        account_status="active",
        accepted_at=now,
        is_owner=False,
        is_active=True,
    )

    invitation.status = "accepted"
    invitation.accepted_at = now

    db.add(user)
    db.add(membership)
    db.flush()
    from app.permissions.role_assignments import assign_configured_category_role
    assign_configured_category_role(db, membership)
    if invitation.role_name.lower() == "staff":
        from app.staff.models import StaffProfile
        db.add(StaffProfile(
            organization_id=invitation.organization_id,
            user_id=user.id,
            staff_code=personnel_id,
        ))
    db.add(AuditLog(
        organization_id=invitation.organization_id,
        user_id=user.id,
        action="personnel.activated",
        entity_type="membership",
        entity_id=membership.id,
        description="Personnel account activated",
        metadata_json=json.dumps({
            "role_name": invitation.role_name,
            "activation_id": str(invitation.id),
        }),
    ))

    return membership


def _next_personnel_id(
    db: Session,
    organization_id: uuid.UUID,
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
