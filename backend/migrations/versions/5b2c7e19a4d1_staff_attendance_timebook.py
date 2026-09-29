"""complete staff shift and attendance timebook fields"""

from alembic import op
import sqlalchemy as sa

revision = "5b2c7e19a4d1"
down_revision = "4a9f35d2c861"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table, column in (
        ("staff_profiles", sa.Column("shift_start", sa.Time(), nullable=False, server_default="09:00:00")),
        ("staff_profiles", sa.Column("shift_end", sa.Time(), nullable=False, server_default="17:00:00")),
        ("staff_profiles", sa.Column("grace_minutes", sa.Integer(), nullable=False, server_default="0")),
        ("attendance_records", sa.Column("work_date", sa.Date(), nullable=True)),
        ("attendance_records", sa.Column("late_minutes", sa.Integer(), nullable=False, server_default="0")),
        ("attendance_records", sa.Column("early_departure_minutes", sa.Integer(), nullable=False, server_default="0")),
    ):
        if column.name not in {c["name"] for c in inspector.get_columns(table)}:
            op.add_column(table, column)
    if op.get_bind().dialect.name == "sqlite":
        op.execute("UPDATE attendance_records SET work_date = date(clock_in) WHERE work_date IS NULL")
    else:
        op.execute("UPDATE attendance_records SET work_date = CAST(clock_in AS DATE) WHERE work_date IS NULL")
    with op.batch_alter_table("attendance_records") as batch:
        batch.alter_column("work_date", nullable=False, existing_type=sa.Date())
    indexes = {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes("attendance_records")}
    if "uq_attendance_one_open_per_staff" not in indexes:
        op.create_index("uq_attendance_one_open_per_staff", "attendance_records", ["organization_id", "staff_id"], unique=True, postgresql_where=sa.text("status = 'open'"), sqlite_where=sa.text("status = 'open'"))
    if not sa.inspect(op.get_bind()).has_table("staff_absences"):
        op.create_table(
        "staff_absences",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("staff_id", sa.UUID(), nullable=False),
        sa.Column("absence_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("created_by_user_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "staff_id", "absence_date", name="uq_staff_absence_org_staff_date"),
    )
    absence_indexes = {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes("staff_absences")}
    if "ix_staff_absences_organization_id" not in absence_indexes:
        op.create_index("ix_staff_absences_organization_id", "staff_absences", ["organization_id"])
    if "ix_staff_absences_staff_id" not in absence_indexes:
        op.create_index("ix_staff_absences_staff_id", "staff_absences", ["staff_id"])


def downgrade() -> None:
    op.drop_index("ix_staff_absences_staff_id", table_name="staff_absences")
    op.drop_index("ix_staff_absences_organization_id", table_name="staff_absences")
    op.drop_table("staff_absences")
    op.drop_index("uq_attendance_one_open_per_staff", table_name="attendance_records")
    op.drop_column("attendance_records", "early_departure_minutes")
    op.drop_column("attendance_records", "late_minutes")
    op.drop_column("attendance_records", "work_date")
    op.drop_column("staff_profiles", "grace_minutes")
    op.drop_column("staff_profiles", "shift_end")
    op.drop_column("staff_profiles", "shift_start")
