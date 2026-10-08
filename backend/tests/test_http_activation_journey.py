from collections.abc import Generator
from threading import enumerate as enumerate_threads

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.activation.models import ActivationAttempt, ActivationCode
from app.activation.service import digest_code, generate_code
from app.db.base import Base
from app.db.dependencies import get_db
from app.db.mixins import utc_now
from app.main import app
from app.models import Membership, Organization


@pytest.fixture
def http_database() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def disposable_db():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = disposable_db
    try:
        yield factory
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        Base.metadata.drop_all(engine)
        engine.dispose()


def _issue(factory: sessionmaker[Session], code: str) -> None:
    with factory.begin() as db:
        db.add(ActivationCode(
            code_digest=digest_code(code),
            status="issued",
            created_at=utc_now(),
        ))


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_http_health_database_dependency_and_client_lifecycle(http_database):
    portal_threads_before = {
        thread.ident for thread in enumerate_threads()
        if thread.name.startswith("asyncio-portal-")
    }
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # This public activation endpoint uses the overridden disposable DB;
        # invalid format exercises and persists the normal failed-attempt path.
        rejected = client.post("/organizations", json={
            "name": "Rejected Store",
            "slug": "rejected-store",
            "owner_email": "rejected@example.com",
            "owner_password": "StrongPass123!",
            "activation_code": "!" * 24,
        })
        assert rejected.status_code == 400

    with http_database() as db:
        assert db.scalar(select(func.count()).select_from(ActivationAttempt)) == 1
    assert not any(
        thread.name.startswith("asyncio-portal-") and thread.ident not in portal_threads_before
        for thread in enumerate_threads()
    )


def test_http_activation_owner_auth_personnel_permissions_and_tenant_isolation(http_database):
    owner_password = "StrongPass123!"
    activation_code = generate_code()
    _issue(http_database, activation_code)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        created = client.post("/organizations", json={
            "name": "HTTP Acceptance Store",
            "slug": "http-acceptance-store",
            "owner_email": "owner@http-acceptance.example",
            "owner_password": owner_password,
            "activation_code": activation_code,
        })
        assert created.status_code == 201
        organization_id = created.json()["id"]

        # A consumed code cannot create a second tenant.
        reused = client.post("/organizations", json={
            "name": "Reused Store",
            "slug": "reused-store",
            "owner_email": "reused@http-acceptance.example",
            "owner_password": owner_password,
            "activation_code": activation_code,
        })
        assert reused.status_code == 400

        owner_headers = _login(client, "owner@http-acceptance.example", owner_password)
        authenticated = client.get("/auth/me", headers=owner_headers)
        assert authenticated.status_code == 200
        assert authenticated.json()["email"] == "owner@http-acceptance.example"

        owner_permissions = client.get(
            f"/organizations/{organization_id}/my-permissions", headers=owner_headers
        )
        assert owner_permissions.status_code == 200
        assert len(owner_permissions.json()["permissions"]) == 27

        manager = client.post(
            f"/organizations/{organization_id}/store-tree/personnel",
            headers=owner_headers,
            json={"email": "manager@http-acceptance.example", "password": owner_password, "role_name": "manager"},
        )
        staff = client.post(
            f"/organizations/{organization_id}/store-tree/personnel",
            headers=owner_headers,
            json={"email": "staff@http-acceptance.example", "password": owner_password, "role_name": "staff"},
        )
        assert manager.status_code == 201
        assert staff.status_code == 201
        manager_headers = _login(client, "manager@http-acceptance.example", owner_password)
        staff_headers = _login(client, "staff@http-acceptance.example", owner_password)

        manager_assignment = client.put(
            f"/organizations/{organization_id}/role-permissions",
            headers=owner_headers,
            json={"role_name": "manager", "permission_keys": ["inventory.view"]},
        )
        staff_assignment = client.put(
            f"/organizations/{organization_id}/role-permissions",
            headers=owner_headers,
            json={"role_name": "staff", "permission_keys": ["sales.create"]},
        )
        assert manager_assignment.status_code == staff_assignment.status_code == 200

        manager_permissions = client.get(
            f"/organizations/{organization_id}/my-permissions", headers=manager_headers
        )
        staff_permissions = client.get(
            f"/organizations/{organization_id}/my-permissions", headers=staff_headers
        )
        assert manager_permissions.json()["permissions"] == ["inventory.view"]
        assert staff_permissions.json()["permissions"] == ["sales.create"]
        assert client.put(
            f"/organizations/{organization_id}/role-permissions",
            headers=manager_headers,
            json={"role_name": "manager", "permission_keys": []},
        ).status_code == 403

        second_code = generate_code()
        _issue(http_database, second_code)
        second = client.post("/organizations", json={
            "name": "HTTP Other Tenant",
            "slug": "http-other-tenant",
            "owner_email": "other-owner@http-acceptance.example",
            "owner_password": owner_password,
            "activation_code": second_code,
        })
        assert second.status_code == 201
        other_id = second.json()["id"]
        assert client.get(
            f"/organizations/{other_id}/my-permissions", headers=owner_headers
        ).status_code == 403

    with http_database() as db:
        assert db.scalar(select(func.count()).select_from(Organization)) == 2
        assert db.scalar(select(func.count()).select_from(Membership)) == 4
        redeemed = db.scalar(select(ActivationCode).where(
            ActivationCode.code_digest == digest_code(activation_code)
        ))
        assert redeemed is not None and redeemed.status == "redeemed"
