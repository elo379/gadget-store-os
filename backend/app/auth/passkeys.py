import uuid

from dotenv import load_dotenv
load_dotenv()
import base64
import json
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.auth.service import create_login_session
from app.models.passkey import PasskeyChallenge, PasskeyCredential
from app.models.user import User

CHALLENGE_MINUTES = 5
RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "Gadget Store OS")
RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:3000")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))


def _save_challenge(
    db: Session,
    challenge: bytes,
    ceremony: str,
    user_id: str | None = None,
) -> None:
    db.add(
        PasskeyChallenge(
            user_id=uuid.UUID(user_id) if user_id else None,
            challenge=_b64(challenge),
            ceremony=ceremony,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=CHALLENGE_MINUTES),
        )
    )
    db.commit()


def _consume_challenge(
    db: Session,
    challenge: bytes,
    ceremony: str,
) -> PasskeyChallenge | None:
    now = datetime.now(timezone.utc)
    challenge_text = _b64(challenge)
    result = db.execute(
        update(PasskeyChallenge)
        .where(
            PasskeyChallenge.challenge == challenge_text,
            PasskeyChallenge.ceremony == ceremony,
            PasskeyChallenge.consumed.is_(False),
            PasskeyChallenge.expires_at > now,
        )
        .values(consumed=True)
    )
    db.commit()
    if result.rowcount != 1:
        # Expired challenges are also retired, without making them usable.
        db.execute(
            update(PasskeyChallenge)
            .where(
                PasskeyChallenge.challenge == challenge_text,
                PasskeyChallenge.ceremony == ceremony,
                PasskeyChallenge.consumed.is_(False),
            )
            .values(consumed=True)
        )
        db.commit()
        return None
    return db.scalar(select(PasskeyChallenge).where(PasskeyChallenge.challenge == challenge_text))


def _credential_payload(payload: dict, ceremony: str) -> dict:
    """Adapt the existing compact API shape to WebAuthn's JSON credential shape."""
    raw_id = payload.get("raw_id") or payload.get("rawId")
    credential_id = payload.get("credential_id") or payload.get("id") or raw_id
    client_data = payload.get("client_data_json") or payload.get("clientDataJSON")
    response = {"clientDataJSON": client_data}
    if ceremony == "registration":
        response["attestationObject"] = payload.get("attestation_object") or payload.get("attestationObject")
    else:
        response["authenticatorData"] = payload.get("authenticator_data") or payload.get("authenticatorData")
        response["signature"] = payload.get("signature")
        response["userHandle"] = payload.get("user_handle") or payload.get("userHandle")
    return {"id": credential_id, "rawId": raw_id, "type": "public-key", "response": response}


def registration_options(db: Session, user: User) -> dict:
    existing = db.scalars(
        select(PasskeyCredential).where(
            PasskeyCredential.user_id == uuid.UUID(str(user.id)),
            PasskeyCredential.revoked.is_(False),
        )
    ).all()

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=user.email,
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=_unb64(item.credential_id))
            for item in existing
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )

    _save_challenge(db, options.challenge, "registration", str(user.id))
    return json.loads(options_to_json(options))


def verify_registration(
    db: Session,
    user: User,
    payload: dict,
) -> dict:
    credential = _credential_payload(payload, "registration")
    challenge_value = credential["response"].get("clientDataJSON")
    if not challenge_value:
        raise ValueError("Missing client data")

    client_data = json.loads(_unb64(challenge_value))
    challenge = _unb64(client_data["challenge"])

    saved = _consume_challenge(db, challenge, "registration")
    if saved is None or saved.user_id != user.id:
        raise ValueError("Invalid or expired passkey challenge")

    verification = verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        require_user_verification=True,
    )

    credential_id = _b64(verification.credential_id)
    item = PasskeyCredential(
        user_id=uuid.UUID(str(user.id)),
        credential_id=credential_id,
        public_key=_b64(verification.credential_public_key),
        sign_count=verification.sign_count,
        name=payload.get("name") or "This device",
        transports=json.dumps(payload.get("transports", [])),
    )

    db.add(item)
    db.commit()

    return {
        "id": str(item.id),
        "name": item.name,
        "created_at": item.created_at,
    }


def authentication_options(db: Session) -> dict:
    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    _save_challenge(db, options.challenge, "authentication")
    return json.loads(options_to_json(options))


def verify_authentication(db: Session, payload: dict) -> dict:
    credential = _credential_payload(payload, "authentication")
    credential_id = credential.get("rawId")
    if not credential_id:
        raise ValueError("Missing credential")

    item = db.scalar(
        select(PasskeyCredential).where(
            PasskeyCredential.credential_id == credential_id,
            PasskeyCredential.revoked.is_(False),
        )
    )

    if item is None:
        raise ValueError("Passkey was not found")

    user = db.get(User, item.user_id)
    if user is None or not user.is_active:
        raise ValueError("User account is inactive")

    client_data = json.loads(_unb64(credential["response"]["clientDataJSON"]))
    challenge = _unb64(client_data["challenge"])

    saved = _consume_challenge(db, challenge, "authentication")
    if saved is None:
        raise ValueError("Invalid or expired passkey challenge")

    verification = verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=_unb64(item.public_key),
        credential_current_sign_count=item.sign_count,
        require_user_verification=True,
    )

    item.sign_count = verification.new_sign_count
    item.last_used_at = datetime.now(timezone.utc)
    db.commit()

    access_token, refresh_token = create_login_session(db, user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
