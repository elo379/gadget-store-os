import uuid
from datetime import date, datetime, timezone

from sqlalchemy import ForeignKey, String, Text, select, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.staff.models import StaffProfile


class AttendanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (Index("uq_attendance_one_open_per_staff", "organization_id", "staff_id", unique=True, sqlite_where=text("status = 'open'"), postgresql_where=text("status = 'open'")),)

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
    work_date: Mapped[date] = mapped_column(nullable=False, default=lambda: datetime.now(timezone.utc).date())
    late_minutes: Mapped[int] = mapped_column(nullable=False, default=0)
    early_departure_minutes: Mapped[int] = mapped_column(nullable=False, default=0)

    organization = relationship("Organization")
    staff = relationship("StaffProfile")


class StaffAbsence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff_absences"
    __table_args__ = (UniqueConstraint("organization_id", "staff_id", "absence_date", name="uq_staff_absence_org_staff_date"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("staff_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    absence_date: Mapped[date] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


def clock_in(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    notes: str = "",
    actor_user_id: uuid.UUID | None = None,
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

    now = datetime.now(timezone.utc)
    today = now.date()
    already_today = db.scalar(select(AttendanceRecord).where(
        AttendanceRecord.organization_id == organization_id,
        AttendanceRecord.staff_id == staff_id,
        AttendanceRecord.work_date == today,
    ))
    if already_today is not None:
        raise ValueError("Attendance is already recorded for today")

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
        clock_in=now,
        work_date=today,
        late_minutes=max(0, int((now - datetime.combine(today, staff.shift_start, timezone.utc)).total_seconds() // 60) - staff.grace_minutes),
        status="open",
        notes=notes.strip(),
    )

    db.add(record)
    if actor_user_id is not None:
        from app.audit.models import AuditLog
        import json
        db.flush()
        db.add(AuditLog(organization_id=organization_id, user_id=actor_user_id, action="attendance.clocked_in", entity_type="attendance", entity_id=record.id, description="Staff clocked in", metadata_json=json.dumps({"staff_id": str(staff_id), "work_date": today.isoformat()})))
    db.commit()
    db.refresh(record)
    return record


def clock_out(
    db: Session,
    organization_id: uuid.UUID,
    staff_id: uuid.UUID,
    actor_user_id: uuid.UUID | None = None,
):
    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.staff_id == staff_id,
            AttendanceRecord.organization_id == organization_id,
            AttendanceRecord.status == "open",
        )
    )

    if record is None:
        raise ValueError("No active attendance session")

    now = datetime.now(timezone.utc)
    record.clock_out = now
    staff = db.scalar(select(StaffProfile).where(
        StaffProfile.id == staff_id,
        StaffProfile.organization_id == organization_id,
    ))
    scheduled_end = datetime.combine(record.work_date, staff.shift_end, timezone.utc)
    record.early_departure_minutes = max(0, int((scheduled_end - now).total_seconds() // 60))
    record.status = "closed"
    if actor_user_id is not None:
        from app.audit.models import AuditLog
        import json
        db.add(AuditLog(organization_id=organization_id, user_id=actor_user_id, action="attendance.clocked_out", entity_type="attendance", entity_id=record.id, description="Staff clocked out", metadata_json=json.dumps({"staff_id": str(staff_id), "work_date": record.work_date.isoformat()})))

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
