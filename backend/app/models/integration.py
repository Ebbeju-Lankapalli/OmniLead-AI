"""External integration configuration model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Integration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Organization-level external service configuration.

    Sensitive secrets are not intended to be stored directly in the JSON
    configuration column.
    """

    __tablename__ = "integrations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_account_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="DISCONNECTED",
        server_default=text("'DISCONNECTED'"),
        index=True,
    )

    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
    )

    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    organization = relationship("Organization", lazy="joined")

    __table_args__ = (
        Index(
            "uq_integrations_org_provider_external_account",
            "organization_id",
            "provider",
            "external_account_id",
            unique=True,
            postgresql_where=text(
                "external_account_id IS NOT NULL"
            ),
        ),
        Index(
            "ix_integrations_org_provider_status",
            "organization_id",
            "provider",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Integration id={self.id!s} "
            f"provider={self.provider!r} "
            f"status={self.status!r}>"
        )
