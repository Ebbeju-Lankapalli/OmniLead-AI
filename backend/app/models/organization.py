"""Organization model for OmniLead AI workspaces."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import DEFAULT_CURRENCY, DEFAULT_TIMEZONE
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A business workspace that owns OmniLead AI application data."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=DEFAULT_TIMEZONE,
        server_default=text(f"'{DEFAULT_TIMEZONE}'"),
    )

    default_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default=DEFAULT_CURRENCY,
        server_default=text(f"'{DEFAULT_CURRENCY}'"),
    )

    demo_mode: Mapped[bool] = mapped_column(
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

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )

    def __repr__(self) -> str:
        return (
            f"<Organization id={self.id!s} "
            f"name={self.name!r} "
            f"slug={self.slug!r}>"
        )
