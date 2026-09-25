import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.reports.access import require_reports_access
from app.reports.schemas import ReportPeriod
from app.reports.service import (
    get_customer_report,
    get_expense_report,
    get_inventory_report,
    get_product_sales_report,
    get_sales_period_report,
    get_sales_report,
    get_staff_sales_report,
)

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


def check_access(
    db: Session,
    current_user,
    organization_id: uuid.UUID,
):
    try:
        require_reports_access(
            db,
            current_user,
            organization_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )


@router.get("/{organization_id}/sales")
def sales_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_sales_report(db, organization_id)


@router.post("/{organization_id}/sales/period")
def sales_period_report(
    organization_id: uuid.UUID,
    payload: ReportPeriod,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)

    if (
        payload.start_date is not None
        and payload.end_date is not None
        and payload.start_date > payload.end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Start date must be before end date",
        )

    return get_sales_period_report(
        db,
        organization_id,
        payload.start_date,
        payload.end_date,
    )


@router.get("/{organization_id}/products")
def product_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_product_sales_report(
        db,
        organization_id,
    )


@router.get("/{organization_id}/staff")
def staff_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_staff_sales_report(
        db,
        organization_id,
    )


@router.get("/{organization_id}/expenses")
def expense_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_expense_report(
        db,
        organization_id,
    )


@router.get("/{organization_id}/inventory")
def inventory_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_inventory_report(
        db,
        organization_id,
    )


@router.get("/{organization_id}/customers")
def customer_report(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_access(db, current_user, organization_id)
    return get_customer_report(
        db,
        organization_id,
    )
