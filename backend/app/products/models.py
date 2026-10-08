import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ProductCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_categories"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
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


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("organization_id", "sku", name="uq_products_org_sku"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    brand: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    is_serialized: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    product_type: Mapped[str] = mapped_column(String(40), nullable=False, default="other")
    barcode: Mapped[str] = mapped_column(String(150), nullable=False, default="")
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    reorder_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=Decimal("0"))

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization = relationship("Organization")
    category = relationship("ProductCategory")
