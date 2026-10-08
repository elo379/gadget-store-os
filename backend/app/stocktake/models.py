import uuid
from decimal import Decimal

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Stocktake(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stocktakes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reference_number: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="draft", index=True
    )
    notes: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization")
    location = relationship("InventoryLocation")
    lines = relationship(
        "StocktakeLine",
        back_populates="stocktake",
        cascade="all, delete-orphan",
    )


class StocktakeLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stocktake_lines"

    stocktake_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stocktakes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("inventory_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    expected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False
    )
    counted_quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 3), nullable=True
    )
    variance: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=Decimal("0")
    )
    notes: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    counted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    stocktake = relationship(
        "Stocktake",
        back_populates="lines",
    )
    inventory_item = relationship("InventoryItem")
