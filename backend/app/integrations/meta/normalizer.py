"""Normalized Meta webhook event models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.db.types import ConversationChannel, LeadSource


@dataclass(slots=True)
class NormalizedMetaMessage:
    """
    Provider-independent inbound Meta message.

    WhatsApp and Instagram webhook payloads are converted into this
    representation before entering OmniLead AI's CRM ingestion pipeline.
    """

    channel: ConversationChannel
    source: LeadSource

    sender_identity_type: str
    sender_identity_value: str

    external_message_id: str
    external_conversation_id: str

    message_text: str | None
    occurred_at: datetime

    sender_name: str | None = None

    recipient_external_id: str | None = None

    campaign_id: str | None = None
    ad_id: str | None = None
    ad_name: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )
