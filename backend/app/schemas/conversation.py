"""Conversation request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import ConversationChannel
from app.schemas.common import ORMModel, TimestampedSchema


class ConversationBase(ORMModel):
    """Shared conversation fields."""

    channel: ConversationChannel
    external_conversation_id: str | None = Field(
        default=None,
        max_length=255,
    )
    title: str | None = Field(default=None, max_length=255)
    started_at: datetime | None = None
    last_message_at: datetime | None = None
    closed_at: datetime | None = None
    summary: str | None = None
    conversation_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "external_conversation_id",
        "title",
    )
    @classmethod
    def normalize_optional_short_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("summary")
    @classmethod
    def normalize_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class ConversationCreate(ConversationBase):
    """Create a unified customer conversation."""

    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None


class ConversationUpdate(ORMModel):
    """Update mutable conversation fields."""

    lead_id: UUID | None = None
    external_conversation_id: str | None = Field(
        default=None,
        max_length=255,
    )
    title: str | None = Field(default=None, max_length=255)
    last_message_at: datetime | None = None
    closed_at: datetime | None = None
    summary: str | None = None
    conversation_metadata: dict[str, Any] | None = None

    @field_validator(
        "external_conversation_id",
        "title",
    )
    @classmethod
    def normalize_optional_short_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())
        return cleaned or None

    @field_validator("summary")
    @classmethod
    def normalize_optional_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class ConversationResponse(ConversationBase, TimestampedSchema):
    """Full conversation returned by the API."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    started_at: datetime


class ConversationSummary(ORMModel):
    """Compact conversation representation for inbox and lead views."""

    id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    channel: ConversationChannel
    title: str | None = None
    started_at: datetime
    last_message_at: datetime | None = None
    closed_at: datetime | None = None
    summary: str | None = None


class ConversationLeadLinkUpdate(ORMModel):
    """Link or unlink a conversation from a lead."""

    lead_id: UUID | None = None


class ConversationCloseUpdate(ORMModel):
    """Close or reopen a conversation."""

    closed_at: datetime | None = None
