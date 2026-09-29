import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
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
from app.models.membership import Membership
from app.models.organization import Organization
from app.api.auth.routes import login as login_route
from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest

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
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    if previous is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous



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


def test_protected_product_routes_require_authentication():
    response = client.get(f"/products?organization_id={uuid.uuid4()}")
    assert response.status_code in {401, 403}


def test_product_routes_reject_another_organizations_membership(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)
    owner_id, _ = make_user()
    db = TestingSessionLocal()
    other_organization = Organization(
        name="Other Store", slug=f"other-{uuid.uuid4().hex}", is_active=True
    )
    db.add(other_organization)
    db.flush()
    db.add(Membership(
        organization_id=other_organization.id, user_id=owner_id, role_name="owner",
        account_status="active", is_active=True, is_owner=True,
    ))
    organization = Organization(
        name="Isolated Store", slug=f"isolated-{uuid.uuid4().hex}", is_active=True
    )
    db.add(organization)
    db.commit()
    organization_id = organization.id
    db.close()
    token = create_access_token(str(owner_id))
    response = client.get(
        f"/products?organization_id={organization_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_sale_route_uses_authenticated_seller_not_payload(monkeypatch):
    from app.auth.schemas import AuthenticatedUser
    from app.sales import routes as sales_routes
    from app.sales.schemas import SaleCreate, SaleLineCreate

    user_id, email = make_user()
    db = TestingSessionLocal()
    organization = Organization(
        name="POS Store", slug=f"pos-{uuid.uuid4().hex}", is_active=True
    )
    db.add(organization)
    db.flush()
    db.add(Membership(
        organization_id=organization.id, user_id=user_id, role_name="owner",
        account_status="active", is_active=True, is_owner=True,
    ))
    db.commit()
    payload = SaleCreate(
        organization_id=organization.id,
        sold_by_user_id=uuid.uuid4(),
        reference_number=f"forged-{uuid.uuid4().hex}",
        lines=[SaleLineCreate(product_id=uuid.uuid4(), quantity=1, unit_price=1)],
    )
    monkeypatch.setattr(sales_routes, "create_sale", lambda _db, value: value)
    result = sales_routes.create_sale_route(
        payload, db, AuthenticatedUser(user_id=str(user_id), email=email)
    )
    assert result.sold_by_user_id == user_id
    db.close()


def test_suspended_personnel_cannot_log_in_or_use_existing_token(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", TEST_SECRET)
    db = TestingSessionLocal()
    user = User(
        email=f"suspended-{uuid.uuid4()}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        is_active=True,
    )
    organization = Organization(
        name="Suspended Test",
        slug=f"suspended-{uuid.uuid4().hex}",
        is_active=True,
    )
    membership = Membership(
        organization=organization,
        user=user,
        role_name="staff",
        account_status="suspended",
        is_active=False,
    )
    db.add_all([user, organization, membership])
    db.commit()
    user_id, email = user.id, user.email
    db.close()

    token = create_access_token(str(user_id))
    db = TestingSessionLocal()
    with pytest.raises(HTTPException) as login_error:
        login_route(
            LoginRequest(email=email, password="StrongPassword123!"),
            db,
        )
    assert login_error.value.status_code == 401
    with pytest.raises(HTTPException) as auth_error:
        get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db,
        )
    assert auth_error.value.status_code == 401
    db.close()
