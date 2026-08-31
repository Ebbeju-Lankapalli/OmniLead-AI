"""Individual customer communication and activity model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


EMBEDDING_DIMENSION = 384
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Interaction(UUIDPrimaryKeyMixin, Base):
    """
    An individual message, call, note, or workflow activity.

    Interactions form the chronological communication timeline and may carry
    embeddings for semantic retrieval.
    """

    __tablename__ = "interactions"

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

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    interaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    direction: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    external_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSION),
        nullable=True,
    )

    embedding_model: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    interaction_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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

    conversation = relationship(
        "Conversation",
        lazy="joined",
    )

    actor = relationship(
        "User",
        foreign_keys=[actor_user_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_interactions_conversation_occurred",
            "conversation_id",
            "occurred_at",
        ),
        Index(
            "ix_interactions_lead_occurred",
            "lead_id",
            "occurred_at",
        ),
        Index(
            "ix_interactions_customer_occurred",
            "customer_id",
            "occurred_at",
        ),
        Index(
            "uq_interactions_org_channel_external_message",
            "organization_id",
            "channel",
            "external_message_id",
            unique=True,
            postgresql_where=text(
                "external_message_id IS NOT NULL"
            ),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Interaction id={self.id!s} "
            f"type={self.interaction_type!r} "
            f"channel={self.channel!r}>"
        )
