import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.inventory.constants import MOVEMENT_RETURN
from app.inventory.models import InventoryItem
from app.inventory.service import record_movement
from app.sales.models import Sale, SaleLine
from app.devices.models import DeviceRecord
from app.audit.models import AuditLog
from app.finance.models import FinancialTransaction


class CustomerReturn(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_returns"
    __table_args__ = (
        UniqueConstraint("organization_id", "reference_number", name="uq_customer_returns_org_reference"),
    )

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
    performed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

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
    condition: Mapped[str] = mapped_column(String(40), nullable=False, default="unknown")
    disposition: Mapped[str] = mapped_column(String(40), nullable=False, default="RESTOCK")
    original_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sale_payments.id", ondelete="SET NULL"), nullable=True)

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
    performed_by_user_id: uuid.UUID | None = None,
):
    try:
        return _process_return(
            db, organization_id, sale_id, reference_number, lines, reason,
            customer_id, performed_by_user_id,
        )
    except Exception:
        db.rollback()
        raise


def _process_return(
    db: Session,
    organization_id: uuid.UUID,
    sale_id: uuid.UUID,
    reference_number: str,
    lines: list[dict],
    reason: str,
    customer_id: uuid.UUID | None,
    performed_by_user_id: uuid.UUID | None,
):
    sale = db.scalar(
        select(Sale).where(
            Sale.id == sale_id,
            Sale.organization_id == organization_id,
            Sale.status == "completed",
        ).with_for_update()
    )

    if sale is None:
        raise ValueError("Sale not found")

    reference_number = reference_number.strip()
    if not reference_number:
        raise ValueError("Return reference is required")
    existing = db.scalar(
        select(CustomerReturn).where(
            CustomerReturn.organization_id == organization_id,
            CustomerReturn.reference_number == reference_number,
        )
    )

    if existing is not None:
        raise ValueError("Return reference already exists")

    if customer_id is not None and customer_id != sale.customer_id:
        raise ValueError("Return customer must match the original sale")

    return_record = CustomerReturn(
        organization_id=organization_id,
        sale_id=sale.id,
        customer_id=sale.customer_id,
        seller_user_id=sale.sold_by_user_id,
        reference_number=reference_number,
        reason=reason.strip(),
        status="completed",
        performed_by_user_id=performed_by_user_id,
    )
    db.add(return_record)
    db.flush()

    refund_total = Decimal("0")

    if not lines:
        raise ValueError("At least one return line is required")
    seen_lines = set()
    for item in lines:
        if item["sale_line_id"] in seen_lines:
            raise ValueError("A sale line may only appear once per return")
        seen_lines.add(item["sale_line_id"])
        sale_line = db.scalar(
            select(SaleLine).where(
                SaleLine.id == item["sale_line_id"],
                SaleLine.sale_id == sale.id,
            ).with_for_update()
        )

        if sale_line is None:
            raise ValueError("Sale line not found")

        quantity = Decimal(item["quantity"])

        previously_returned = db.scalar(
            select(func.coalesce(func.sum(CustomerReturnLine.quantity), 0))
            .join(CustomerReturn, CustomerReturn.id == CustomerReturnLine.return_id)
            .where(
                CustomerReturn.organization_id == organization_id,
                CustomerReturn.sale_id == sale.id,
                CustomerReturn.status == "completed",
                CustomerReturnLine.sale_line_id == sale_line.id,
            )
        )
        if quantity <= 0 or quantity + Decimal(previously_returned or 0) > sale_line.quantity:
            raise ValueError("Invalid return quantity")

        if sale_line.device_id is not None and quantity != 1:
            raise ValueError("Serialized products must be returned one device at a time")

        amount = sale_line.unit_price * quantity

        inventory_query = select(InventoryItem).where(
            InventoryItem.organization_id == organization_id,
            InventoryItem.product_id == sale_line.product_id,
            InventoryItem.status == "active",
        )
        location_id = item.get("location_id")
        if location_id is not None:
            inventory_query = inventory_query.where(InventoryItem.location_id == location_id)
        inventories = list(db.scalars(inventory_query.with_for_update()).all())
        if not inventories:
            raise ValueError("Inventory not found")
        if location_id is None and len(inventories) > 1:
            raise ValueError("Return inventory location required")
        inventory = inventories[0]

        disposition = str(item.get("disposition", "RESTOCK")).upper()
        condition = str(item.get("condition", "unknown")).lower()
        allowed = {"RESTOCK", "DAMAGED", "DEFECTIVE", "SERVICE", "WRITE OFF"}
        if disposition not in allowed:
            raise ValueError("Invalid return disposition")
        if disposition == "RESTOCK":
            record_movement(
                db=db, organization_id=organization_id, inventory_item_id=inventory.id,
                movement_type=MOVEMENT_RETURN, quantity=quantity,
                reason=f"Customer return {reference_number}", reference_type="customer_return",
                reference_id=return_record.id, performed_by_user_id=performed_by_user_id,
            )
            db.add(FinancialTransaction(
                organization_id=organization_id, transaction_type="cogs_return", direction="credit",
                amount=sale_line.unit_cost * quantity, reference_type="customer_return",
                reference_id=return_record.id, description=f"Restored COGS for return {reference_number}", actor_id=performed_by_user_id,
            ))

        if sale_line.device_id is not None:
            device = db.scalar(select(DeviceRecord).where(
                DeviceRecord.id == sale_line.device_id,
                DeviceRecord.organization_id == organization_id,
            ).with_for_update())
            if device is None or device.status != "sold":
                raise ValueError("Serialized device is not in a returnable state")
            device.status = {"RESTOCK": "received", "DAMAGED": "damaged", "DEFECTIVE": "defective", "SERVICE": "service", "WRITE OFF": "written_off"}[disposition]

        return_record.lines.append(
            CustomerReturnLine(
                sale_line_id=sale_line.id,
                quantity=quantity,
                amount=amount,
                reason=reason.strip(),
                condition=condition,
                disposition=disposition,
                original_cost=sale_line.unit_cost * quantity,
                payment_id=db.scalar(select(__import__("app.sales.models", fromlist=["SalePayment"]).SalePayment.id).where(__import__("app.sales.models", fromlist=["SalePayment"]).SalePayment.sale_id == sale.id).limit(1)),
            )
        )

        refund_total += amount

    return_record.refund_amount = refund_total

    db.flush()
    db.add(AuditLog(
        organization_id=organization_id,
        user_id=performed_by_user_id,
        action="customer_return.completed",
        entity_type="customer_return",
        entity_id=return_record.id,
        description=f"Return {return_record.reference_number} completed",
        metadata_json="{}",
    ))
    if refund_total:
        db.add(FinancialTransaction(
            organization_id=organization_id, transaction_type="refund", direction="debit",
            amount=refund_total, reference_type="customer_return", reference_id=return_record.id,
            description=f"Refund for return {return_record.reference_number}", actor_id=performed_by_user_id,
        ))
    db.flush()
    db.refresh(return_record)

    return return_record
