import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.finance.service import get_financial_summary, get_reconciliation
from app.permissions.access import require_organization_permission

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/{organization_id}/summary")
def financial_summary(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    require_organization_permission(
        db, uuid.UUID(current_user.user_id), organization_id, "finance.view"
    )
    return get_financial_summary(
        db,
        organization_id,
    )


@router.get("/{organization_id}/reconciliation")
def reconciliation(organization_id: uuid.UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    require_organization_permission(db, uuid.UUID(current_user.user_id), organization_id, "finance.view")
    return get_reconciliation(db, organization_id)
