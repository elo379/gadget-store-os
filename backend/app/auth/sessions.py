import hashlib
import secrets
from datetime import datetime, timedelta, timezone

SESSION_EXPIRE_DAYS = 30


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=SESSION_EXPIRE_DAYS
    )
