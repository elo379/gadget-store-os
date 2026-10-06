"""allow serialized product templates without quantity SKU"""

from alembic import op
import sqlalchemy as sa


revision = "d7e8f9a0b1c2"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "sku",
            existing_type=sa.String(length=100),
            nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM products WHERE sku IS NULL LIMIT 1")).first():
        raise RuntimeError("Cannot restore required SKU while serialized products without SKU exist")
    with op.batch_alter_table("products") as batch:
        batch.alter_column(
            "sku",
            existing_type=sa.String(length=100),
            nullable=False,
        )
