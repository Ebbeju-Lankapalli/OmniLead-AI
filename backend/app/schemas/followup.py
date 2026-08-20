"""Follow-up request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.core.constants import DEFAULT_FOLLOWUP_REMINDER_MINUTES
from app.db.types import FollowUpStatus, FollowUpType
from app.schemas.common import ORMModel, TimestampedSchema


class FollowUpBase(ORMModel):
    """Shared follow-up fields."""

    followup_type: FollowUpType
    scheduled_at: datetime
    status: FollowUpStatus = FollowUpStatus.SCHEDULED
    reminder_minutes_before: int = Field(
        default=DEFAULT_FOLLOWUP_REMINDER_MINUTES,
        ge=0,
        le=10080,
    )
    reminder_sent_at: datetime | None = None
    completed_at: datetime | None = None
    outcome: str | None = None
    notes: str | None = None
    rescheduled_from_id: UUID | None = None

    @field_validator("outcome", "notes")
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class FollowUpCreate(FollowUpBase):
    """Create a scheduled lead follow-up."""

    organization_id: UUID
    lead_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID
    created_by_user_id: UUID | None = None


class FollowUpUpdate(ORMModel):
    """Update mutable follow-up fields."""

    assigned_to_user_id: UUID | None = None
    followup_type: FollowUpType | None = None
    scheduled_at: datetime | None = None
    status: FollowUpStatus | None = None
    reminder_minutes_before: int | None = Field(
        default=None,
        ge=0,
        le=10080,
    )
    reminder_sent_at: datetime | None = None
    completed_at: datetime | None = None
    outcome: str | None = None
    notes: str | None = None
    rescheduled_from_id: UUID | None = None

    @field_validator("outcome", "notes")
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class FollowUpResponse(FollowUpBase, TimestampedSchema):
    """Full follow-up returned by the API."""

    id: UUID
    organization_id: UUID
    lead_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID
    created_by_user_id: UUID | None = None


class FollowUpSummary(ORMModel):
    """Compact follow-up representation for queues and dashboards."""

    id: UUID
    lead_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID
    followup_type: FollowUpType
    scheduled_at: datetime
    status: FollowUpStatus
    reminder_minutes_before: int
    completed_at: datetime | None = None
    outcome: str | None = None


class FollowUpCompleteRequest(ORMModel):
    """Mark a follow-up as completed."""

    completed_at: datetime
    outcome: str | None = None
    notes: str | None = None

    @field_validator("outcome", "notes")
    @classmethod
    def normalize_completion_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class FollowUpRescheduleRequest(ORMModel):
    """Reschedule an existing follow-up."""

    scheduled_at: datetime
    assigned_to_user_id: UUID | None = None
    followup_type: FollowUpType | None = None
    reminder_minutes_before: int | None = Field(
        default=None,
        ge=0,
        le=10080,
    )
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_reschedule_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class FollowUpStatusUpdate(ORMModel):
    """Update only the follow-up lifecycle status."""

    status: FollowUpStatus


class FollowUpAssignmentUpdate(ORMModel):
    """Reassign a follow-up to another team member."""

    assigned_to_user_id: UUID


class FollowUpCreateRequest(ORMModel):
    """Create a follow-up inside the authenticated organization."""

    lead_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID

    followup_type: FollowUpType
    scheduled_at: datetime

    reminder_minutes_before: int = Field(
        default=DEFAULT_FOLLOWUP_REMINDER_MINUTES,
        ge=0,
        le=10080,
    )

    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_create_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class FollowUpPatchRequest(ORMModel):
    """Safely update mutable scheduled follow-up fields."""

    assigned_to_user_id: UUID | None = None
    followup_type: FollowUpType | None = None
    scheduled_at: datetime | None = None
    reminder_minutes_before: int | None = Field(
        default=None,
        ge=0,
        le=10080,
    )
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def normalize_patch_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None
