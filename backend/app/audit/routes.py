import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit.access import can_view_audit
from app.audit.schemas import AuditLogCreate, AuditLogResponse
from app.audit.service import create_audit_log, list_audit_logs
from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.post(
    "",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_audit(
    payload: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not can_view_audit(
        db,
        current_user.id,
        payload.organization_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit access denied",
        )

    if payload.user_id is None:
        payload.user_id = current_user.id

    return create_audit_log(db, payload)


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

    if not can_view_audit(
        db,
        current_user.id,
        organization_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Audit access denied",
        )

    return list_audit_logs(
        db,
        organization_id,
        limit,
    )
