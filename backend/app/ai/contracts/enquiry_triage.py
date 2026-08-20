"""Structured AI contract for automatic enquiry triage."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

EnquiryTriageDecision = Literal[
    "SALES_LEAD",
    "GENERAL_ENQUIRY",
    "NEEDS_REVIEW",
]


class EnquiryTriageResult(BaseModel):
    """Structured classification of a newly received enquiry."""

    decision: EnquiryTriageDecision

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    reasoning: str = Field(
        min_length=1,
        max_length=2000,
    )

    requirement: str | None = Field(
        default=None,
        max_length=3000,
    )

    sales_signals: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    general_enquiry_signals: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    ambiguity_reasons: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    @field_validator(
        "reasoning",
        "requirement",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalize explanatory text."""

        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            return None

        return cleaned

    @field_validator(
        "sales_signals",
        "general_enquiry_signals",
        "ambiguity_reasons",
    )
    @classmethod
    def normalize_lists(
        cls,
        value: list[str],
    ) -> list[str]:
        """Remove empty and duplicate evidence strings."""

        cleaned: list[str] = []
        seen: set[str] = set()

        for item in value:
            normalized = " ".join(
                item.split()
            )

            if not normalized:
                continue

            key = normalized.casefold()

            if key in seen:
                continue

            seen.add(key)
            cleaned.append(normalized)

        return cleaned
