import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InventoryLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_locations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
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


class InventoryItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_items"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("inventory_locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0"),
    )

    reserved_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0"),
    )

    average_unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    organization = relationship("Organization")
    product = relationship("Product")
    location = relationship("InventoryLocation")
