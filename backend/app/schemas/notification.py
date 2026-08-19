"""Notification request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import NotificationChannel, NotificationStatus
from app.schemas.common import ORMModel


class NotificationBase(ORMModel):
    """Shared notification fields."""

    notification_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1)
    channel: NotificationChannel
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    notification_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("notification_type")
    @classmethod
    def normalize_notification_type(cls, value: str) -> str:
        cleaned = (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not cleaned:
            raise ValueError("Notification type cannot be empty.")

        return cleaned

    @field_validator("title", "message")
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Notification text cannot be empty.")

        return cleaned


class NotificationCreate(NotificationBase):
    """Create a notification for a team member."""

    organization_id: UUID
    user_id: UUID
    lead_id: UUID | None = None
    followup_id: UUID | None = None


class NotificationUpdate(ORMModel):
    """Update mutable notification fields."""

    notification_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=40,
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    message: str | None = Field(default=None, min_length=1)
    channel: NotificationChannel | None = None
    status: NotificationStatus | None = None
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    notification_metadata: dict[str, Any] | None = None

    @field_validator("notification_type")
    @classmethod
    def normalize_optional_notification_type(
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

        if not cleaned:
            raise ValueError("Notification type cannot be empty.")

        return cleaned

    @field_validator("title", "message")
    @classmethod
    def normalize_optional_required_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Notification text cannot be empty.")

        return cleaned


class NotificationResponse(NotificationBase):
    """Full notification returned by the API."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    lead_id: UUID | None = None
    followup_id: UUID | None = None
    created_at: datetime


class NotificationSummary(ORMModel):
    """Compact notification representation for lists and menus."""

    id: UUID
    user_id: UUID
    lead_id: UUID | None = None
    followup_id: UUID | None = None
    notification_type: str
    title: str
    message: str
    channel: NotificationChannel
    status: NotificationStatus
    scheduled_for: datetime | None = None
    sent_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime


class NotificationStatusUpdate(ORMModel):
    """Update notification delivery status."""

    status: NotificationStatus
    sent_at: datetime | None = None


class NotificationReadUpdate(ORMModel):
    """Mark a notification as read or unread."""

    read_at: datetime | None = None


class NotificationScheduleUpdate(ORMModel):
    """Schedule or reschedule notification delivery."""

    scheduled_for: datetime | None = None


class NotificationCountResponse(ORMModel):
    """Notification counters for the application header."""

    total: int = Field(ge=0)
    unread: int = Field(ge=0)
    pending: int = Field(ge=0)
