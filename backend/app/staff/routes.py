import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_db
from app.staff.attendance import clock_in, clock_out, list_attendance
from app.staff.schemas import StaffProfileCreate
from app.staff.service import (
    create_staff,
    get_staff,
    get_staff_attendance_summary,
    list_staff,
)

router = APIRouter(prefix="/staff", tags=["staff"])


@router.post("")
def add_staff(
    payload: StaffProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return create_staff(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}")
def staff(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_staff(db, organization_id)


@router.post("/{organization_id}/{staff_id}/clock-in")
def staff_clock_in(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return clock_in(db, organization_id, staff_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{organization_id}/{staff_id}/clock-out")
def staff_clock_out(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return clock_out(db, organization_id, staff_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{organization_id}/attendance")
def attendance(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_attendance(db, organization_id)


@router.get("/{organization_id}/{staff_id}/attendance-summary")
def attendance_summary(
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_staff_attendance_summary(
        db,
        organization_id,
        staff_id,
    )
