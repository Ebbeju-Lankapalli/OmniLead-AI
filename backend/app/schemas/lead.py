"""Lead request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import LeadSource, PurchaseIntent
from app.schemas.common import ORMModel, TimestampedSchema


class LeadBase(ORMModel):
    """Shared lead fields."""

    source: LeadSource
    original_source: LeadSource | None = None
    campaign_id: str | None = Field(default=None, max_length=255)
    ad_id: str | None = Field(default=None, max_length=255)
    requirement: str | None = None
    original_enquiry: str | None = None
    purchase_intent: PurchaseIntent | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(default=None, ge=0, le=100)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    qualification_summary: str | None = None
    conversation_summary: str | None = None
    next_best_action: str | None = Field(default=None, max_length=50)
    next_best_action_reason: str | None = None
    tags: list[str] = Field(default_factory=list)
    last_contact_at: datetime | None = None
    next_followup_at: datetime | None = None
    closed_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator(
        "campaign_id",
        "ad_id",
        "next_best_action",
    )
    @classmethod
    def normalize_optional_short_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator(
        "requirement",
        "original_enquiry",
        "qualification_summary",
        "conversation_summary",
        "next_best_action_reason",
    )
    @classmethod
    def normalize_optional_long_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

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


class LeadCreate(LeadBase):
    """Create a sales lead."""

    organization_id: UUID
    customer_id: UUID
    status_id: UUID
    source_enquiry_id: UUID | None = None
    product_id: UUID | None = None
    assigned_to_user_id: UUID | None = None


class LeadUpdate(ORMModel):
    """Update mutable lead fields."""

    source_enquiry_id: UUID | None = None
    product_id: UUID | None = None
    status_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    source: LeadSource | None = None
    original_source: LeadSource | None = None
    campaign_id: str | None = Field(default=None, max_length=255)
    ad_id: str | None = Field(default=None, max_length=255)
    requirement: str | None = None
    original_enquiry: str | None = None
    purchase_intent: PurchaseIntent | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(default=None, ge=0, le=100)
    score_breakdown: dict[str, Any] | None = None
    qualification_summary: str | None = None
    conversation_summary: str | None = None
    next_best_action: str | None = Field(default=None, max_length=50)
    next_best_action_reason: str | None = None
    tags: list[str] | None = None
    last_contact_at: datetime | None = None
    next_followup_at: datetime | None = None
    closed_at: datetime | None = None
    archived_at: datetime | None = None

    @field_validator(
        "campaign_id",
        "ad_id",
        "next_best_action",
    )
    @classmethod
    def normalize_optional_short_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator(
        "requirement",
        "original_enquiry",
        "qualification_summary",
        "conversation_summary",
        "next_best_action_reason",
    )
    @classmethod
    def normalize_optional_long_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("tags")
    @classmethod
    def normalize_optional_tags(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return None

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


class LeadResponse(LeadBase, TimestampedSchema):
    """Full lead returned by the API."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    source_enquiry_id: UUID | None = None
    product_id: UUID | None = None
    status_id: UUID
    assigned_to_user_id: UUID | None = None


class LeadSummary(ORMModel):
    """Compact lead representation for tables and queues."""

    id: UUID
    customer_id: UUID
    product_id: UUID | None = None
    status_id: UUID
    assigned_to_user_id: UUID | None = None
    source: LeadSource
    purchase_intent: PurchaseIntent | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(default=None, ge=0, le=100)
    next_followup_at: datetime | None = None
    last_contact_at: datetime | None = None
    archived_at: datetime | None = None


class LeadStatusUpdate(ORMModel):
    """Update only the lead lifecycle status."""

    status_id: UUID
    closed_at: datetime | None = None


class LeadAssignmentUpdate(ORMModel):
    """Assign or reassign a lead."""

    assigned_to_user_id: UUID | None = None


class LeadScoreUpdate(ORMModel):
    """Update explainable AI/rule-based lead scoring."""

    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(default=None, ge=0, le=100)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)


class LeadAIInsightUpdate(ORMModel):
    """Update AI-assisted lead intelligence fields."""

    purchase_intent: PurchaseIntent | None = None
    qualification_summary: str | None = None
    conversation_summary: str | None = None
    next_best_action: str | None = Field(default=None, max_length=50)
    next_best_action_reason: str | None = None


class LeadCreateRequest(ORMModel):
    """Create a lead inside the authenticated user's organization."""

    customer_id: UUID
    status_id: UUID

    source: LeadSource
    original_source: LeadSource | None = None

    source_enquiry_id: UUID | None = None
    product_id: UUID | None = None
    assigned_to_user_id: UUID | None = None

    campaign_id: str | None = Field(
        default=None,
        max_length=255,
    )
    ad_id: str | None = Field(
        default=None,
        max_length=255,
    )

    requirement: str | None = None
    original_enquiry: str | None = None

    purchase_intent: PurchaseIntent | None = None

    lead_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    priority_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    followup_risk_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    score_breakdown: dict[str, Any] = Field(
        default_factory=dict,
    )

    qualification_summary: str | None = None
    conversation_summary: str | None = None

    next_best_action: str | None = Field(
        default=None,
        max_length=50,
    )
    next_best_action_reason: str | None = None

    tags: list[str] = Field(
        default_factory=list,
    )

    last_contact_at: datetime | None = None
    next_followup_at: datetime | None = None

    @field_validator(
        "campaign_id",
        "ad_id",
        "next_best_action",
        "requirement",
        "original_enquiry",
        "qualification_summary",
        "conversation_summary",
        "next_best_action_reason",
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

    @field_validator("tags")
    @classmethod
    def normalize_create_tags(
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
