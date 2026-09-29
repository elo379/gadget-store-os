"""add authentication sessions and organization workflows

Revision ID: 768f8f0e5a1d
Revises: ffd20b9bc632
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "768f8f0e5a1d"
down_revision: Union[str, Sequence[str], None] = "ffd20b9bc632"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_if_missing(name: str, *items) -> None:
    if not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *items)


def upgrade() -> None:
    # This revision was previously generated from a live schema and contained
    # duplicate columns, UUID affinity rewrites, and destructive return-table
    # drops. Keep it additive and safe when a database was initialized with
    # metadata.create_all before migrations were introduced.
    _create_if_missing(
        "sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    _create_if_missing(
        "passkey_credentials",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("credential_id", sa.Text(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("name", sa.String(120), nullable=False, server_default="This device"),
        sa.Column("transports", sa.Text(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credential_id"),
    )
    _create_if_missing(
        "passkey_challenges",
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("challenge", sa.Text(), nullable=False),
        sa.Column("ceremony", sa.String(30), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("challenge"),
    )
    _create_if_missing(
        "store_tree_policies",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("managers_can_create_staff", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("managers_can_create_managers", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("managers_can_assign_roles", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("managers_can_modify_permissions", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    _create_if_missing(
        "personnel_invitations",
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role_name", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("parent_membership_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_membership_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_membership_id"], ["memberships.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_membership_id"], ["memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )


    inspector = sa.inspect(op.get_bind())
    for table, columns in {
        "sessions": ("user_id", "refresh_token_hash", "expires_at"),
        "passkey_credentials": ("user_id", "credential_id"),
        "passkey_challenges": ("user_id", "challenge", "expires_at"),
        "store_tree_policies": ("organization_id",),
        "personnel_invitations": ("email", "organization_id", "token_hash"),
    }.items():
        existing = {index["name"] for index in inspector.get_indexes(table)}
        for column in columns:
            name = f"ix_{table}_{column}"
            if name not in existing:
                # Uniqueness is enforced by the table constraints above; these
                # secondary indexes only support lookups.
                op.create_index(name, table, [column], unique=False)


def downgrade() -> None:
    # Keep workflow data and authentication records when rolling back code.
    # Destructive table removal is intentionally avoided.
    pass
