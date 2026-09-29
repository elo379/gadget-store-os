import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership
from app.models.user import User
from app.staff.models import StaffProfile
from app.staff.schemas import StaffProfileCreate


def create_staff(
    db: Session,
    payload: StaffProfileCreate,
):
    user = db.scalar(
        select(User).where(
            User.email == payload.email,
            User.is_active.is_(True),
        )
    )

    if user is None:
        raise ValueError("User not found")

    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == payload.organization_id,
            Membership.user_id == user.id,
            Membership.is_active.is_(True),
            Membership.account_status == "active",
        )
    )
    if membership is None:
        raise ValueError("User does not belong to organization")

    staff_code = payload.staff_code.strip()
    if not staff_code:
        count = len(db.scalars(
            select(StaffProfile).where(
                StaffProfile.organization_id == payload.organization_id,
            )
        ).all())
        staff_code = f"GSOS-STF-{count + 1:03d}"

    existing = db.scalar(
        select(StaffProfile).where(
            StaffProfile.organization_id == payload.organization_id,
            StaffProfile.staff_code == staff_code,
        )
    )

    if existing is not None:
        raise ValueError("Staff code already exists")

    if db.scalar(select(StaffProfile).where(StaffProfile.organization_id == payload.organization_id, StaffProfile.user_id == user.id)) is not None:
        raise ValueError("Staff profile already exists")

    profile = StaffProfile(
        organization_id=payload.organization_id,
        user_id=user.id,
        staff_code=staff_code,
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
