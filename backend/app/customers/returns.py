import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.inventory.constants import MOVEMENT_RETURN
from app.inventory.models import InventoryItem
from app.inventory.service import record_movement
from app.sales.models import Sale, SaleLine


class CustomerReturn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_returns"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reference_number: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0"),
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="completed",
        index=True,
    )

    sale = relationship("Sale")
    customer = relationship("Customer")
    lines = relationship(
        "CustomerReturnLine",
        back_populates="return_record",
        cascade="all, delete-orphan",
    )


class CustomerReturnLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_return_lines"

    return_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer_returns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sale_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sale_lines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    return_record = relationship(
        "CustomerReturn",
        back_populates="lines",
    )
    sale_line = relationship("SaleLine")


def process_return(
    db: Session,
    organization_id: uuid.UUID,
    sale_id: uuid.UUID,
    reference_number: str,
    lines: list[dict],
    reason: str = "",
    customer_id: uuid.UUID | None = None,
):
    sale = db.scalar(
        select(Sale).where(
            Sale.id == sale_id,
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        )
    )

    if sale is None:
        raise ValueError("Sale not found")

    existing = db.scalar(
        select(CustomerReturn).where(
            CustomerReturn.organization_id == organization_id,
            CustomerReturn.reference_number == reference_number,
        )
    )

    if existing is not None:
        raise ValueError("Return reference already exists")

    return_record = CustomerReturn(
        organization_id=organization_id,
        sale_id=sale.id,
        customer_id=customer_id,
        reference_number=reference_number.strip(),
        reason=reason.strip(),
        status="completed",
    )

    refund_total = Decimal("0")

    for item in lines:
        sale_line = db.scalar(
            select(SaleLine).where(
                SaleLine.id == item["sale_line_id"],
                SaleLine.sale_id == sale.id,
            )
        )

        if sale_line is None:
            raise ValueError("Sale line not found")

        quantity = Decimal(item["quantity"])

        if quantity <= 0 or quantity > sale_line.quantity:
            raise ValueError("Invalid return quantity")

        amount = sale_line.unit_price * quantity

        inventory = db.scalar(
            select(InventoryItem).where(
                InventoryItem.organization_id == organization_id,
                InventoryItem.product_id == sale_line.product_id,
                InventoryItem.status == "active",
            )
        )

        if inventory is None:
            raise ValueError("Inventory not found")

        record_movement(
            db=db,
            organization_id=organization_id,
            inventory_item_id=inventory.id,
            movement_type=MOVEMENT_RETURN,
            quantity=quantity,
            reason=f"Customer return {reference_number}",
        )

        return_record.lines.append(
            CustomerReturnLine(
                sale_line_id=sale_line.id,
                quantity=quantity,
                amount=amount,
                reason=reason.strip(),
            )
        )

        refund_total += amount

    return_record.refund_amount = refund_total

    db.add(return_record)
    db.commit()
    db.refresh(return_record)

    return return_record
