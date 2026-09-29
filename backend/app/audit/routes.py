import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogResponse
from app.audit.service import list_audit_logs
from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "/{organization_id}",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    organization_id: uuid.UUID,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if limit < 1 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 500",
        )

    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "audit.view")

    return list_audit_logs(
        db,
        organization_id,
        limit,
    )
