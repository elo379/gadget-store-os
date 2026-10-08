import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.activation.models import ActivationAttempt, ActivationCode
from app.audit.models import AuditLog
from app.auth.passwords import hash_password
from app.db.mixins import utc_now
from app.models import Membership, Organization, User

CODE_LENGTH = 24
CODE_ALPHABET = string.ascii_uppercase + string.digits
MAX_ATTEMPTS = 10
ATTEMPT_WINDOW = timedelta(minutes=15)


def normalize_code(code: str) -> str:
    normalized = code.strip().upper()
    if len(normalized) != CODE_LENGTH or any(char not in CODE_ALPHABET for char in normalized):
        raise ValueError("Invalid activation code")
    return normalized


def digest_code(code: str) -> str:
    return hashlib.sha256(normalize_code(code).encode("ascii")).hexdigest()


def generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def register_failed_attempt(db: Session, remote_address: str) -> bool:
    """Persist a per-address rolling attempt window; return True when blocked."""
    address_digest = hashlib.sha256((remote_address or "unknown").encode("utf-8")).hexdigest()
    now = utc_now()
    cutoff = now - ATTEMPT_WINDOW
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(ActivationAttempt).values(
        address_digest=address_digest, attempts=1, window_started_at=now
    )
    reset = ActivationAttempt.window_started_at < cutoff
    statement = statement.on_conflict_do_update(
        index_elements=[ActivationAttempt.address_digest],
        set_={
            "attempts": case((reset, 1), else_=ActivationAttempt.attempts + 1),
            "window_started_at": case((reset, now), else_=ActivationAttempt.window_started_at),
        },
    ).returning(ActivationAttempt.attempts)
    attempt_count = db.scalar(statement)
    db.execute(delete(ActivationAttempt).where(ActivationAttempt.window_started_at < now - timedelta(days=1)))
    return int(attempt_count or 0) > MAX_ATTEMPTS


def is_rate_limited(db: Session, remote_address: str) -> bool:
    address_digest = hashlib.sha256((remote_address or "unknown").encode("utf-8")).hexdigest()
    attempt = db.scalar(select(ActivationAttempt).where(ActivationAttempt.address_digest == address_digest))
    if attempt is None:
        return False
    if attempt.window_started_at.tzinfo is None:
        window_started_at = attempt.window_started_at.replace(tzinfo=timezone.utc)
    else:
        window_started_at = attempt.window_started_at
    return window_started_at >= utc_now() - ATTEMPT_WINDOW and attempt.attempts > MAX_ATTEMPTS


def create_organization_with_code(
    db: Session,
    *,
    name: str,
    slug: str,
    owner_email: str,
    owner_password: str,
    activation_code: str,
) -> Organization:
    now = datetime.now(timezone.utc)
    normalized = normalize_code(activation_code)
    code = db.query(ActivationCode).filter(ActivationCode.code_digest == digest_code(normalized)).one_or_none()
    if code is None or code.status != "issued":
        raise ValueError("Invalid or unavailable activation code")
    expiry = code.expires_at
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry is not None and expiry <= now:
        code.status = "expired"
        db.flush()
        raise ValueError("Activation code expired")

    if db.query(Organization).filter(Organization.slug == slug).first() is not None:
        raise ValueError("Organization slug already exists")
    if db.query(User).filter(User.email == owner_email).first() is not None:
        raise ValueError("User email already exists")

    # Keep tenant creation, the one-time conditional redemption, and its audit
    # in one savepoint. The request layer may commit a throttling attempt after
    # a failed redemption, so rollback must not depend on the outer request
    # transaction being discarded.
    with db.begin_nested():
        organization = Organization(name=name, slug=slug, is_active=True)
        owner = User(email=owner_email, password_hash=hash_password(owner_password), is_active=True)
        membership = Membership(
            organization=organization,
            user=owner,
            role_name="owner",
            personnel_id="GSOS-OWN-001",
            account_status="active",
            is_owner=True,
            is_active=True,
        )
        db.add_all([organization, owner, membership])
        db.flush()

        # A conditional update is the single-winner gate across concurrent requests.
        redeemed = db.execute(
            update(ActivationCode)
            .where(
                ActivationCode.id == code.id,
                ActivationCode.status == "issued",
                (ActivationCode.expires_at.is_(None) | (ActivationCode.expires_at > now)),
            )
            .values(status="redeemed", redeemed_at=now, organization_id=organization.id)
        )
        if redeemed.rowcount != 1:
            raise ValueError("Invalid or unavailable activation code")

        db.add(AuditLog(
            organization_id=organization.id,
            user_id=owner.id,
            action="organization.created",
            entity_type="organization",
            entity_id=organization.id,
            description="Organization activated",
            metadata_json='{"activation":"redeemed","owner_role":"owner"}',
        ))
    return organization
