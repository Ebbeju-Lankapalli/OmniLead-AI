"""Structured AI contract for next-best-action recommendations."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class NextActionResult(BaseModel):
    """Structured next-best-action recommendation."""

    action: str = Field(
        min_length=1,
        max_length=50,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )

    suggested_message: str | None = Field(
        default=None,
        max_length=5000,
    )

    recommended_followup_minutes: int | None = Field(
        default=None,
        ge=0,
        le=525600,
    )

    priority: str | None = Field(
        default=None,
        max_length=30,
    )

    @field_validator("action")
    @classmethod
    def normalize_action(
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
            raise ValueError(
                "Next action cannot be empty."
            )

        return cleaned

    @field_validator(
        "reason",
        "suggested_message",
        "priority",
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
