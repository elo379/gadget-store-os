from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser, LoginRequest, TokenResponse
from app.auth.service import authenticate_user
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

    return TokenResponse(access_token=token)


@router.get("/me", response_model=AuthenticatedUser)
def get_authenticated_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return current_user
