"""remove the redundant branch assignment unique constraint"""
from alembic import op
import sqlalchemy as sa

revision = "i5e6f7a8b9c0"
down_revision = "h4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    constraints = {item.get("name") for item in inspector.get_unique_constraints("membership_branches")}
    if "uq_membership_branches_member_branch" in constraints:
        with op.batch_alter_table("membership_branches") as batch:
            batch.drop_constraint("uq_membership_branches_member_branch", type_="unique")


def downgrade() -> None:
    pass
