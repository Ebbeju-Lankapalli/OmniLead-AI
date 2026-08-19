"""Product request and response schemas."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ORMModel, TimestampedSchema


class ProductBase(ORMModel):
    """Shared product fields."""

    name: str = Field(min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    price: Decimal | None = Field(default=None, ge=Decimal("0"))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if not cleaned:
            raise ValueError("Product name cannot be empty.")

        return cleaned

    @field_validator("code")
    @classmethod
    def normalize_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().upper()
        return cleaned or None

    @field_validator("category")
    @classmethod
    def normalize_category(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().upper()

        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError(
                "Currency must be a 3-letter alphabetic code."
            )

        return cleaned


class ProductCreate(ProductBase):
    """Create a product within an organization."""

    organization_id: UUID


class ProductUpdate(ORMModel):
    """Update mutable product fields."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    price: Decimal | None = Field(default=None, ge=Decimal("0"))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())

        if not cleaned:
            raise ValueError("Product name cannot be empty.")

        return cleaned

    @field_validator("code")
    @classmethod
    def normalize_optional_code(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().upper()
        return cleaned or None

    @field_validator("category")
    @classmethod
    def normalize_optional_category(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("description")
    @classmethod
    def normalize_optional_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("currency")
    @classmethod
    def normalize_optional_currency(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().upper()

        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError(
                "Currency must be a 3-letter alphabetic code."
            )

        return cleaned


class ProductResponse(ProductBase, TimestampedSchema):
    """Full product returned by the API."""

    id: UUID
    organization_id: UUID


class ProductSummary(ORMModel):
    """Compact product representation for lead views."""

    id: UUID
    name: str
    code: str | None = None
    category: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    is_active: bool
