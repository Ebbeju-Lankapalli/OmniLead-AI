"""Structured AI contract for sales-objection detection."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ObjectionItem(BaseModel):
    """One customer objection detected in a conversation."""

    category: str = Field(
        min_length=1,
        max_length=50,
    )

    objection: str = Field(
        min_length=1,
        max_length=1000,
    )

    severity: str = Field(
        min_length=1,
        max_length=30,
    )

    suggested_response: str | None = Field(
        default=None,
        max_length=3000,
    )

    @field_validator(
        "category",
        "severity",
    )
    @classmethod
    def normalize_enum_like_text(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not cleaned:
            raise ValueError("Value cannot be empty.")

        return cleaned

    @field_validator(
        "objection",
        "suggested_response",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class ObjectionAnalysisResult(BaseModel):
    """Structured objection-analysis output."""

    objections_detected: bool

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    objections: list[ObjectionItem] = Field(
        default_factory=list,
        max_length=20,
    )

    overall_summary: str | None = Field(
        default=None,
        max_length=3000,
    )

    @field_validator("overall_summary")
    @classmethod
    def normalize_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None
