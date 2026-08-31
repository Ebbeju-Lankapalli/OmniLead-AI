"""Unified customer model for omnichannel identity resolution."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A unified customer/contact.

    Instagram, WhatsApp, phone, and email identities are linked through the
    customer_identities table rather than creating channel-specific customers.
    """

    __tablename__ = "customers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    company_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    primary_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    primary_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    notes_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
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

    identities = relationship(
        "CustomerIdentity",
        back_populates="customer",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_customers_organization_phone",
            "organization_id",
            "primary_phone",
        ),
        Index(
            "ix_customers_organization_email",
            "organization_id",
            "primary_email",
        ),
        Index(
            "ix_customers_organization_last_seen",
            "organization_id",
            "last_seen_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Customer id={self.id!s} "
            f"name={self.full_name!r}>"
        )
