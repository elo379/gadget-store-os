import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import app.models  # noqa: F401 - register model metadata
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import passkeys
from app.auth.passkeys import _consume_challenge, _save_challenge, verify_authentication, verify_registration
from app.db.base import Base
from app.models.passkey import PasskeyChallenge, PasskeyCredential
from app.models.user import User


def _session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def test_passkey_challenge_is_single_use():
    Session = _session_factory()
    with Session() as db:
        challenge = b"single-use-challenge"
        _save_challenge(db, challenge, "authentication")

        assert _consume_challenge(db, challenge, "authentication") is not None
        assert _consume_challenge(db, challenge, "authentication") is None


def test_expired_passkey_challenge_is_retired():
    Session = _session_factory()
    with Session() as db:
        challenge = b"expired-challenge"
        db.add(PasskeyChallenge(
            challenge=_b64(challenge), ceremony="authentication",
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1), consumed=False,
        ))
        db.commit()

        assert _consume_challenge(db, challenge, "authentication") is None
        item = db.scalar(select(PasskeyChallenge).where(PasskeyChallenge.challenge == _b64(challenge)))
        assert item is not None and item.consumed


def test_registration_challenge_is_bound_to_authenticated_user():
    Session = _session_factory()
    with Session() as db:
        user = User(email=f"passkey-{uuid.uuid4()}@example.com", password_hash="unused", is_active=True)
        other_user = User(email=f"passkey-{uuid.uuid4()}@example.com", password_hash="unused", is_active=True)
        db.add_all([user, other_user])
        db.flush()
        challenge = b"owned-registration-challenge"
        _save_challenge(db, challenge, "registration", str(other_user.id))
        client_data = _b64(json.dumps({"challenge": _b64(challenge)}).encode())

        try:
            verify_registration(db, user, {
                "credential_id": _b64(b"credential"),
                "raw_id": _b64(b"credential"),
                "client_data_json": client_data,
                "attestation_object": _b64(b"attestation"),
            })
        except ValueError as exc:
            assert "challenge" in str(exc).lower()
        else:
            raise AssertionError("registration challenge from another user was accepted")


def test_registration_uses_standard_webauthn_payload_and_binds_credential(monkeypatch):
    Session = _session_factory()
    with Session() as db:
        user = User(email=f"register-{uuid.uuid4()}@example.com", password_hash="unused", is_active=True)
        db.add(user)
        db.commit()
        challenge = b"valid-registration"
        _save_challenge(db, challenge, "registration", str(user.id))
        client_data = _b64(json.dumps({"challenge": _b64(challenge)}).encode())

        def verify(**kwargs):
            assert kwargs["credential"]["rawId"] == _b64(b"registration-id")
            assert kwargs["credential"]["response"]["attestationObject"] == _b64(b"attestation")
            return SimpleNamespace(credential_id=b"registration-id", credential_public_key=b"public-key", sign_count=0)

        monkeypatch.setattr(passkeys, "verify_registration_response", verify)
        result = verify_registration(db, user, {
            "credential_id": _b64(b"registration-id"), "raw_id": _b64(b"registration-id"),
            "client_data_json": client_data, "attestation_object": _b64(b"attestation"),
        })
        credential = db.scalar(select(PasskeyCredential).where(PasskeyCredential.id == uuid.UUID(result["id"])))
        assert credential is not None
        assert credential.user_id == user.id
        assert credential.credential_id == _b64(b"registration-id")


def test_authentication_verifies_payload_updates_counter_and_rejects_replay(monkeypatch):
    Session = _session_factory()
    with Session() as db:
        user = User(email=f"authenticate-{uuid.uuid4()}@example.com", password_hash="unused", is_active=True)
        db.add(user)
        db.flush()
        credential = PasskeyCredential(
            user_id=user.id, credential_id=_b64(b"authentication-id"), public_key=_b64(b"public-key"),
            sign_count=2, name="Test key", revoked=False,
        )
        db.add(credential)
        db.commit()
        challenge = b"valid-authentication"
        _save_challenge(db, challenge, "authentication")
        client_data = _b64(json.dumps({"challenge": _b64(challenge)}).encode())

        def verify(**kwargs):
            assert kwargs["credential"]["rawId"] == _b64(b"authentication-id")
            assert kwargs["credential"]["response"]["authenticatorData"] == _b64(b"auth-data")
            assert kwargs["credential"]["response"]["signature"] == _b64(b"signature")
            assert kwargs["credential_current_sign_count"] == 2
            return SimpleNamespace(new_sign_count=3)

        monkeypatch.setattr(passkeys, "verify_authentication_response", verify)
        payload = {
            "credential_id": _b64(b"authentication-id"), "raw_id": _b64(b"authentication-id"),
            "client_data_json": client_data, "authenticator_data": _b64(b"auth-data"),
            "signature": _b64(b"signature"), "user_handle": None,
        }
        session = verify_authentication(db, payload)
        assert session["access_token"] and session["refresh_token"]
        assert credential.sign_count == 3
        with pytest.raises(ValueError, match="challenge"):
            verify_authentication(db, payload)
