import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.staff.models import StaffProfile
from app.staff.schemas import StaffProfileCreate


def create_staff(
    db: Session,
    payload: StaffProfileCreate,
):
    user = db.scalar(
        select(User).where(
            User.id == payload.user_id,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise ValueError("User not found")

    existing = db.scalar(
        select(StaffProfile).where(
            StaffProfile.organization_id == payload.organization_id,
            StaffProfile.staff_code == payload.staff_code.strip(),
        )
    )

    if existing is not None:
        raise ValueError("Staff code already exists")

    profile = StaffProfile(
        organization_id=payload.organization_id,
        user_id=payload.user_id,
        staff_code=payload.staff_code.strip(),
        phone=payload.phone.strip(),
        job_title=payload.job_title.strip(),
        notes=payload.notes.strip(),
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_staff(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
):
    return db.scalar(
        select(StaffProfile).where(
            StaffProfile.id == staff_id,
            StaffProfile.organization_id == organization_id,
        )
    )


def list_staff(
    db: Session,
    organization_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(StaffProfile).where(
                StaffProfile.organization_id == organization_id
            ).order_by(StaffProfile.staff_code.asc())
        ).all()
    )


def get_staff_attendance_summary(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
):
    from app.staff.attendance import AttendanceRecord

    records = list(
        db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.organization_id == organization_id,
                AttendanceRecord.staff_id == staff_id,
                AttendanceRecord.status == "closed",
            )
        ).all()
    )

    total_seconds = 0

    for record in records:
        if record.clock_out is not None:
            total_seconds += (
                record.clock_out - record.clock_in
            ).total_seconds()

    return {
        "staff_id": staff_id,
        "attendance_count": len(records),
        "total_hours": round(total_seconds / 3600, 2),
    }
