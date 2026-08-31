"""Unified omnichannel conversation model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A communication thread between the organization and a customer.

    Separate channel threads remain connected to the same unified customer
    and may optionally be associated with a lead.
    """

    __tablename__ = "conversations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "leads.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    external_conversation_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    conversation_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    organization = relationship(
        "Organization",
        lazy="joined",
    )

    customer = relationship(
        "Customer",
        lazy="joined",
    )

    lead = relationship(
        "Lead",
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_conversations_org_customer_channel",
            "organization_id",
            "customer_id",
            "channel",
        ),
        Index(
            "uq_conversations_org_channel_external",
            "organization_id",
            "channel",
            "external_conversation_id",
            unique=True,
            postgresql_where=text(
                "external_conversation_id IS NOT NULL"
            ),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation id={self.id!s} "
            f"channel={self.channel!r} "
            f"customer_id={self.customer_id!s}>"
        )
