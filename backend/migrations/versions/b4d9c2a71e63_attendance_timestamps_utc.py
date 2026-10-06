"""store attendance instants as timezone-aware UTC timestamps

Revision ID: b4d9c2a71e63
Revises: a7e4c91d2f60
"""

from alembic import op
import sqlalchemy as sa


revision = "b4d9c2a71e63"
down_revision = "a7e4c91d2f60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Historical attendance values were written as UTC wall time into naive
    # columns. Interpret them as UTC while converting PostgreSQL columns.
    if op.get_bind().dialect.name == "postgresql":
        op.alter_column(
            "attendance_records",
            "clock_in",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="clock_in AT TIME ZONE 'UTC'",
        )
        op.alter_column(
            "attendance_records",
            "clock_out",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using="clock_out AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.alter_column(
            "attendance_records",
            "clock_out",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(timezone=False),
            existing_nullable=True,
            postgresql_using="clock_out AT TIME ZONE 'UTC'",
        )
        op.alter_column(
            "attendance_records",
            "clock_in",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(timezone=False),
            existing_nullable=False,
            postgresql_using="clock_in AT TIME ZONE 'UTC'",
        )
