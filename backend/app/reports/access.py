import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.user import User
from app.permissions.access import require_organization_permission


def require_reports_access(
    db: Session,
    user: User,
    organization_id: uuid.UUID,
):
    try:
        return require_organization_permission(db, user.id, organization_id, "reports.view")
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            raise ValueError("Reports access denied") from exc
        raise
