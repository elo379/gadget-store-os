"""capture configured supplier lead time for replenishment planning"""

from alembic import op
import sqlalchemy as sa

revision = "g3c4d5e6a7b8"
down_revision = "f2b3c4d5e6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("lead_time_days", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("suppliers", "lead_time_days")
