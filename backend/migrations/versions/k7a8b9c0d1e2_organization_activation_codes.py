"""Add one-time organization activation licenses."""
from alembic import op
import sqlalchemy as sa


revision = "k7a8b9c0d1e2"
down_revision = "j6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activation_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code_digest", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("organization_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_digest"),
        sa.UniqueConstraint("organization_id"),
        sa.CheckConstraint("status IN ('issued', 'redeemed', 'revoked', 'expired')", name="activation_code_status"),
    )
    op.create_index("ix_activation_codes_code_digest", "activation_codes", ["code_digest"])
    op.create_table(
        "activation_attempts",
        sa.Column("address_digest", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("address_digest"),
    )
    op.create_index("ix_activation_attempts_window_started_at", "activation_attempts", ["window_started_at"])


def downgrade() -> None:
    op.drop_index("ix_activation_attempts_window_started_at", table_name="activation_attempts")
    op.drop_table("activation_attempts")
    op.drop_index("ix_activation_codes_code_digest", table_name="activation_codes")
    op.drop_table("activation_codes")
