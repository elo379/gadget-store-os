"""persist sale branch and branch assignments"""
from alembic import op
import sqlalchemy as sa

revision = "h4d5e6f7a8b9"
down_revision = "g3c4d5e6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sales") as batch:
        batch.add_column(sa.Column("branch_id", sa.Uuid(), nullable=True))
        batch.create_index("ix_sales_branch_id", ["branch_id"])
        batch.create_foreign_key("fk_sales_branch_id_inventory_locations", "inventory_locations", ["branch_id"], ["id"], ondelete="SET NULL")
    op.create_table("membership_branches",
        sa.Column("membership_id", sa.Uuid(), sa.ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("branch_id", sa.Uuid(), sa.ForeignKey("inventory_locations.id", ondelete="CASCADE"), primary_key=True))


def downgrade() -> None:
    op.drop_table("membership_branches")
    with op.batch_alter_table("sales") as batch:
        batch.drop_constraint("fk_sales_branch_id_inventory_locations", type_="foreignkey")
        batch.drop_index("ix_sales_branch_id")
        batch.drop_column("branch_id")
