import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.db.dependencies import get_db
from app.permissions.access import user_has_permission


def require_permission(permission_key: str) -> Callable:
    def dependency(
        current_user: AuthenticatedUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> AuthenticatedUser:
        try:
            organization_id = uuid.UUID(str(current_user.organization_id))
            user_id = uuid.UUID(str(current_user.user_id))
        except (AttributeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context is required",
            )

        if not user_has_permission(
            db,
            organization_id,
            user_id,
            permission_key,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return dependency
