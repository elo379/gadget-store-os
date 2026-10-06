"""align PostgreSQL schema with inventory, device and expense models"""

from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "b4d9c2a71e63"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    sqlite = bind.dialect.name == "sqlite"

    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("device_records")}
    if "ix_device_records_location_id" not in indexes:
        op.create_index("ix_device_records_location_id", "device_records", ["location_id"])

    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("expenses")}
    if "ix_expenses_actor_id" not in indexes:
        op.create_index("ix_expenses_actor_id", "expenses", ["actor_id"])

    constraints = sa.inspect(bind).get_unique_constraints("inventory_items")
    if not any(set(item.get("column_names") or ()) == {"organization_id", "product_id", "location_id"} for item in constraints):
        if sqlite:
            with op.batch_alter_table("inventory_items", recreate="always") as batch:
                batch.create_unique_constraint("uq_inventory_org_product_location", ["organization_id", "product_id", "location_id"])
        else:
            op.create_unique_constraint("uq_inventory_org_product_location", "inventory_items", ["organization_id", "product_id", "location_id"])

    constraints = sa.inspect(bind).get_unique_constraints("inventory_locations")
    if not any(set(item.get("column_names") or ()) == {"organization_id", "name"} for item in constraints):
        if sqlite:
            with op.batch_alter_table("inventory_locations", recreate="always") as batch:
                batch.create_unique_constraint("uq_inventory_locations_org_name", ["organization_id", "name"])
        else:
            op.create_unique_constraint("uq_inventory_locations_org_name", "inventory_locations", ["organization_id", "name"])

    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("inventory_items")}
    if "uq_inventory_org_product_unlocated" not in indexes:
        op.create_index(
            "uq_inventory_org_product_unlocated", "inventory_items",
            ["organization_id", "product_id"], unique=True,
            sqlite_where=sa.text("location_id IS NULL"),
            postgresql_where=sa.text("location_id IS NULL"),
        )


def downgrade() -> None:
    op.drop_index("uq_inventory_org_product_unlocated", table_name="inventory_items")
    op.drop_constraint("uq_inventory_locations_org_name", "inventory_locations", type_="unique")
    op.drop_constraint("uq_inventory_org_product_location", "inventory_items", type_="unique")
    op.drop_index("ix_expenses_actor_id", table_name="expenses")
    op.drop_index("ix_device_records_location_id", table_name="device_records")
