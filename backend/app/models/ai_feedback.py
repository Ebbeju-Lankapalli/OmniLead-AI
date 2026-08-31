"""Human-in-the-loop feedback model for AI decisions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class AIFeedback(UUIDPrimaryKeyMixin, Base):
    """A human review of an AI-generated analysis."""

    __tablename__ = "ai_feedback"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ai_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reviewed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    original_result: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    final_result: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    changed_fields: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    feedback_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    organization = relationship("Organization", lazy="joined")
    ai_analysis = relationship("AIAnalysis", lazy="joined")

    reviewed_by = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_ai_feedback_analysis_reviewed",
            "ai_analysis_id",
            "reviewed_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AIFeedback id={self.id!s} "
            f"analysis_id={self.ai_analysis_id!s} "
            f"decision={self.decision!r}>"
        )
