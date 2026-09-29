"""catalog sellable fields and serialized device traceability"""

from alembic import op
import sqlalchemy as sa

revision = "7d9f2a1c4e60"
down_revision = "6c1e8a42b7d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    product_uniques = inspector.get_unique_constraints("products")
    if not any(set(c.get("column_names") or ()) == {"organization_id", "sku"} for c in product_uniques):
        with op.batch_alter_table("products") as batch:
            batch.create_unique_constraint("uq_products_org_sku", ["organization_id", "sku"])

    inspector = sa.inspect(bind)

    def add(table, name, column):
        if name not in {c["name"] for c in sa.inspect(bind).get_columns(table)}:
            op.add_column(table, column)

    add("products", "product_type", sa.Column("product_type", sa.String(40), nullable=False, server_default="other"))
    add("products", "barcode", sa.Column("barcode", sa.String(150), nullable=False, server_default=""))
    add("products", "unit_cost", sa.Column("unit_cost", sa.Numeric(14, 2), nullable=False, server_default="0"))
    add("products", "selling_price", sa.Column("selling_price", sa.Numeric(14, 2), nullable=False, server_default="0"))
    add("products", "reorder_threshold", sa.Column("reorder_threshold", sa.Numeric(14, 3), nullable=False, server_default="0"))
    add("inventory_items", "reorder_threshold", sa.Column("reorder_threshold", sa.Numeric(14, 3), nullable=False, server_default="0"))
    add("inventory_movements", "product_id", sa.Column("product_id", sa.Uuid(), nullable=True))
    add("inventory_movements", "location_id", sa.Column("location_id", sa.Uuid(), nullable=True))
    op.execute(sa.text("UPDATE inventory_movements SET product_id = (SELECT product_id FROM inventory_items WHERE inventory_items.id = inventory_movements.inventory_item_id), location_id = (SELECT location_id FROM inventory_items WHERE inventory_items.id = inventory_movements.inventory_item_id) WHERE product_id IS NULL"))
    add("inventory_locations", "parent_location_id", sa.Column("parent_location_id", sa.Uuid(), nullable=True))
    add("inventory_locations", "location_type", sa.Column("location_type", sa.String(30), nullable=False, server_default="location"))
    for name, column in [
        ("ram", sa.String(50)), ("network_sim", sa.String(100)), ("grade", sa.String(50)),
        ("selling_price", sa.Numeric(14, 2)), ("warranty", sa.String(150)),
        ("location_id", sa.Uuid()),
    ]:
        nullable = name in {"selling_price", "location_id"}
        add("device_records", name, sa.Column(name, column, nullable=nullable, **({} if nullable else {"server_default": ""})))

    inspector = sa.inspect(bind)
    movement_fks = {fk.get("name") for fk in inspector.get_foreign_keys("inventory_movements")}
    if "fk_inventory_movements_product_id_products" not in movement_fks:
        with op.batch_alter_table("inventory_movements") as batch:
            batch.alter_column("product_id", existing_type=sa.Uuid(), nullable=False)
            batch.create_foreign_key("fk_inventory_movements_product_id_products", "products", ["product_id"], ["id"], ondelete="RESTRICT")
            batch.create_foreign_key("fk_inventory_movements_location_id_inventory_locations", "inventory_locations", ["location_id"], ["id"], ondelete="SET NULL")
    for table, name, cols in [
        ("inventory_movements", "ix_inventory_movements_product_id", ["product_id"]),
        ("inventory_movements", "ix_inventory_movements_location_id", ["location_id"]),
    ]:
        if name not in {i["name"] for i in sa.inspect(bind).get_indexes(table)}:
            op.create_index(name, table, cols)

    payment_indexes = {i["name"] for i in sa.inspect(bind).get_indexes("sale_payments")}
    if "uq_sale_payments_sale_reference" not in payment_indexes:
        op.create_index(
            "uq_sale_payments_sale_reference", "sale_payments", ["sale_id", "reference"], unique=True,
            sqlite_where=sa.text("reference != ''"), postgresql_where=sa.text("reference != ''"),
        )

    inspector = sa.inspect(bind)
    indexes = {i["name"] for i in inspector.get_indexes("device_records")}
    for column in ("imei", "imei_2", "serial_number", "barcode"):
        name = f"uq_device_records_org_{column}"
        if name not in indexes:
            op.create_index(name, "device_records", ["organization_id", column], unique=True, sqlite_where=sa.text(f"{column} IS NOT NULL"), postgresql_where=sa.text(f"{column} IS NOT NULL"))

    fks = {fk.get("name") for fk in inspector.get_foreign_keys("device_records")}
    if "fk_device_records_location_id_inventory_locations" not in fks:
        with op.batch_alter_table("device_records") as batch:
            batch.create_foreign_key("fk_device_records_location_id_inventory_locations", "inventory_locations", ["location_id"], ["id"], ondelete="SET NULL")
    fks = {fk.get("name") for fk in sa.inspect(bind).get_foreign_keys("inventory_locations")}
    if "fk_inventory_locations_parent_location_id_inventory_locations" not in fks:
        with op.batch_alter_table("inventory_locations") as batch:
            batch.create_foreign_key("fk_inventory_locations_parent_location_id_inventory_locations", "inventory_locations", ["parent_location_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_index("uq_sale_payments_sale_reference", table_name="sale_payments")
    op.drop_index("ix_inventory_movements_location_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_product_id", table_name="inventory_movements")
    with op.batch_alter_table("inventory_movements") as batch:
        batch.drop_constraint("fk_inventory_movements_location_id_inventory_locations", type_="foreignkey")
        batch.drop_constraint("fk_inventory_movements_product_id_products", type_="foreignkey")
        batch.drop_column("location_id")
        batch.drop_column("product_id")
    for column in ("imei", "imei_2", "serial_number", "barcode"):
        op.drop_index(f"uq_device_records_org_{column}", table_name="device_records")
    with op.batch_alter_table("products") as batch:
        batch.drop_constraint("uq_products_org_sku", type_="unique")
    with op.batch_alter_table("device_records") as batch:
        batch.drop_constraint("fk_device_records_location_id_inventory_locations", type_="foreignkey")
        for column in ("ram", "network_sim", "grade", "selling_price", "warranty", "location_id"):
            batch.drop_column(column)
    with op.batch_alter_table("inventory_locations") as batch:
        batch.drop_constraint("fk_inventory_locations_parent_location_id_inventory_locations", type_="foreignkey")
        batch.drop_column("parent_location_id")
        batch.drop_column("location_type")
    op.drop_column("inventory_items", "reorder_threshold")
    for column in ("product_type", "barcode", "unit_cost", "selling_price", "reorder_threshold"):
        op.drop_column("products", column)
