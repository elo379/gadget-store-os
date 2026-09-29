from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DeviceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "device_records"
    __table_args__ = tuple(
        Index(
            f"uq_device_records_org_{column}", "organization_id", column,
            unique=True, sqlite_where=text(f"{column} IS NOT NULL"),
            postgresql_where=text(f"{column} IS NOT NULL"),
        )
        for column in ("imei", "imei_2", "serial_number", "barcode")
    )

    organization_id = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    product_id = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    imei = mapped_column(
        String(15),
        nullable=True,
        index=True,
    )

    imei_2 = mapped_column(
        String(15),
        nullable=True,
        index=True,
    )

    serial_number = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    barcode = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    brand = mapped_column(
        String(100),
        nullable=False,
        default="",
    )

    model = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    variant = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    storage = mapped_column(
        String(50),
        nullable=False,
        default="",
    )

    ram = mapped_column(String(50), nullable=False, default="")

    color = mapped_column(
        String(75),
        nullable=False,
        default="",
    )

    network_sim = mapped_column(String(100), nullable=False, default="")
    grade = mapped_column(String(50), nullable=False, default="")
    selling_price = mapped_column(Numeric(14, 2), nullable=True)
    warranty = mapped_column(String(150), nullable=False, default="")
    location_id = mapped_column(ForeignKey("inventory_locations.id", ondelete="SET NULL"), nullable=True, index=True)

    source_type = mapped_column(
        String(50),
        nullable=False,
        default="vendor",
    )

    source_name = mapped_column(
        String(200),
        nullable=False,
        default="",
    )

    source_contact = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    source_reference = mapped_column(
        String(150),
        nullable=False,
        default="",
    )

    received_by_user_id = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    condition = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
    )

    status = mapped_column(
        String(50),
        nullable=False,
        default="received",
        index=True,
    )

    acquisition_cost = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    notes = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    is_active = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization = relationship("Organization")
    product = relationship("Product")
    received_by = relationship("User")
