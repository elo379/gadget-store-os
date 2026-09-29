import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.passkeys import (
    authentication_options,
    registration_options,
    verify_authentication,
    verify_registration,
)
from app.auth.schemas import AuthenticatedUser
from app.db.dependencies import get_db
from app.models.user import User

router = APIRouter(
    prefix="/auth/passkeys",
    tags=["Passkeys"],
)


def _user_from_auth(
    current_user: AuthenticatedUser,
    db: Session,
) -> User:
    user_id = uuid.UUID(str(current_user.user_id))
    user = db.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or does not exist",
        )

    return user


@router.post("/register/options")
def register_options(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = _user_from_auth(current_user, db)
    return registration_options(db, user)


@router.post("/register/verify")
def register_verify(
    payload: dict,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = _user_from_auth(current_user, db)

    try:
        return verify_registration(db, user, payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passkey registration failed",
        ) from exc


@router.post("/login/options")
def login_options(db: Session = Depends(get_db)):
    return authentication_options(db)


@router.post("/login/verify")
def login_verify(
    payload: dict,
    db: Session = Depends(get_db),
):
    try:
        return verify_authentication(db, payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Passkey authentication failed",
        ) from exc


@router.get("")
def list_passkeys(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = _user_from_auth(current_user, db)

    from sqlalchemy import select
    from app.models.passkey import PasskeyCredential

    items = db.scalars(
        select(PasskeyCredential)
        .where(PasskeyCredential.user_id == user.id)
        .order_by(PasskeyCredential.created_at.desc())
    ).all()

    return [
        {
            "id": str(item.id),
            "name": item.name,
            "last_used_at": item.last_used_at,
            "created_at": item.created_at,
            "revoked": item.revoked,
        }
        for item in items
        if not item.revoked
    ]


@router.delete("/{passkey_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_passkey(
    passkey_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = _user_from_auth(current_user, db)

    from app.models.passkey import PasskeyCredential

    item = db.scalar(
        __import__("sqlalchemy").select(PasskeyCredential).where(
            PasskeyCredential.id == passkey_id,
            PasskeyCredential.user_id == user.id,
            PasskeyCredential.revoked.is_(False),
        )
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passkey not found",
        )

    item.revoked = True
    db.commit()
