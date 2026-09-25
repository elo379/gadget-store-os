import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
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

    organization = relationship("Organization")
    user = relationship("User")
