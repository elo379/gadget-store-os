import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.dashboard.access import require_dashboard_access
from app.dashboard.service import (
    get_dashboard_summary,
    get_operational_metrics,
    get_low_stock_inventory,
)
from app.db.dependencies import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get("/{organization_id}/summary")
def dashboard_summary(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_dashboard_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return get_dashboard_summary(
        db,
        organization_id,
    )


@router.get("/{organization_id}/operational")
def dashboard_operational(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_dashboard_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return get_operational_metrics(
        db,
        organization_id,
    )


@router.get("/{organization_id}/low-stock")
def dashboard_low_stock(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        require_dashboard_access(db, current_user, organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    return get_low_stock_inventory(
        db,
        organization_id,
    )
