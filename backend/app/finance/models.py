import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class FinancialTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_transactions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False
    )
    reference_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=""
    )
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )

    organization = relationship("Organization")
