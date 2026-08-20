"""Structured AI contract for lead qualification."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QualificationResult(BaseModel):
    """Structured lead-qualification result."""

    qualified: bool

    qualification_score: int = Field(
        ge=0,
        le=100,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    summary: str = Field(
        min_length=1,
        max_length=3000,
    )

    requirement: str | None = Field(
        default=None,
        max_length=3000,
    )

    urgency: str | None = Field(
        default=None,
        max_length=100,
    )

    budget_signal: str | None = Field(
        default=None,
        max_length=500,
    )

    authority_signal: str | None = Field(
        default=None,
        max_length=500,
    )

    timeline_signal: str | None = Field(
        default=None,
        max_length=500,
    )

    qualification_reasons: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    disqualification_reasons: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    @field_validator(
        "summary",
        "requirement",
        "urgency",
        "budget_signal",
        "authority_signal",
        "timeline_signal",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator(
        "qualification_reasons",
        "disqualification_reasons",
    )
    @classmethod
    def normalize_reason_lists(
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
