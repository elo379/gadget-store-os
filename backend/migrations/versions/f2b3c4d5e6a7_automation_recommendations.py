"""add durable automation recommendations and approvals"""

from alembic import op
import sqlalchemy as sa

revision = "f2b3c4d5e6a7"
down_revision = "e1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "automation_recommendations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_type", sa.String(60), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=False),
        sa.Column("dedupe_key", sa.String(180), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("resulting_entity_type", sa.String(60), nullable=True),
        sa.Column("resulting_entity_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "dedupe_key", name="uq_automation_recommendations_dedupe"),
    )
    op.create_index("ix_automation_recommendations_organization_id", "automation_recommendations", ["organization_id"])
    op.create_index("ix_automation_recommendations_recommendation_type", "automation_recommendations", ["recommendation_type"])
    op.create_index("ix_automation_recommendations_status", "automation_recommendations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_automation_recommendations_status", table_name="automation_recommendations")
    op.drop_index("ix_automation_recommendations_recommendation_type", table_name="automation_recommendations")
    op.drop_index("ix_automation_recommendations_organization_id", table_name="automation_recommendations")
    op.drop_table("automation_recommendations")
