"""Internal sales note model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Note(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An internal employee note attached to a customer or lead."""

    __tablename__ = "notes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        index=True,
    )

    organization = relationship("Organization", lazy="joined")
    lead = relationship("Lead", lazy="joined")
    customer = relationship("Customer", lazy="joined")
    author = relationship(
        "User",
        foreign_keys=[author_user_id],
        lazy="joined",
    )

    __table_args__ = (
        Index(
            "ix_notes_lead_created",
            "lead_id",
            "created_at",
        ),
        Index(
            "ix_notes_customer_created",
            "customer_id",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Note id={self.id!s} "
            f"lead_id={self.lead_id!s} "
            f"author_user_id={self.author_user_id!s}>"
        )
