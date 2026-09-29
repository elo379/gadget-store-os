"""atomic checkout totals and warranty/repair lifecycle"""
from alembic import op
import sqlalchemy as sa

revision = "8ab3d2f0c911"
down_revision = "7d9f2a1c4e60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = {c["name"] for c in inspector.get_columns("sales")}
    if "tax" not in existing:
        op.add_column("sales", sa.Column("tax", sa.Numeric(14, 2), nullable=False, server_default="0"))
    if "fees" not in existing:
        op.add_column("sales", sa.Column("fees", sa.Numeric(14, 2), nullable=False, server_default="0"))
    return_columns = {c["name"] for c in inspector.get_columns("customer_returns")}
    if "seller_user_id" not in return_columns:
        op.add_column("customer_returns", sa.Column("seller_user_id", sa.UUID(), nullable=True))
        with op.batch_alter_table("customer_returns") as batch:
            batch.create_foreign_key("fk_customer_returns_seller_user_id_users", "users", ["seller_user_id"], ["id"], ondelete="SET NULL")
    line_columns = {c["name"] for c in inspector.get_columns("customer_return_lines")}
    for name, column in (
        ("condition", sa.Column("condition", sa.String(40), nullable=False, server_default="unknown")),
        ("disposition", sa.Column("disposition", sa.String(40), nullable=False, server_default="RESTOCK")),
        ("original_cost", sa.Column("original_cost", sa.Numeric(14, 2), nullable=False, server_default="0")),
        ("payment_id", sa.Column("payment_id", sa.UUID(), nullable=True)),
    ):
        if name not in line_columns:
            op.add_column("customer_return_lines", column)
    if "payment_id" not in line_columns:
        with op.batch_alter_table("customer_return_lines") as batch:
            batch.create_foreign_key("fk_customer_return_lines_payment_id_sale_payments", "sale_payments", ["payment_id"], ["id"], ondelete="SET NULL")
    op.create_table(
        "warranties",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.UUID(), sa.ForeignKey("device_records.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="SET NULL")),
        sa.Column("sale_id", sa.UUID(), sa.ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("starts_at", sa.Date(), nullable=False), sa.Column("ends_at", sa.Date(), nullable=False),
        sa.Column("coverage", sa.String(200), nullable=False, server_default="manufacturer"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("claims", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_warranties_organization_id", "warranties", ["organization_id"])
    op.create_index("ix_warranties_device_id", "warranties", ["device_id"])
    op.create_index("ix_warranties_customer_id", "warranties", ["customer_id"])
    op.create_index("ix_warranties_sale_id", "warranties", ["sale_id"])
    op.create_index("ix_warranties_status", "warranties", ["status"])
    op.create_table(
        "repair_cases",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("organization_id", sa.UUID(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.UUID(), sa.ForeignKey("device_records.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("customer_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reference_number", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="intake"),
        sa.Column("diagnosis", sa.Text(), nullable=False, server_default=""),
        sa.Column("parts", sa.Text(), nullable=False, server_default=""),
        sa.Column("labour", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("customer_charge", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column("repair_cases", sa.Column("assigned_to_user_id", sa.UUID(), nullable=True))
    with op.batch_alter_table("repair_cases") as batch:
        batch.create_foreign_key("fk_repair_cases_assigned_to_user_id_users", "users", ["assigned_to_user_id"], ["id"], ondelete="SET NULL")
    for col in ("organization_id", "device_id", "customer_id", "status"):
        op.create_index(f"ix_repair_cases_{col}", "repair_cases", [col])
    op.create_table(
        "repair_status_history",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("repair_id", sa.UUID(), sa.ForeignKey("repair_cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False, server_default=""),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("changed_by_user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_repair_status_history_repair_id", "repair_status_history", ["repair_id"])


def downgrade() -> None:
    op.drop_table("repair_status_history")
    op.drop_table("repair_cases")
    op.drop_table("warranties")
    op.drop_column("customer_return_lines", "payment_id")
    op.drop_column("customer_return_lines", "original_cost")
    op.drop_column("customer_return_lines", "disposition")
    op.drop_column("customer_return_lines", "condition")
    op.drop_column("customer_returns", "seller_user_id")
    op.drop_column("sales", "fees")
    op.drop_column("sales", "tax")
