"""track partial purchase receipts and enforce sale idempotency"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "4a9f35d2c861"
down_revision: Union[str, Sequence[str], None] = "768f8f0e5a1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    inspector = sa.inspect(op.get_bind())
    if "received_quantity" not in {c["name"] for c in inspector.get_columns("purchase_lines")}:
        op.add_column(
            "purchase_lines",
            sa.Column("received_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        )
    if "payment_status" not in {c["name"] for c in inspector.get_columns("sales")}:
        op.add_column(
            "sales", sa.Column("payment_status", sa.String(length=30), nullable=False, server_default="unpaid")
        )

    inspector = sa.inspect(op.get_bind())
    indexes = {idx["name"] for idx in inspector.get_indexes("sales")}
    if "ix_sales_payment_status" not in indexes:
        op.create_index("ix_sales_payment_status", "sales", ["payment_status"], unique=False)

    constraints = inspector.get_unique_constraints("sales")
    if not any(set(c.get("column_names") or ()) == {"organization_id", "reference_number"} for c in constraints):
        if is_sqlite:
            with op.batch_alter_table("sales", recreate="always") as batch:
                batch.create_unique_constraint("uq_sales_org_reference", ["organization_id", "reference_number"])
        else:
            op.create_unique_constraint("uq_sales_org_reference", "sales", ["organization_id", "reference_number"])

    # Do not rewrite existing customer values; a legacy orphan should stop the
    # migration for explicit repair instead of silently discarding data.
    foreign_keys = sa.inspect(op.get_bind()).get_foreign_keys("sales")
    old_fk = next((fk for fk in foreign_keys if fk.get("constrained_columns") == ["customer_id"]), None)
    target_customer_fk = any(
        fk.get("constrained_columns") == ["customer_id"] and fk.get("referred_table") == "customers"
        for fk in foreign_keys
    )
    if not target_customer_fk:
        if is_sqlite:
            with op.batch_alter_table("sales", recreate="always") as batch:
                if old_fk and old_fk.get("name"):
                    batch.drop_constraint(old_fk["name"], type_="foreignkey")
                batch.create_foreign_key(
                    "fk_sales_customer_id_customers", "customers",
                    ["customer_id"], ["id"], ondelete="SET NULL",
                )
        else:
            if old_fk and old_fk.get("name"):
                op.drop_constraint(old_fk["name"], "sales", type_="foreignkey")
            op.create_foreign_key(
                "fk_sales_customer_id_customers", "sales", "customers",
                ["customer_id"], ["id"], ondelete="SET NULL",
            )


def downgrade() -> None:
    op.drop_constraint("fk_sales_customer_id_customers", "sales", type_="foreignkey")
    op.create_foreign_key(
        "fk_sales_customer_id_users", "sales", "users",
        ["customer_id"], ["id"], ondelete="SET NULL",
    )
    op.drop_constraint("uq_sales_org_reference", "sales", type_="unique")
    op.drop_index("ix_sales_payment_status", table_name="sales")
    op.drop_column("sales", "payment_status")
    op.drop_column("purchase_lines", "received_quantity")
