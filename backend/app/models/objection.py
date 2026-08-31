"""Sales objection model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Objection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A detected or manually recorded customer sales objection."""

    __tablename__ = "objections"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    objection_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    detected_by_ai: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        index=True,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    confirmed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DETECTED",
        server_default=text("'DETECTED'"),
        index=True,
    )

    organization = relationship("Organization", lazy="joined")
    lead = relationship("Lead", lazy="joined")
    interaction = relationship("Interaction", lazy="joined")

    confirmed_by = relationship(
        "User",
        foreign_keys=[confirmed_by_user_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_objections_org_type_status",
            "organization_id",
            "objection_type",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Objection id={self.id!s} "
            f"type={self.objection_type!r} "
            f"status={self.status!r}>"
        )
