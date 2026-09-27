from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    AuthenticatedUser,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.auth.service import (
    authenticate_user,
    create_login_session,
    refresh_login_session,
    revoke_login_session,
)
from app.db.dependencies import get_db
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.email == payload.email,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = authenticate_user(
        str(user.id),
        payload.password,
        user.password_hash,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token, refresh_token = create_login_session(
        db,
        user,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    access_token = refresh_login_session(
        db,
        payload.refresh_token,
    )

    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=payload.refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    revoke_login_session(
        db,
        payload.refresh_token,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUser,
)
def get_authenticated_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return current_user
