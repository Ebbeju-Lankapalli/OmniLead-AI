"""Natural-language and structured search schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import LeadSource, PurchaseIntent
from app.schemas.common import ORMModel


class SearchScoreRange(ORMModel):
    """Inclusive score range used in lead filtering."""

    minimum: int | None = Field(default=None, ge=0, le=100)
    maximum: int | None = Field(default=None, ge=0, le=100)


class SearchDateRange(ORMModel):
    """Optional datetime range for lead activity filters."""

    start: datetime | None = None
    end: datetime | None = None


class LeadSearchFilters(ORMModel):
    """Structured filters produced manually or by AI."""

    sources: list[LeadSource] = Field(default_factory=list)
    original_sources: list[LeadSource] = Field(default_factory=list)

    purchase_intents: list[PurchaseIntent] = Field(default_factory=list)

    status_ids: list[UUID] = Field(default_factory=list)
    assigned_to_user_ids: list[UUID] = Field(default_factory=list)
    product_ids: list[UUID] = Field(default_factory=list)
    customer_ids: list[UUID] = Field(default_factory=list)

    lead_score: SearchScoreRange | None = None
    priority_score: SearchScoreRange | None = None
    followup_risk_score: SearchScoreRange | None = None

    next_followup_at: SearchDateRange | None = None
    last_contact_at: SearchDateRange | None = None

    tags: list[str] = Field(default_factory=list)

    has_assignee: bool | None = None
    has_next_followup: bool | None = None
    is_archived: bool | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
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


class SearchSort(ORMModel):
    """Requested sorting configuration."""

    field: str = Field(default="priority_score", min_length=1, max_length=50)
    direction: str = Field(default="desc")

    @field_validator("field")
    @classmethod
    def normalize_field(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Sort field cannot be empty.")

        return cleaned

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, value: str) -> str:
        cleaned = value.strip().lower()

        if cleaned not in {"asc", "desc"}:
            raise ValueError("Sort direction must be 'asc' or 'desc'.")

        return cleaned


class SearchRequest(ORMModel):
    """Search leads using natural language and/or structured filters."""

    organization_id: UUID

    query: str | None = Field(default=None, max_length=2000)
    filters: LeadSearchFilters = Field(default_factory=LeadSearchFilters)

    semantic_search: bool = False
    semantic_limit: int = Field(default=20, ge=1, le=100)

    sort: SearchSort = Field(default_factory=SearchSort)

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def normalize_query(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None


class NaturalLanguageSearchRequest(ORMModel):
    """Convert a natural-language lead query into structured filters."""

    organization_id: UUID | None = None
    query: str = Field(min_length=1, max_length=2000)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if not cleaned:
            raise ValueError("Search query cannot be empty.")

        return cleaned


class ParsedSearchResponse(ORMModel):
    """AI-parsed interpretation of a natural-language search."""

    original_query: str
    interpreted_query: str | None = None

    filters: LeadSearchFilters
    sort: SearchSort = Field(default_factory=SearchSort)

    semantic_search: bool = False

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    explanation: str | None = None


class LeadSearchResult(ORMModel):
    """A lead returned from structured or semantic search."""

    lead_id: UUID
    customer_id: UUID

    customer_name: str | None = None
    company_name: str | None = None
    primary_phone: str | None = None
    primary_email: str | None = None

    product_id: UUID | None = None
    product_name: str | None = None

    status_id: UUID
    status_name: str

    assigned_to_user_id: UUID | None = None
    assigned_to_name: str | None = None

    source: LeadSource
    original_source: LeadSource | None = None
    purchase_intent: PurchaseIntent | None = None

    requirement: str | None = None
    qualification_summary: str | None = None
    conversation_summary: str | None = None

    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    next_best_action: str | None = None
    next_followup_at: datetime | None = None
    last_contact_at: datetime | None = None

    tags: list[str] = Field(default_factory=list)

    semantic_similarity: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
    )


class SearchResponse(ORMModel):
    """Paginated lead search response."""

    query: str | None = None
    filters: LeadSearchFilters
    sort: SearchSort

    results: list[LeadSearchResult] = Field(default_factory=list)

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    semantic_search_used: bool = False

    metadata: dict[str, Any] = Field(default_factory=dict)
