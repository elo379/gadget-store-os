import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Membership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "memberships"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_membership_organization_user",
        ),
        UniqueConstraint(
            "organization_id",
            "personnel_id",
            name="uq_membership_organization_personnel",
        ),
    )

    organization_id = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_name = mapped_column(
        String(100),
        nullable=False,
        default="member",
    )

    personnel_id = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    parent_membership_id = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by_membership_id = mapped_column(
        ForeignKey("memberships.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    account_status = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )

    invited_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    accepted_at = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_owner = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    organization = relationship(
        "Organization",
        back_populates="memberships",
    )

    user = relationship(
        "User",
        back_populates="memberships",
    )

    parent_membership = relationship(
        "Membership",
        foreign_keys=[parent_membership_id],
        remote_side="Membership.id",
        back_populates="child_memberships",
    )

    child_memberships = relationship(
        "Membership",
        foreign_keys=[parent_membership_id],
        back_populates="parent_membership",
    )

    created_by_membership = relationship(
        "Membership",
        foreign_keys=[created_by_membership_id],
        remote_side="Membership.id",
        back_populates="created_memberships",
    )

    created_memberships = relationship(
        "Membership",
        foreign_keys=[created_by_membership_id],
        back_populates="created_by_membership",
    )
