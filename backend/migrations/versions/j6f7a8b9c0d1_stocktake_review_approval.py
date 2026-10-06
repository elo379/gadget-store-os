"""add attributable stocktake review and approval lifecycle"""
from alembic import op
import sqlalchemy as sa


revision = "j6f7a8b9c0d1"
down_revision = "i5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("stocktakes") as batch:
        batch.add_column(sa.Column("created_by_user_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("submitted_by_user_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("completed_by_user_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_foreign_key("fk_stocktakes_created_by_user_id_users", "users", ["created_by_user_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_stocktakes_submitted_by_user_id_users", "users", ["submitted_by_user_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_stocktakes_completed_by_user_id_users", "users", ["completed_by_user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_stocktakes_created_by_user_id", "stocktakes", ["created_by_user_id"])
    op.create_index("ix_stocktakes_submitted_by_user_id", "stocktakes", ["submitted_by_user_id"])
    op.create_index("ix_stocktakes_completed_by_user_id", "stocktakes", ["completed_by_user_id"])

    with op.batch_alter_table("stocktake_lines") as batch:
        batch.add_column(sa.Column("counted_by_user_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key("fk_stocktake_lines_counted_by_user_id_users", "users", ["counted_by_user_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_stocktake_lines_counted_by_user_id", "stocktake_lines", ["counted_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_stocktake_lines_counted_by_user_id", table_name="stocktake_lines")
    with op.batch_alter_table("stocktake_lines") as batch:
        batch.drop_constraint("fk_stocktake_lines_counted_by_user_id_users", type_="foreignkey")
        batch.drop_column("counted_by_user_id")
    op.drop_index("ix_stocktakes_completed_by_user_id", table_name="stocktakes")
    op.drop_index("ix_stocktakes_submitted_by_user_id", table_name="stocktakes")
    op.drop_index("ix_stocktakes_created_by_user_id", table_name="stocktakes")
    with op.batch_alter_table("stocktakes") as batch:
        batch.drop_constraint("fk_stocktakes_completed_by_user_id_users", type_="foreignkey")
        batch.drop_constraint("fk_stocktakes_submitted_by_user_id_users", type_="foreignkey")
        batch.drop_constraint("fk_stocktakes_created_by_user_id_users", type_="foreignkey")
        batch.drop_column("completed_at")
        batch.drop_column("submitted_at")
        batch.drop_column("completed_by_user_id")
        batch.drop_column("submitted_by_user_id")
        batch.drop_column("created_by_user_id")
