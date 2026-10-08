from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
import uuid

import pytest
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.activation.models import ActivationAttempt, ActivationCode
from app.activation.service import (
    create_organization_with_code,
    digest_code,
    generate_code,
    is_rate_limited,
    normalize_code,
    register_failed_attempt,
)
from app.audit.models import AuditLog
from app.db.base import Base
from app.db.mixins import utc_now
from app.models import Membership, Organization, User
from app.api.auth.routes import login as login_route
from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest
from app.organizations.routes import create_new_organization
from app.organizations.schemas import OrganizationCreate
from app.auth.schemas import AuthenticatedUser
from app.stocktake.access import require_stocktake_access
from app.organizations.role_permissions import (
    RolePermissionUpdate,
    my_permissions,
    save_role_permissions,
)
from app.organizations.personnel import create_personnel
from app.permissions.access import user_has_permission


@pytest.fixture
def activation_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, pool_size=1)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def issue(engine, code: str, *, expires_at=None, status="issued"):
    with Session(engine) as db:
        db.add(ActivationCode(
            code_digest=digest_code(code), status=status, created_at=utc_now(), expires_at=expires_at
        ))
        db.commit()


def activate(engine, code, slug="elo-gadgets"):
    with Session(engine) as db:
        organization = create_organization_with_code(
            db,
            name="RemiDee Gadgets Ltd",
            slug=slug,
            owner_email=f"owner-{slug}@example.com",
            owner_password="StrongOwnerPassword123!",
            activation_code=code,
        )
        db.commit()
        return organization.id


def test_generated_activation_codes_are_24_normalized_characters():
    code = generate_code()
    assert len(code) == 24
    assert code.isascii() and code.isalnum() and code == code.upper()
    assert normalize_code(f"  {code.lower()}  ") == code
    with pytest.raises(ValueError, match="Invalid activation code"):
        normalize_code("too-short")


def test_operator_generator_exports_40_codes_private_and_never_prints_codes(activation_engine, tmp_path, monkeypatch, capsys):
    from sqlalchemy.orm import sessionmaker
    from scripts import manage_activation_codes

    monkeypatch.setattr(manage_activation_codes, "SessionLocal", sessionmaker(bind=activation_engine))
    output = tmp_path / "launch-codes.txt"
    manage_activation_codes.generate_batch(40, output, None)
    exported = output.read_text().splitlines()
    assert len(exported) == 40
    assert all(len(code) == 24 and code.isascii() and code.isalnum() for code in exported)
    assert output.stat().st_mode & 0o777 == 0o600
    captured = capsys.readouterr().out
    assert all(code not in captured for code in exported)
    with Session(activation_engine) as db:
        assert db.query(ActivationCode).count() == 40

    output.write_text("keep-existing")
    with pytest.raises(FileExistsError):
        manage_activation_codes.generate_batch(1, output, None)
    assert output.read_text() == "keep-existing"


def test_valid_code_creates_active_owner_and_audit_then_cannot_be_reused(activation_engine):
    code = generate_code()
    issue(activation_engine, code)
    organization_id = activate(activation_engine, code)
    with Session(activation_engine) as db:
        organization = db.get(Organization, organization_id)
        owner = db.scalar(select(User).where(User.email == "owner-elo-gadgets@example.com"))
        membership = db.scalar(select(Membership).where(Membership.organization_id == organization_id))
        activation = db.scalar(select(ActivationCode).where(ActivationCode.code_digest == digest_code(code)))
        audit = db.scalar(select(AuditLog).where(AuditLog.organization_id == organization_id))
        assert organization is not None and organization.is_active
        assert owner is not None and owner.is_active
        assert membership is not None and membership.is_owner and membership.role_name == "owner"
        assert activation.status == "redeemed"
        assert activation.redeemed_at is not None and activation.organization_id == organization_id
        assert audit.action == "organization.created" and audit.user_id == owner.id
        with pytest.raises(ValueError, match="unavailable"):
            create_organization_with_code(
                db, name="Second Store", slug="second-store", owner_email="second@example.com",
                owner_password="StrongOwnerPassword123!", activation_code=code,
            )


