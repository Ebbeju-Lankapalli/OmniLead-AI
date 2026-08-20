"""Customer request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import ORMModel, TimestampedSchema


class CustomerBase(ORMModel):
    """Shared customer/contact fields."""

    full_name: str | None = Field(default=None, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    primary_phone: str | None = Field(default=None, max_length=30)
    primary_email: EmailStr | None = None
    location: str | None = Field(default=None, max_length=255)
    customer_type: str | None = Field(default=None, max_length=30)
    notes_summary: str | None = None

    @field_validator(
        "full_name",
        "company_name",
        "location",
        "customer_type",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("primary_phone")
    @classmethod
    def normalize_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("notes_summary")
    @classmethod
    def normalize_notes_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class CustomerCreate(CustomerBase):
    """Create a unified customer within an organization."""

    organization_id: UUID


class CustomerUpdate(ORMModel):
    """Update mutable customer fields."""

    full_name: str | None = Field(default=None, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    primary_phone: str | None = Field(default=None, max_length=30)
    primary_email: EmailStr | None = None
    location: str | None = Field(default=None, max_length=255)
    customer_type: str | None = Field(default=None, max_length=30)
    notes_summary: str | None = None
    archived_at: datetime | None = None

    @field_validator(
        "full_name",
        "company_name",
        "location",
        "customer_type",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("primary_phone")
    @classmethod
    def normalize_optional_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("notes_summary")
    @classmethod
    def normalize_optional_notes_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class CustomerResponse(CustomerBase, TimestampedSchema):
    """Full unified customer returned by the API."""

    id: UUID
    organization_id: UUID
    first_seen_at: datetime
    last_seen_at: datetime
    archived_at: datetime | None = None


class CustomerSummary(ORMModel):
    """Compact customer representation for lead and conversation views."""

    id: UUID
    full_name: str | None = None
    company_name: str | None = None
    primary_phone: str | None = None
    primary_email: EmailStr | None = None
    customer_type: str | None = None
    last_seen_at: datetime
    archived_at: datetime | None = None


class CustomerCreateRequest(CustomerBase):
    """Create a customer inside the authenticated organization."""

    pass
