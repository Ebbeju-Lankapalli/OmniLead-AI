"""Configurable lead lifecycle status model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LeadStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Organization-scoped lead lifecycle status.

    Statuses live in the database so sales workflow states are not hard-coded
    throughout the frontend and backend.
    """

    __tablename__ = "lead_statuses"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )

    is_terminal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_won: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_lost: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
    )

    organization = relationship(
        "Organization",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "key",
            name="uq_lead_statuses_organization_key",
        ),
        Index(
            "ix_lead_statuses_org_display_order",
            "organization_id",
            "display_order",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LeadStatus id={self.id!s} "
            f"key={self.key!r} "
            f"name={self.name!r}>"
        )
