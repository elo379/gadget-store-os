import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.finance.service import get_financial_summary

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/{organization_id}/summary")
def financial_summary(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_financial_summary(
        db,
        organization_id,
    )
