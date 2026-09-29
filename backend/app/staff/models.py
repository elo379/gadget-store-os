import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, String, Text, Time, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StaffProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "staff_profiles"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    staff_code: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    phone: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    job_title: Mapped[str] = mapped_column(
        String(100), nullable=False, default=""
    )
    notes: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    shift_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(9, 0))
    shift_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(17, 0))
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    organization = relationship("Organization")
    user = relationship("User")
