import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PasskeyCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "passkey_credentials"
    __table_args__ = (UniqueConstraint("credential_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credential_id: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )
    public_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sign_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="This device",
    )
    transports: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )


class PasskeyChallenge(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "passkey_challenges"
    __table_args__ = (UniqueConstraint("challenge"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    challenge: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )
    ceremony: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    consumed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
