"""expense attribution and traceable finance events"""
from alembic import op
import sqlalchemy as sa

revision = "9c2d4e6f1a30"
down_revision = "8ab3d2f0c911"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, columns in {
        "expenses": [
            sa.Column("expense_date", sa.Date(), nullable=False, server_default=sa.func.current_date()),
            sa.Column("store_id", sa.UUID(), nullable=True),
            sa.Column("payment_account", sa.String(100), nullable=False, server_default=""),
            sa.Column("actor_id", sa.UUID(), nullable=True),
            sa.Column("approved_by_user_id", sa.UUID(), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attachment_reference", sa.String(255), nullable=False, server_default=""),
        ],
        "financial_transactions": [
            sa.Column("actor_id", sa.UUID(), nullable=True),
            sa.Column("store_id", sa.UUID(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        ],
    }.items():
        existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
        for column in columns:
            if column.name not in existing:
                op.add_column(table, column)
    with op.batch_alter_table("expenses") as batch:
        batch.create_foreign_key("fk_expenses_actor_id_users", "users", ["actor_id"], ["id"], ondelete="SET NULL")
        batch.create_foreign_key("fk_expenses_approved_by_user_id_users", "users", ["approved_by_user_id"], ["id"], ondelete="SET NULL")
    with op.batch_alter_table("financial_transactions") as batch:
        batch.create_foreign_key("fk_financial_transactions_actor_id_users", "users", ["actor_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("financial_transactions") as batch:
        batch.drop_constraint("fk_financial_transactions_actor_id_users", type_="foreignkey")
        batch.drop_column("occurred_at")
        batch.drop_column("store_id")
        batch.drop_column("actor_id")
    with op.batch_alter_table("expenses") as batch:
        batch.drop_constraint("fk_expenses_approved_by_user_id_users", type_="foreignkey")
        batch.drop_constraint("fk_expenses_actor_id_users", type_="foreignkey")
        for column in ("attachment_reference", "approved_at", "approved_by_user_id", "actor_id", "payment_account", "store_id", "expense_date"):
            batch.drop_column(column)
