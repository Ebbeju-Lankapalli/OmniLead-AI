"""Durable inbound webhook event model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class WebhookEvent(UUIDPrimaryKeyMixin, Base):
    """A persisted external webhook event for idempotency and retries."""

    __tablename__ = "webhook_events"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    integration_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    external_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    signature_valid: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RECEIVED",
        server_default=text("'RECEIVED'"),
        index=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    organization = relationship("Organization", lazy="joined")
    integration = relationship("Integration", lazy="joined")

    __table_args__ = (
        Index(
            "ix_webhook_events_org_status_received",
            "organization_id",
            "status",
            "received_at",
        ),
        Index(
            "uq_webhook_events_provider_external_event",
            "provider",
            "external_event_id",
            unique=True,
            postgresql_where=text(
                "external_event_id IS NOT NULL"
            ),
        ),
        Index(
            "ix_webhook_events_provider_payload_hash",
            "provider",
            "payload_hash",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent id={self.id!s} "
            f"provider={self.provider!r} "
            f"status={self.status!r}>"
        )
