"""Structured AI contract for call-intelligence analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.db.types import PurchaseIntent


class CallAnalysisResult(BaseModel):
    """Structured call-intelligence output."""

    summary: str = Field(
        min_length=1,
        max_length=5000,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    purchase_intent: PurchaseIntent | None = None

    sentiment: str | None = Field(
        default=None,
        max_length=30,
    )

    requirement: str | None = Field(
        default=None,
        max_length=3000,
    )

    objections: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    commitments: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    action_items: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    customer_questions: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    key_moments: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    @field_validator(
        "summary",
        "requirement",
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

    @field_validator("sentiment")
    @classmethod
    def normalize_sentiment(
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

    @field_validator(
        "objections",
        "commitments",
        "action_items",
        "customer_questions",
        "key_moments",
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
