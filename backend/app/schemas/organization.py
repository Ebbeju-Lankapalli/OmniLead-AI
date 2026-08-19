"""Organization request and response schemas."""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel, TimestampedSchema

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class OrganizationBase(ORMModel):
    """Shared organization fields."""

    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=100)
    timezone: str = Field(default="Asia/Kolkata", min_length=1, max_length=64)
    default_currency: str = Field(default="INR", min_length=3, max_length=3)
    demo_mode: bool = False
    is_active: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError("Organization name must contain at least 2 characters.")

        return cleaned

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        cleaned = value.strip().lower()

        if not _SLUG_PATTERN.fullmatch(cleaned):
            raise ValueError(
                "Slug may contain lowercase letters, numbers, "
                "and single hyphens only."
            )

        return cleaned

    @field_validator("default_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        cleaned = value.strip().upper()

        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError(
                "Currency must be a 3-letter alphabetic code."
            )

        return cleaned


class OrganizationCreate(OrganizationBase):
    """Create an organization."""

    pass


class OrganizationUpdate(ORMModel):
    """Update mutable organization fields."""

    name: str | None = Field(default=None, min_length=2, max_length=150)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    default_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )
    demo_mode: bool | None = None
    is_active: bool | None = None
    settings: dict[str, Any] | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError("Organization name must contain at least 2 characters.")

        return cleaned

    @field_validator("default_currency")
    @classmethod
    def normalize_optional_currency(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().upper()

        if not cleaned.isalpha() or len(cleaned) != 3:
            raise ValueError(
                "Currency must be a 3-letter alphabetic code."
            )

        return cleaned


class OrganizationResponse(OrganizationBase, TimestampedSchema):
    """Organization returned by the API."""

    id: UUID


class OrganizationSummary(ORMModel):
    """Compact organization representation."""

    id: UUID
    name: str
    slug: str
    demo_mode: bool
    is_active: bool
