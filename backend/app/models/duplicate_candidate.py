"""Potential duplicate customer review model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin


class DuplicateCandidate(UUIDPrimaryKeyMixin, Base):
    """A possible customer duplicate requiring deterministic or human review."""

    __tablename__ = "duplicate_candidates"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    candidate_customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    match_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )

    match_reasons: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
        index=True,
    )

    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    organization = relationship("Organization", lazy="joined")

    customer = relationship(
        "Customer",
        foreign_keys=[customer_id],
        lazy="joined",
    )

    candidate_customer = relationship(
        "Customer",
        foreign_keys=[candidate_customer_id],
        lazy="joined",
    )

    reviewed_by = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "uq_duplicate_candidates_customer_pair",
            "organization_id",
            "customer_id",
            "candidate_customer_id",
            unique=True,
        ),
        Index(
            "ix_duplicate_candidates_org_status_score",
            "organization_id",
            "status",
            "match_score",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<DuplicateCandidate id={self.id!s} "
            f"customer_id={self.customer_id!s} "
            f"candidate_id={self.candidate_customer_id!s}>"
        )
