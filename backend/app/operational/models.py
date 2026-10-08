import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, JSON, String, Table, Column, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


membership_branches = Table(
    "membership_branches",
    Base.metadata,
    Column("membership_id", ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True),
    Column("branch_id", ForeignKey("inventory_locations.id", ondelete="CASCADE"), primary_key=True),
)


class BusinessEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_events"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_business_events_idempotency"),
        Index("ix_business_events_event_type", "event_type"),
        Index("ix_business_events_org_created", "organization_id", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    audit_log_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("audit_logs.id", ondelete="SET NULL"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), nullable=True)


class AutomationRecommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automation_recommendations"
    __table_args__ = (
        UniqueConstraint("organization_id", "dedupe_key", name="uq_automation_recommendations_dedupe"),
        Index("ix_automation_recommendations_organization_id", "organization_id"),
        Index("ix_automation_recommendations_recommendation_type", "recommendation_type"),
        Index("ix_automation_recommendations_status", "status"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str] = mapped_column(String(1000), nullable=False)
    action_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(180), nullable=False)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resulting_entity_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    resulting_entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
