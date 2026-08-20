"""Structured AI contract for natural-language lead search."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.db.types import LeadSource, PurchaseIntent


class SearchScoreRangeContract(BaseModel):
    """Inclusive score range parsed from natural language."""

    minimum: int | None = Field(default=None, ge=0, le=100)
    maximum: int | None = Field(default=None, ge=0, le=100)


class SearchDateRangeContract(BaseModel):
    """Optional datetime range parsed from natural language."""

    start: datetime | None = None
    end: datetime | None = None


class NaturalLanguageSearchFiltersResult(BaseModel):
    """Validated filters produced by the AI search parser."""

    interpreted_query: str | None = Field(
        default=None,
        max_length=2000,
    )

    sources: list[LeadSource] = Field(
        default_factory=list,
    )

    purchase_intents: list[PurchaseIntent] = Field(
        default_factory=list,
    )

    lead_score: SearchScoreRangeContract | None = None
    priority_score: SearchScoreRangeContract | None = None
    followup_risk_score: SearchScoreRangeContract | None = None

    next_followup_at: SearchDateRangeContract | None = None
    last_contact_at: SearchDateRangeContract | None = None

    tags: list[str] = Field(
        default_factory=list,
    )

    has_assignee: bool | None = None
    has_next_followup: bool | None = None
    is_archived: bool | None = None

    sort_field: str = Field(
        default="priority_score",
        min_length=1,
        max_length=50,
    )

    sort_direction: str = Field(
        default="desc",
    )

    semantic_search: bool = False

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    explanation: str | None = Field(
        default=None,
        max_length=3000,
    )

    @field_validator("tags")
    @classmethod
    def normalize_tags(
        cls,
        value: list[str],
    ) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for tag in value:
            normalized = " ".join(tag.split())

            if not normalized:
                continue

            key = normalized.casefold()

            if key in seen:
                continue

            seen.add(key)
            cleaned.append(normalized)

        return cleaned

    @field_validator("sort_field")
    @classmethod
    def validate_sort_field(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        allowed = {
            "priority_score",
            "lead_score",
            "followup_risk_score",
            "next_followup_at",
            "last_contact_at",
            "created_at",
        }

        if cleaned not in allowed:
            return "priority_score"

        return cleaned

    @field_validator("sort_direction")
    @classmethod
    def validate_sort_direction(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip().lower()

        if cleaned not in {"asc", "desc"}:
            return "desc"

        return cleaned
