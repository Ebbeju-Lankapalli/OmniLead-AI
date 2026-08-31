"""Incoming enquiry model for OmniLead AI."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import EnquiryStatus


class Enquiry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A raw customer enquiry received from any supported channel.

    Enquiries are stored before AI analysis so incoming customer information
    is never lost if an external AI service is unavailable.
    """

    __tablename__ = "enquiries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "customers.id",
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
            use_alter=True,
            name="fk_enquiries_conversation_id_conversations",
        ),
        nullable=True,
        index=True,
    )

    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "interactions.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_enquiries_interaction_id_interactions",
        ),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    original_source: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    external_reference_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_name_raw: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contact_raw: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    message_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=EnquiryStatus.NEW.value,
        server_default=text(f"'{EnquiryStatus.NEW.value}'"),
        index=True,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now().astimezone(),
        server_default=func.now(),
        index=True,
    )

    campaign_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ad_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ad_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    enquiry_metadata: Mapped[dict[str, Any]] = mapped_column(
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

    __table_args__ = (
        Index(
            "ix_enquiries_org_status_received",
            "organization_id",
            "status",
            "received_at",
        ),
        Index(
            "ix_enquiries_org_source_received",
            "organization_id",
            "source",
            "received_at",
        ),
        Index(
            "uq_enquiries_org_source_external_reference",
            "organization_id",
            "source",
            "external_reference_id",
            unique=True,
            postgresql_where=text("external_reference_id IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Enquiry id={self.id!s} "
            f"source={self.source!r} "
            f"status={self.status!r}>"
        )
