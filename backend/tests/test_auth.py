import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import ALGORITHM, create_access_token, decode_access_token
from app.core.config import settings
from app.db.base import Base
from app.db.dependencies import get_db
from app.main import app
from app.models.user import User

TEST_SECRET = "test-secret-key-for-authentication-32"

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def restore_auth_db_override():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)



def make_user():
    db = TestingSessionLocal()
    user = User(
        email=f"{uuid.uuid4()}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    email = user.email
    db.close()
    return user_id, email


def test_password_hash_and_verify():
    password = "StrongPassword123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword!", password_hash)


def test_create_access_token():
    settings.SECRET_KEY = TEST_SECRET
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
        "exp": now - timedelta(minutes=1),
        "iat": now - timedelta(minutes=2),
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

    user_id, email = make_user()
    token = create_access_token(str(user_id))

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    assert response.json()["user_id"] == str(user_id)
    assert response.json()["email"] == email


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
