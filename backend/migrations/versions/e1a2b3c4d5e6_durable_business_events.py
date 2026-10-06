"""add organization-scoped durable business events"""

from alembic import op
import sqlalchemy as sa

revision = "e1a2b3c4d5e6"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_events",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("branch_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("audit_log_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["audit_log_id"], ["audit_logs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "idempotency_key", name="uq_business_events_idempotency"),
    )
    op.create_index("ix_business_events_event_type", "business_events", ["event_type"])
    op.create_index("ix_business_events_org_created", "business_events", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_business_events_org_created", table_name="business_events")
    op.drop_index("ix_business_events_event_type", table_name="business_events")
    op.drop_table("business_events")
