"""reconcile financial and operational indexes

Revision ID: a7e4c91d2f60
Revises: 9c2d4e6f1a30
"""

from alembic import op
import sqlalchemy as sa


revision = "a7e4c91d2f60"
down_revision = "9c2d4e6f1a30"
branch_labels = None
depends_on = None


def _indexes(table):
    return {x["name"] for x in sa.inspect(op.get_bind()).get_indexes(table)}


def _add(name, table, columns):
    if name not in _indexes(table):
        op.create_index(name, table, columns)


def upgrade():
    _add("ix_expenses_expense_date", "expenses", ["expense_date"])
    _add("ix_expenses_store_id", "expenses", ["store_id"])

    _add(
        "ix_financial_transactions_actor_id",
        "financial_transactions",
        ["actor_id"],
    )
    _add(
        "ix_financial_transactions_occurred_at",
        "financial_transactions",
        ["occurred_at"],
    )
    _add(
        "ix_financial_transactions_store_id",
        "financial_transactions",
        ["store_id"],
    )

    _add(
        "ix_inventory_locations_parent_location_id",
        "inventory_locations",
        ["parent_location_id"],
    )


def downgrade():
    bind = op.get_bind()

    for name, table in (
        ("ix_inventory_locations_parent_location_id", "inventory_locations"),
        ("ix_financial_transactions_store_id", "financial_transactions"),
        ("ix_financial_transactions_occurred_at", "financial_transactions"),
        ("ix_financial_transactions_actor_id", "financial_transactions"),
        ("ix_expenses_store_id", "expenses"),
        ("ix_expenses_expense_date", "expenses"),
    ):
        if name in {x["name"] for x in sa.inspect(bind).get_indexes(table)}:
            op.drop_index(name, table_name=table)
