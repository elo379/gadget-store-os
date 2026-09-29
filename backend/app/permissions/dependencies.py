import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthenticatedUser
from app.db.dependencies import get_db
from app.permissions.access import require_organization_permission


def require_permission(permission_key: str) -> Callable:
    def dependency(
        organization_id: uuid.UUID,
        current_user: AuthenticatedUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> AuthenticatedUser:
        try:
            user_id = uuid.UUID(str(current_user.user_id))
        except (AttributeError, TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization context is required",
            )

        require_organization_permission(db, user_id, organization_id, permission_key)

        return current_user

    return dependency
