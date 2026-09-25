from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import ALGORITHM, create_access_token, decode_access_token
from app.core.config import settings
from app.main import app


client = TestClient(app)

TEST_SECRET = "test-secret-key-for-authentication-32"


def test_password_hash_and_verify():
    password = "StrongPassword123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword123!", password_hash)


def test_create_and_decode_access_token(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)

    token = create_access_token("user-123")
    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"


def test_invalid_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.token.value")


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)

    now = datetime.now(timezone.utc)

    expired_payload = {
        "sub": "user-123",
        "exp": now - timedelta(seconds=1),
        "iat": now - timedelta(minutes=1),
    }

    token = jwt.encode(
        expired_payload,
        TEST_SECRET,
        algorithm=ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_auth_me_with_valid_token(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)

    token = create_access_token("user-123")

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "user-123"


def test_auth_me_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)

    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401


def test_auth_me_requires_authentication():
    response = client.get("/auth/me")

    assert response.status_code == 401
