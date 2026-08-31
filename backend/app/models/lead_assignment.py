"""Lead assignment history model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class LeadAssignment(UUIDPrimaryKeyMixin, Base):
    """Historical record of lead ownership and reassignment."""

    __tablename__ = "lead_assignments"

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

    assigned_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    lead = relationship(
        "Lead",
        lazy="joined",
    )

    assigned_from = relationship(
        "User",
        foreign_keys=[assigned_from_id],
        lazy="joined",
    )

    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        lazy="joined",
    )

    assigned_by = relationship(
        "User",
        foreign_keys=[assigned_by_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_lead_assignments_lead_assigned_at",
            "lead_id",
            "assigned_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LeadAssignment id={self.id!s} "
            f"lead_id={self.lead_id!s} "
            f"assigned_to={self.assigned_to_id!s}>"
        )
