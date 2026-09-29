import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Warranty(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "warranties"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device_records.id", ondelete="RESTRICT"), index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), index=True)
    starts_at: Mapped[date] = mapped_column(Date, nullable=False)
    ends_at: Mapped[date] = mapped_column(Date, nullable=False)
    coverage: Mapped[str] = mapped_column(String(200), nullable=False, default="manufacturer")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    claims: Mapped[str] = mapped_column(Text, nullable=False, default="")

    device = relationship("DeviceRecord")
    customer = relationship("Customer")
    sale = relationship("Sale")


class RepairCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repair_cases"
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("device_records.id", ondelete="RESTRICT"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    reference_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="intake", index=True)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parts: Mapped[str] = mapped_column(Text, nullable=False, default="")
    labour: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    customer_charge: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    device = relationship("DeviceRecord")
    customer = relationship("Customer")
    status_history = relationship("RepairStatusHistory", cascade="all, delete-orphan", order_by="RepairStatusHistory.created_at")


class RepairStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "repair_status_history"
    repair_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("repair_cases.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
