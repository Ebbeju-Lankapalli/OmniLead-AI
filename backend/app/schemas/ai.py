"""AI analysis, observability, and human-review schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import AIReviewDecision
from app.schemas.common import ORMModel


class AIAnalysisBase(ORMModel):
    """Shared fields for an auditable AI analysis."""

    analysis_type: str = Field(
        min_length=1,
        max_length=50,
    )

    model_provider: str = Field(
        min_length=1,
        max_length=50,
    )

    model_name: str = Field(
        min_length=1,
        max_length=100,
    )

    prompt_name: str = Field(
        min_length=1,
        max_length=100,
    )

    prompt_version: str = Field(
        min_length=1,
        max_length=50,
    )

    input_hash: str | None = Field(
        default=None,
        max_length=64,
    )

    result: dict[str, Any] = Field(
        default_factory=dict,
    )

    model_confidence: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )

    status: str = Field(
        min_length=1,
        max_length=30,
    )

    latency_ms: int | None = Field(
        default=None,
        ge=0,
    )

    input_tokens: int | None = Field(
        default=None,
        ge=0,
    )

    output_tokens: int | None = Field(
        default=None,
        ge=0,
    )

    error_code: str | None = Field(
        default=None,
        max_length=100,
    )

    error_message: str | None = None

    @field_validator(
        "analysis_type",
        "status",
    )
    @classmethod
    def normalize_enum_like_text(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not cleaned:
            raise ValueError("Value cannot be empty.")

        return cleaned

    @field_validator(
        "model_provider",
        "model_name",
        "prompt_name",
        "prompt_version",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str,
    ) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Value cannot be empty.")

        return cleaned

    @field_validator(
        "input_hash",
        "error_code",
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

    @field_validator("error_message")
    @classmethod
    def normalize_error_message(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class AIAnalysisCreate(AIAnalysisBase):
    """Persist a new AI analysis."""

    organization_id: UUID

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    enquiry_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    call_recording_id: UUID | None = None


class AIAnalysisUpdate(ORMModel):
    """Update mutable observability/result fields."""

    result: dict[str, Any] | None = None

    model_confidence: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )

    status: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    latency_ms: int | None = Field(
        default=None,
        ge=0,
    )

    input_tokens: int | None = Field(
        default=None,
        ge=0,
    )

    output_tokens: int | None = Field(
        default=None,
        ge=0,
    )

    error_code: str | None = Field(
        default=None,
        max_length=100,
    )

    error_message: str | None = None

    @field_validator("status")
    @classmethod
    def normalize_status(
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
        "error_code",
        "error_message",
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


class AIAnalysisResponse(AIAnalysisBase):
    """Full persisted AI analysis returned by the API."""

    id: UUID
    organization_id: UUID

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    enquiry_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    call_recording_id: UUID | None = None

    created_at: datetime


class AIAnalysisSummary(ORMModel):
    """Compact AI analysis representation for review queues."""

    id: UUID

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    enquiry_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    call_recording_id: UUID | None = None

    analysis_type: str

    model_provider: str
    model_name: str

    model_confidence: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )

    status: str
    latency_ms: int | None = Field(default=None, ge=0)

    created_at: datetime


class AIFeedbackCreate(ORMModel):
    """Submit a human review for an AI analysis."""

    organization_id: UUID
    ai_analysis_id: UUID
    reviewed_by_user_id: UUID

    decision: AIReviewDecision

    original_result: dict[str, Any]
    final_result: dict[str, Any] | None = None

    changed_fields: list[str] = Field(
        default_factory=list,
    )

    feedback_notes: str | None = None

    @field_validator("changed_fields")
    @classmethod
    def normalize_changed_fields(
        cls,
        value: list[str],
    ) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for field_name in value:
            normalized = field_name.strip()

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(normalized)

        return cleaned

    @field_validator("feedback_notes")
    @classmethod
    def normalize_feedback_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class AIFeedbackResponse(ORMModel):
    """Persisted human review returned by the API."""

    id: UUID
    organization_id: UUID
    ai_analysis_id: UUID
    reviewed_by_user_id: UUID

    decision: AIReviewDecision

    original_result: dict[str, Any]
    final_result: dict[str, Any] | None = None
    changed_fields: list[str] = Field(default_factory=list)

    feedback_notes: str | None = None
    reviewed_at: datetime


class AIReviewQueueItem(ORMModel):
    """AI result awaiting or showing human review."""

    analysis: AIAnalysisSummary

    customer_name: str | None = None
    lead_status_name: str | None = None

    result: dict[str, Any] = Field(default_factory=dict)

    has_feedback: bool = False
    feedback_decision: AIReviewDecision | None = None

    requires_review: bool = False
    review_reason: str | None = None


class AIReviewQueueResponse(ORMModel):
    """Paginated AI human-review queue."""

    items: list[AIReviewQueueItem] = Field(
        default_factory=list,
    )

    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)

    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class AIExecutionRequest(ORMModel):
    """Generic request to execute a supported AI workflow."""

    organization_id: UUID

    analysis_type: str = Field(
        min_length=1,
        max_length=50,
    )

    customer_id: UUID | None = None
    lead_id: UUID | None = None
    enquiry_id: UUID | None = None
    conversation_id: UUID | None = None
    interaction_id: UUID | None = None
    call_recording_id: UUID | None = None

    force_refresh: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("analysis_type")
    @classmethod
    def normalize_analysis_type(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not cleaned:
            raise ValueError("Analysis type cannot be empty.")

        return cleaned


class AIExecutionResponse(ORMModel):
    """Response returned after starting or completing an AI workflow."""

    analysis_id: UUID

    analysis_type: str
    status: str

    result: dict[str, Any] = Field(
        default_factory=dict,
    )

    confidence: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("1"),
    )

    requires_review: bool = False

    @field_validator(
        "analysis_type",
        "status",
    )
    @classmethod
    def normalize_execution_values(
        cls,
        value: str,
    ) -> str:
        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not cleaned:
            raise ValueError("Value cannot be empty.")

        return cleaned
