"""Lead model for qualified or potentially valuable customer opportunities."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A sales opportunity associated with a unified customer.

    A customer may contact the organization many times across multiple
    channels while still being represented by a single active lead.
    """

    __tablename__ = "leads"

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

    source_enquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "enquiries.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "products.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "lead_statuses.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
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

    campaign_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ad_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    requirement: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    original_enquiry: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    purchase_intent: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    lead_score: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
    )

    priority_score: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
    )

    followup_risk_score: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        index=True,
    )

    score_breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    qualification_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    conversation_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    next_best_action: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    next_best_action_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    last_contact_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    next_followup_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    organization = relationship(
        "Organization",
        lazy="joined",
    )

    customer = relationship(
        "Customer",
        lazy="joined",
    )

    product = relationship(
        "Product",
        lazy="joined",
    )

    status = relationship(
        "LeadStatus",
        lazy="joined",
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        lazy="joined",
    )

    source_enquiry = relationship(
        "Enquiry",
        foreign_keys=[source_enquiry_id],
        lazy="joined",
    )

    __table_args__ = (
        CheckConstraint(
            "lead_score IS NULL OR (lead_score >= 0 AND lead_score <= 100)",
            name="lead_score_range",
        ),
        CheckConstraint(
            "priority_score IS NULL OR "
            "(priority_score >= 0 AND priority_score <= 100)",
            name="priority_score_range",
        ),
        CheckConstraint(
            "followup_risk_score IS NULL OR "
            "(followup_risk_score >= 0 AND followup_risk_score <= 100)",
            name="followup_risk_score_range",
        ),
        Index(
            "ix_leads_org_status",
            "organization_id",
            "status_id",
        ),
        Index(
            "ix_leads_org_assignee",
            "organization_id",
            "assigned_to_user_id",
        ),
        Index(
            "ix_leads_org_next_followup",
            "organization_id",
            "next_followup_at",
        ),
        Index(
            "ix_leads_org_priority",
            "organization_id",
            "priority_score",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Lead id={self.id!s} "
            f"customer_id={self.customer_id!s} "
            f"score={self.lead_score!r}>"
        )