def test_public_activation_route_creates_owner_who_can_log_in(activation_engine):
    code = generate_code()
    issue(activation_engine, code)
    scope = {
        "type": "http", "method": "POST", "path": "/organizations", "headers": [],
        "client": ("198.51.100.20", 1234), "server": ("localhost", 80),
        "scheme": "http", "query_string": b"",
    }
    with Session(activation_engine) as db:
        organization = create_new_organization(
            OrganizationCreate(
                name="RemiDee Gadgets Ltd", slug="elo-gadgets", owner_email="admin@elogadgets.ng",
                owner_password="StrongOwnerPassword123!", activation_code=code,
            ),
            Request(scope),
            db,
        )
        db.commit()
        tokens = login_route(LoginRequest(email="admin@elogadgets.ng", password="StrongOwnerPassword123!"), db)
        principal = get_current_user(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=tokens.access_token), db
        )
        membership = db.scalar(select(Membership).where(
            Membership.organization_id == organization.id, Membership.user_id == uuid.UUID(principal.user_id)
        ))
        assert principal.email == "admin@elogadgets.ng"
        assert membership is not None and membership.is_owner and membership.account_status == "active"
        assert db.scalar(select(ActivationAttempt)) is None


def test_invalid_expired_and_revoked_codes_cannot_create_organizations(activation_engine):
    expired = generate_code()
    revoked = generate_code()
    issue(activation_engine, expired, expires_at=utc_now() - timedelta(minutes=1))
    issue(activation_engine, revoked, status="revoked")
    for code in ("0" * 24, expired, revoked):
        with Session(activation_engine) as db:
            with pytest.raises(ValueError):
                create_organization_with_code(
                    db, name="No Store", slug=f"no-{code[:5]}", owner_email=f"{code[:5]}@example.com",
                    owner_password="StrongOwnerPassword123!", activation_code=code,
                )
            if code == expired:
                db.commit()
            else:
                db.rollback()
    with Session(activation_engine) as db:
        assert db.scalar(select(Organization)) is None
        expired_row = db.scalar(select(ActivationCode).where(ActivationCode.code_digest == digest_code(expired)))
        assert expired_row.status == "expired"


def test_concurrent_redemption_has_exactly_one_winner(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'activation-race.db'}", connect_args={"timeout": 10})
    Base.metadata.create_all(engine)
    code = generate_code()
    issue(engine, code)
    gate = Barrier(2)

    def redeem():
        with Session(engine) as db:
            gate.wait(timeout=5)
            result = db.execute(
                update(ActivationCode)
                .where(ActivationCode.code_digest == digest_code(code), ActivationCode.status == "issued")
                .values(status="redeemed", redeemed_at=utc_now())
            )
            db.commit()
            return result.rowcount

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(lambda _: redeem(), range(2)))
    assert outcomes == [0, 1]
    engine.dispose()


def test_failed_redemption_rolls_back_tenant_before_attempt_is_committed(activation_engine, monkeypatch):
    from types import SimpleNamespace

    import app.activation.service as activation_service

    code = generate_code()
    issue(activation_engine, code)
    with Session(activation_engine) as db:
        real_execute = db.execute

        def lose_redemption(statement, *args, **kwargs):
            if "update activation_codes" in str(statement).lower():
                return SimpleNamespace(rowcount=0)
            return real_execute(statement, *args, **kwargs)

        monkeypatch.setattr(db, "execute", lose_redemption)
        with pytest.raises(ValueError, match="unavailable"):
            create_organization_with_code(
                db, name="Racing Store", slug="racing-store", owner_email="racing-owner@example.com",
                owner_password="StrongOwnerPassword123!", activation_code=code,
            )
        # This is what the router does after a failed activation; committing the
        # throttling attempt must not commit the flushed tenant records.
        register_failed_attempt(db, "198.51.100.99")
        db.commit()

    with Session(activation_engine) as db:
        assert db.scalar(select(Organization).where(Organization.slug == "racing-store")) is None
        assert db.scalar(select(User).where(User.email == "racing-owner@example.com")) is None
        assert db.scalar(select(Membership)) is None
        assert db.scalar(select(ActivationCode).where(ActivationCode.code_digest == digest_code(code))).status == "issued"
        assert db.scalar(select(ActivationAttempt)) is not None


