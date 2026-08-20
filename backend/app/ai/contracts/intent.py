"""Structured AI contract for purchase-intent classification."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.db.types import PurchaseIntent


class IntentAnalysisResult(BaseModel):
    """Structured purchase-intent classification returned by AI."""

    purchase_intent: PurchaseIntent

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str = Field(
        min_length=1,
        max_length=2000,
    )

    buying_signals: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    negative_signals: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    @field_validator("reasoning")
    @classmethod
    def normalize_reasoning(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Intent reasoning cannot be empty."
            )

        return cleaned

    @field_validator(
        "buying_signals",
        "negative_signals",
    )
    @classmethod
    def normalize_signals(
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
