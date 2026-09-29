"""create customer return tables

Revision ID: 5c7a1d9e3b42
Revises: 5b2c7e19a4d1
"""

from alembic import op
import sqlalchemy as sa


revision = "5c7a1d9e3b42"
down_revision = "5b2c7e19a4d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("customer_returns"):
        op.create_table(
            "customer_returns",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("organization_id", sa.UUID(), nullable=False),
            sa.Column("sale_id", sa.UUID(), nullable=False),
            sa.Column("customer_id", sa.UUID(), nullable=True),
            sa.Column("reference_number", sa.String(100), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column(
                "refund_amount",
                sa.Numeric(14, 2),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "status",
                sa.String(50),
                nullable=False,
                server_default="completed",
            ),
            sa.Column("performed_by_user_id", sa.UUID(), nullable=True),
            sa.Column("seller_user_id", sa.UUID(), nullable=True),
            sa.ForeignKeyConstraint(
                ["organization_id"],
                ["organizations.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["sale_id"],
                ["sales.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["customer_id"],
                ["customers.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["performed_by_user_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["seller_user_id"],
                ["users.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "organization_id",
                "reference_number",
                name="uq_customer_returns_org_reference",
            ),
        )

    indexes = {
        idx["name"]
        for idx in sa.inspect(bind).get_indexes("customer_returns")
    }

    for name, columns in (
        (
            "ix_customer_returns_organization_id",
            ["organization_id"],
        ),
        ("ix_customer_returns_sale_id", ["sale_id"]),
        ("ix_customer_returns_customer_id", ["customer_id"]),
        ("ix_customer_returns_reference_number", ["reference_number"]),
        ("ix_customer_returns_status", ["status"]),
        (
            "ix_customer_returns_performed_by_user_id",
            ["performed_by_user_id"],
        ),
    ):
        if name not in indexes:
            op.create_index(name, "customer_returns", columns)


    if not inspector.has_table("customer_return_lines"):
        op.create_table(
            "customer_return_lines",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("return_id", sa.UUID(), nullable=False),
            sa.Column("sale_line_id", sa.UUID(), nullable=False),
            sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column(
                "condition",
                sa.String(40),
                nullable=False,
                server_default="unknown",
            ),
            sa.Column(
                "disposition",
                sa.String(40),
                nullable=False,
                server_default="RESTOCK",
            ),
            sa.Column(
                "original_cost",
                sa.Numeric(14, 2),
                nullable=False,
                server_default="0",
            ),
            sa.Column("payment_id", sa.UUID(), nullable=True),
            sa.ForeignKeyConstraint(
                ["return_id"],
                ["customer_returns.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["sale_line_id"],
                ["sale_lines.id"],
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["payment_id"],
                ["sale_payments.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = {
        idx["name"]
        for idx in sa.inspect(bind).get_indexes("customer_return_lines")
    }

    for name, columns in (
        ("ix_customer_return_lines_return_id", ["return_id"]),
        ("ix_customer_return_lines_sale_line_id", ["sale_line_id"]),
    ):
        if name not in indexes:
            op.create_index(name, "customer_return_lines", columns)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("customer_return_lines"):
        op.drop_index(
            "ix_customer_return_lines_sale_line_id",
            table_name="customer_return_lines",
        )
        op.drop_index(
            "ix_customer_return_lines_return_id",
            table_name="customer_return_lines",
        )
        op.drop_table("customer_return_lines")

    if inspector.has_table("customer_returns"):
        for name in (
            "ix_customer_returns_performed_by_user_id",
            "ix_customer_returns_status",
            "ix_customer_returns_reference_number",
            "ix_customer_returns_customer_id",
            "ix_customer_returns_sale_id",
            "ix_customer_returns_organization_id",
        ):
            indexes = {
                idx["name"]
                for idx in sa.inspect(bind).get_indexes("customer_returns")
            }
            if name in indexes:
                op.drop_index(name, table_name="customer_returns")

        op.drop_table("customer_returns")
