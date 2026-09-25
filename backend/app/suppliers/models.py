import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    contact_person: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        default="",
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization = relationship("Organization")
