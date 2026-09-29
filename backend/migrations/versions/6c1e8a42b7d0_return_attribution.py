"""attribute return completion and enforce tenant scoped idempotency"""

from alembic import op
import sqlalchemy as sa

revision = "6c1e8a42b7d0"
down_revision = "5c7a1d9e3b42"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("customer_returns")}
    if "performed_by_user_id" not in columns:
        op.add_column(
            "customer_returns",
            sa.Column("performed_by_user_id", sa.UUID(), nullable=True),
        )
        with op.batch_alter_table("customer_returns") as batch:
            batch.create_foreign_key(
                "fk_customer_returns_performed_by_user_id_users",
                "users", ["performed_by_user_id"], ["id"], ondelete="SET NULL",
            )
        op.create_index(
            "ix_customer_returns_performed_by_user_id",
            "customer_returns", ["performed_by_user_id"], unique=False,
        )
    constraints = sa.inspect(op.get_bind()).get_unique_constraints("customer_returns")
    if not any(set(item.get("column_names") or ()) == {"organization_id", "reference_number"} for item in constraints):
        with op.batch_alter_table("customer_returns") as batch:
            batch.create_unique_constraint(
                "uq_customer_returns_org_reference",
                ["organization_id", "reference_number"],
            )


def downgrade() -> None:
    with op.batch_alter_table("customer_returns") as batch:
        batch.drop_constraint("uq_customer_returns_org_reference", type_="unique")
    op.drop_index("ix_customer_returns_performed_by_user_id", table_name="customer_returns")
    with op.batch_alter_table("customer_returns") as batch:
        batch.drop_constraint("fk_customer_returns_performed_by_user_id_users", type_="foreignkey")
    op.drop_column("customer_returns", "performed_by_user_id")
