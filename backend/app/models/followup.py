"""Scheduled sales follow-up model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_FOLLOWUP_REMINDER_MINUTES
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import FollowUpStatus


class FollowUp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A scheduled action for continuing communication with a lead."""

    __tablename__ = "followups"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "leads.id",
            ondelete="CASCADE",
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

    assigned_to_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    followup_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FollowUpStatus.SCHEDULED.value,
        server_default=text(f"'{FollowUpStatus.SCHEDULED.value}'"),
        index=True,
    )

    reminder_minutes_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_FOLLOWUP_REMINDER_MINUTES,
        server_default=text(str(DEFAULT_FOLLOWUP_REMINDER_MINUTES)),
    )

    reminder_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    outcome: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rescheduled_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "followups.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    organization = relationship(
        "Organization",
        lazy="joined",
    )

    lead = relationship(
        "Lead",
        lazy="joined",
    )

    customer = relationship(
        "Customer",
        lazy="joined",
    )

    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_user_id],
        lazy="joined",
    )

    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        lazy="joined",
    )

    rescheduled_from = relationship(
        "FollowUp",
        remote_side="FollowUp.id",
        foreign_keys=[rescheduled_from_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_followups_org_status_scheduled",
            "organization_id",
            "status",
            "scheduled_at",
        ),
        Index(
            "ix_followups_assignee_status_scheduled",
            "assigned_to_user_id",
            "status",
            "scheduled_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<FollowUp id={self.id!s} "
            f"lead_id={self.lead_id!s} "
            f"scheduled_at={self.scheduled_at!s}>"
        )
