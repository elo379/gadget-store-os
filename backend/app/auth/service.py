from app.auth.passwords import verify_password
from app.auth.tokens import create_access_token


def authenticate_user(
    user_id: str,
    password: str,
    password_hash: str,
) -> str | None:
    if not verify_password(password, password_hash):
        return None

    return create_access_token(user_id)
