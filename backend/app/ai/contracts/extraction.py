"""Structured AI contract for extracting customer and enquiry details."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ExtractionResult(BaseModel):
    """Structured entities extracted from customer communication."""

    customer_name: str | None = Field(
        default=None,
        max_length=150,
    )

    company_name: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    email: str | None = Field(
        default=None,
        max_length=320,
    )

    product_name: str | None = Field(
        default=None,
        max_length=150,
    )

    requirement: str | None = Field(
        default=None,
        max_length=3000,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    budget: str | None = Field(
        default=None,
        max_length=500,
    )

    timeline: str | None = Field(
        default=None,
        max_length=500,
    )

    quantities: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    keywords: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @field_validator(
        "customer_name",
        "company_name",
        "phone",
        "email",
        "product_name",
        "requirement",
        "location",
        "budget",
        "timeline",
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

    @field_validator(
        "quantities",
        "keywords",
    )
    @classmethod
    def normalize_lists(
        cls,
        value: list[str],
    ) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for item in value:
            normalized = " ".join(item.split())

            if not normalized:
                continue

            key = normalized.casefold()

            if key in seen:
                continue

            seen.add(key)
            cleaned.append(normalized)

        return cleaned
