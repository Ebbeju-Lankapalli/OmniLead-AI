"""Customer channel identity model for deterministic identity resolution."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CustomerIdentity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A normalized identity belonging to a customer.

    Examples:
    - phone number
    - email address
    - WhatsApp identifier
    - Instagram user identifier
    """

    __tablename__ = "customer_identities"

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
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    identity_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    identity_value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    normalized_value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    display_value: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )

    source: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    identity_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    customer = relationship(
        "Customer",
        back_populates="identities",
    )

    organization = relationship(
        "Organization",
        lazy="joined",
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "identity_type",
            "normalized_value",
            name="uq_customer_identities_org_type_normalized",
        ),
        Index(
            "ix_customer_identities_customer_type",
            "customer_id",
            "identity_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerIdentity id={self.id!s} "
            f"type={self.identity_type!r}>"
        )
