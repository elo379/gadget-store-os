import uuid

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class StoreTreePolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "store_tree_policies"
    __table_args__ = (UniqueConstraint("organization_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    managers_can_create_staff: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    managers_can_create_managers: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    managers_can_assign_roles: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    managers_can_modify_permissions: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    organization = relationship("Organization")


def get_or_create_store_tree_policy(
    db,
    organization_id: uuid.UUID,
) -> StoreTreePolicy:
    from sqlalchemy import select

    policy = db.scalar(
        select(StoreTreePolicy).where(
            StoreTreePolicy.organization_id == organization_id
        )
    )

    if policy is not None:
        return policy

    policy = StoreTreePolicy(
        organization_id=organization_id,
        managers_can_create_staff=False,
        managers_can_create_managers=False,
        managers_can_assign_roles=False,
        managers_can_modify_permissions=False,
    )

    db.add(policy)
    db.flush()

    return policy
