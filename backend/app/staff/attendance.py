import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.staff.models import StaffProfile


class AttendanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clock_in: Mapped[datetime] = mapped_column(
        nullable=False
    )
    clock_out: Mapped[datetime | None] = mapped_column(
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open"
    )
    notes: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )

    organization = relationship("Organization")
    staff = relationship("StaffProfile")


def clock_in(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    notes: str = "",
):
    staff = db.scalar(
        select(StaffProfile).where(
            StaffProfile.id == staff_id,
            StaffProfile.organization_id == organization_id,
            StaffProfile.is_active.is_(True),
        )
    )

    if staff is None:
        raise ValueError("Staff member not found")

    active = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.staff_id == staff_id,
            AttendanceRecord.status == "open",
        )
    )

    if active is not None:
        raise ValueError("Staff member is already clocked in")

    record = AttendanceRecord(
        organization_id=organization_id,
        staff_id=staff_id,
        clock_in=datetime.now(timezone.utc),
        status="open",
        notes=notes.strip(),
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def clock_out(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
):
    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.staff_id == staff_id,
            AttendanceRecord.status == "open",
        )
    )

    if record is None:
        raise ValueError("No active attendance session")

    record.clock_out = datetime.now(timezone.utc)
    record.status = "closed"

    db.commit()
    db.refresh(record)
    return record


def list_attendance(
    db: Session,
    organization_id: uuid.UUID,
):
    return list(
        db.scalars(
            select(AttendanceRecord).where(
                AttendanceRecord.organization_id == organization_id
            ).order_by(
                AttendanceRecord.clock_in.desc()
            )
        ).all()
    )