def test_attempt_throttle_persists_per_address_and_resets_after_window(activation_engine):
    with Session(activation_engine) as db:
        for _ in range(10):
            assert register_failed_attempt(db, "192.0.2.10") is False
        assert register_failed_attempt(db, "192.0.2.10") is True
        assert is_rate_limited(db, "192.0.2.10") is True
        assert register_failed_attempt(db, "192.0.2.11") is False
        row = db.scalar(select(ActivationAttempt))
        row.window_started_at = utc_now() - timedelta(minutes=20)
        db.commit()
        assert register_failed_attempt(db, "192.0.2.10") is False


def test_stocktake_access_accepts_org_owner_and_rejects_other_tenant(activation_engine):
    with Session(activation_engine) as db:
        # Use the internal setup service to isolate the access contract from activation.
        from app.organizations.service import create_organization
        store = create_organization(
            db, "Access Store", "access-store", "access-owner@example.com", "StrongOwnerPassword123!"
        )
        owner = db.scalar(select(User).where(User.email == "access-owner@example.com"))
        other = User(email="outside@example.com", password_hash="unused", is_active=True)
        db.add(other)
        db.flush()
        assert require_stocktake_access(db, AuthenticatedUser(user_id=str(owner.id), email=owner.email), store.id).is_owner
        with pytest.raises(ValueError, match="access denied"):
            require_stocktake_access(db, AuthenticatedUser(user_id=str(other.id), email=other.email), store.id)


def test_owner_configures_manager_permissions_and_revocation_is_immediate(activation_engine):
    from app.organizations.service import create_organization

    with Session(activation_engine) as db:
        store = create_organization(
            db, "Permissions Store", "permissions-store", "permission-owner@example.com", "StrongOwnerPassword123!"
        )
        owner = db.scalar(select(User).where(User.email == "permission-owner@example.com"))
        owner_membership = db.scalar(select(Membership).where(
            Membership.organization_id == store.id, Membership.user_id == owner.id
        ))
        manager = create_personnel(
            db, store.id, owner_membership, "manager@example.com", "StrongManagerPassword123!", "manager"
        )
        owner_auth = AuthenticatedUser(user_id=str(owner.id), email=owner.email)
        manager_auth = AuthenticatedUser(user_id=str(manager.user_id), email="manager@example.com")
        assert len(my_permissions(store.id, db, owner_auth)["permissions"]) == 27

        save_role_permissions(
            store.id, RolePermissionUpdate(role_name="manager", permission_keys=["inventory.view", "sales.create"]),
            db, owner_auth,
        )
        assert user_has_permission(db, manager.user_id, store.id, "sales.create")
        assert my_permissions(store.id, db, manager_auth)["permissions"] == ["inventory.view", "sales.create"]

        save_role_permissions(
            store.id, RolePermissionUpdate(role_name="manager", permission_keys=["inventory.view"]), db, owner_auth
        )
        assert not user_has_permission(db, manager.user_id, store.id, "sales.create")
        with pytest.raises(Exception) as denied:
            save_role_permissions(
                store.id, RolePermissionUpdate(role_name="manager", permission_keys=[]), db, manager_auth
            )
        assert getattr(denied.value, "status_code", None) == 403


def test_owner_permission_api_routes_are_included_in_application():
    from app.main import app

    paths = app.openapi()["paths"]
    assert "/organizations/{organization_id}/my-permissions" in paths
    assert "/organizations/{organization_id}/role-permissions" in paths
    assert "put" in paths["/organizations/{organization_id}/role-permissions"]
