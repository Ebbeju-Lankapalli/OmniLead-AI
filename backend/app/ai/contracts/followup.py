"""Structured AI contract for follow-up recommendations."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.db.types import FollowUpType


class FollowUpRecommendationResult(BaseModel):
    """Structured sales follow-up recommendation."""

    should_follow_up: bool

    followup_type: FollowUpType | None = None

    recommended_delay_minutes: int | None = Field(
        default=None,
        ge=0,
        le=525600,
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

    urgency: str | None = Field(
        default=None,
        max_length=30,
    )

    @field_validator(
        "reason",
        "suggested_message",
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

    @field_validator("urgency")
    @classmethod
    def normalize_urgency(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        return cleaned or None
