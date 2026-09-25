from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/me", response_model=AuthenticatedUser)
def get_authenticated_user(
    user_id: str = Depends(get_current_user),
):
    return AuthenticatedUser(
        user_id=user_id,
        email="authenticated-user@example.com",
    )
