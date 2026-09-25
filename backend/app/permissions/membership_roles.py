import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MembershipRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "membership_roles"

    __table_args__ = (
        UniqueConstraint(
            "membership_id",
            "role_id",
            name="uq_membership_role",
        ),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    membership = relationship("Membership")
    role = relationship("Role")
