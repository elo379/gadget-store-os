from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import verify_password
from app.auth.sessions import (
    create_refresh_token,
    hash_refresh_token,
    session_expires_at,
)
from app.auth.tokens import create_access_token
from app.models.session import Session as AuthSession
from app.models.user import User


def authenticate_user(
    user_id: str,
    password: str,
    password_hash: str,
) -> str | None:
    if not verify_password(password, password_hash):
        return None

    return create_access_token(user_id)


def create_login_session(
    db: Session,
    user: User,
) -> tuple[str, str]:
    refresh_token = create_refresh_token()

    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=session_expires_at(),
    )

    db.add(session)
    db.commit()

    return create_access_token(str(user.id)), refresh_token


def refresh_login_session(
    db: Session,
    refresh_token: str,
) -> str | None:
    token_hash = hash_refresh_token(refresh_token)

    session = db.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == token_hash,
            AuthSession.revoked.is_(False),
        )
    )

    if session is None:
        return None

    now = datetime.now(timezone.utc)

    if session.expires_at <= now:
        session.revoked = True
        db.commit()
        return None

    return create_access_token(str(session.user_id))


def revoke_login_session(
    db: Session,
    refresh_token: str,
) -> bool:
    token_hash = hash_refresh_token(refresh_token)

    session = db.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == token_hash,
            AuthSession.revoked.is_(False),
        )
    )

    if session is None:
        return False

    session.revoked = True
    db.commit()

    return True
