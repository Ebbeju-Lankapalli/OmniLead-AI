"""Structured AI contract for customer-conversation summaries."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ConversationSummaryResult(BaseModel):
    """Structured conversation summary produced by AI."""

    summary: str = Field(
        min_length=1,
        max_length=5000,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    key_points: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    customer_requirements: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    commitments: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    unresolved_questions: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    @field_validator("summary")
    @classmethod
    def normalize_summary(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Conversation summary cannot be empty."
            )

        return cleaned

    @field_validator(
        "key_points",
        "customer_requirements",
        "commitments",
        "unresolved_questions",
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
