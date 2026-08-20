"""Enquiry request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import EnquiryStatus, LeadSource, PurchaseIntent
from app.schemas.common import ORMModel, TimestampedSchema


class EnquiryBase(ORMModel):
    """Shared enquiry fields."""

    source: LeadSource
    original_source: LeadSource | None = None
    external_reference_id: str | None = Field(default=None, max_length=255)
    customer_name_raw: str | None = Field(default=None, max_length=150)
    contact_raw: str | None = Field(default=None, max_length=320)
    message_text: str | None = None
    status: EnquiryStatus = EnquiryStatus.NEW
    received_at: datetime | None = None
    campaign_id: str | None = Field(default=None, max_length=255)
    ad_id: str | None = Field(default=None, max_length=255)
    ad_name: str | None = Field(default=None, max_length=255)
    enquiry_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "external_reference_id",
        "customer_name_raw",
        "contact_raw",
        "campaign_id",
        "ad_id",
        "ad_name",
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

    @field_validator("message_text")
    @classmethod
    def normalize_message_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class EnquiryCreate(EnquiryBase):
    """Create a raw enquiry before AI analysis."""

    organization_id: UUID
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None


class EnquiryUpdate(ORMModel):
    """Update mutable enquiry processing fields."""

    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    original_source: LeadSource | None = None
    customer_name_raw: str | None = Field(default=None, max_length=150)
    contact_raw: str | None = Field(default=None, max_length=320)
    message_text: str | None = None
    status: EnquiryStatus | None = None
    campaign_id: str | None = Field(default=None, max_length=255)
    ad_id: str | None = Field(default=None, max_length=255)
    ad_name: str | None = Field(default=None, max_length=255)
    enquiry_metadata: dict[str, Any] | None = None

    @field_validator(
        "customer_name_raw",
        "contact_raw",
        "campaign_id",
        "ad_id",
        "ad_name",
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

    @field_validator("message_text")
    @classmethod
    def normalize_optional_message_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class EnquiryResponse(EnquiryBase, TimestampedSchema):
    """Full enquiry returned by the API."""

    id: UUID
    organization_id: UUID
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    received_at: datetime


class EnquirySummary(ORMModel):
    """Compact enquiry representation for inbox and review queues."""

    id: UUID
    customer_id: UUID | None = None
    source: LeadSource
    original_source: LeadSource | None = None
    customer_name_raw: str | None = None
    contact_raw: str | None = None
    message_text: str | None = None
    status: EnquiryStatus
    received_at: datetime
    campaign_id: str | None = None
    ad_id: str | None = None


class EnquiryStatusUpdate(ORMModel):
    """Update only an enquiry processing status."""

    status: EnquiryStatus


class EnquiryLinkUpdate(ORMModel):
    """Link an enquiry to resolved customer/conversation records."""

    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None


class EnquiryCreateRequest(EnquiryBase):
    """Create an enquiry inside the authenticated organization."""

    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None


class EnquiryConvertRequest(ORMModel):
    """Convert a linked enquiry into a lead."""

    status_id: UUID
    product_id: UUID | None = None
    assigned_to_user_id: UUID | None = None

    source: LeadSource
    original_source: LeadSource | None = None

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
