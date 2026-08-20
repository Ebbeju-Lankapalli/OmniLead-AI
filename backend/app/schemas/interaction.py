"""Interaction request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.db.types import (
    ConversationChannel,
    InteractionDirection,
    InteractionType,
)
from app.models.interaction import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
)
from app.schemas.common import ORMModel


class InteractionBase(ORMModel):
    """Shared interaction fields."""

    interaction_type: InteractionType
    direction: InteractionDirection | None = None
    channel: ConversationChannel
    content: str | None = None
    external_message_id: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None
    interaction_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("content")
    @classmethod
    def normalize_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("external_message_id")
    @classmethod
    def normalize_external_message_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class InteractionCreate(InteractionBase):
    """Create a customer interaction."""

    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    actor_user_id: UUID | None = None


class InteractionUpdate(ORMModel):
    """Update mutable interaction fields."""

    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    actor_user_id: UUID | None = None
    direction: InteractionDirection | None = None
    content: str | None = None
    external_message_id: str | None = Field(default=None, max_length=255)
    occurred_at: datetime | None = None
    interaction_metadata: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def normalize_optional_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("external_message_id")
    @classmethod
    def normalize_optional_external_message_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class InteractionResponse(InteractionBase):
    """Full interaction returned by the API."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    actor_user_id: UUID | None = None
    occurred_at: datetime
    embedding_model: str | None = None
    created_at: datetime


class InteractionSummary(ORMModel):
    """Compact interaction representation for timelines."""

    id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    actor_user_id: UUID | None = None
    interaction_type: InteractionType
    direction: InteractionDirection | None = None
    channel: ConversationChannel
    content: str | None = None
    occurred_at: datetime


class InteractionEmbeddingUpdate(ORMModel):
    """Internal payload for persisting a semantic embedding."""

    embedding: list[float] = Field(
        min_length=EMBEDDING_DIMENSION,
        max_length=EMBEDDING_DIMENSION,
    )
    embedding_model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        min_length=1,
        max_length=150,
    )

    @field_validator("embedding_model")
    @classmethod
    def normalize_embedding_model(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Embedding model cannot be empty.")

        return cleaned


class InteractionCreateRequest(ORMModel):
    """Create an authenticated CRM interaction."""

    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None

    interaction_type: InteractionType
    direction: InteractionDirection | None = None
    channel: ConversationChannel

    content: str | None = None

    external_message_id: str | None = Field(
        default=None,
        max_length=255,
    )

    occurred_at: datetime | None = None

    interaction_metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator("content")
    @classmethod
    def normalize_create_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("external_message_id")
    @classmethod
    def normalize_create_external_message_id(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class InteractionPatchRequest(ORMModel):
    """Safely update mutable CRM interaction fields."""

    lead_id: UUID | None = None
    conversation_id: UUID | None = None

    content: str | None = None

    interaction_metadata: dict[str, Any] | None = None

    @field_validator("content")
    @classmethod
    def normalize_patch_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None
