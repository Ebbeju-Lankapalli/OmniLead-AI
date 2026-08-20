"""Instagram Messaging webhook parsing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.db.types import ConversationChannel, LeadSource
from app.integrations.meta.normalizer import NormalizedMetaMessage

INSTAGRAM_WEBHOOK_OBJECT = "instagram"


def parse_instagram_webhook(
    payload: dict[str, Any],
) -> list[NormalizedMetaMessage]:
    """
    Convert Instagram Messaging webhook payloads into normalized messages.

    Only inbound customer messages are returned. Delivery/read events,
    echoes, and unsupported events are ignored.
    """

    if payload.get("object") != INSTAGRAM_WEBHOOK_OBJECT:
        return []

    normalized: list[NormalizedMetaMessage] = []

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue

        recipient_account_id = _clean_string(
            entry.get("id")
        )

        for event in entry.get("messaging", []):
            if not isinstance(event, dict):
                continue

            parsed = _parse_message_event(
                event,
                recipient_account_id=recipient_account_id,
            )

            if parsed is not None:
                normalized.append(parsed)

    return normalized


def _parse_message_event(
    event: dict[str, Any],
    *,
    recipient_account_id: str | None,
) -> NormalizedMetaMessage | None:
    """Normalize one Instagram Messaging event."""

    sender = event.get("sender")
    recipient = event.get("recipient")
    message = event.get("message")

    if not isinstance(sender, dict):
        return None

    if not isinstance(message, dict):
        return None

    if message.get("is_echo") is True:
        return None

    sender_id = _clean_string(
        sender.get("id")
    )

    message_id = _clean_string(
        message.get("mid")
    )

    if not sender_id or not message_id:
        return None

    recipient_id = recipient_account_id

    if isinstance(recipient, dict):
        recipient_id = (
            _clean_string(recipient.get("id"))
            or recipient_id
        )

    message_text = _extract_message_text(
        message
    )

    occurred_at = _parse_timestamp(
        event.get("timestamp")
    )

    referral = event.get("referral")

    campaign_id = None
    ad_id = None
    ad_name = None

    if isinstance(referral, dict):
        ad_id = _clean_string(
            referral.get("source")
            or referral.get("ad_id")
        )

        ad_name = _clean_string(
            referral.get("headline")
            or referral.get("ad_title")
        )

        campaign_id = _clean_string(
            referral.get("ref")
        )

    return NormalizedMetaMessage(
        channel=ConversationChannel.INSTAGRAM,
        source=LeadSource.INSTAGRAM,
        sender_identity_type="INSTAGRAM",
        sender_identity_value=sender_id,
        external_message_id=message_id,
        external_conversation_id=sender_id,
        message_text=message_text,
        occurred_at=occurred_at,
        sender_name=None,
        recipient_external_id=recipient_id,
        campaign_id=campaign_id,
        ad_id=ad_id,
        ad_name=ad_name,
        metadata={
            "provider": "META",
            "message_type": _message_type(
                message
            ),
            "raw_message": message,
            "raw_event": event,
        },
    )


def _extract_message_text(
    message: dict[str, Any],
) -> str | None:
    """Extract useful text or media description."""

    text = _clean_string(
        message.get("text")
    )

    if text:
        return text

    quick_reply = message.get(
        "quick_reply"
    )

    if isinstance(quick_reply, dict):
        payload = _clean_string(
            quick_reply.get("payload")
        )

        if payload:
            return payload

    attachments = message.get(
        "attachments"
    )

    if isinstance(attachments, list):
        for attachment in attachments:
            if not isinstance(
                attachment,
                dict,
            ):
                continue

            attachment_type = _clean_string(
                attachment.get("type")
            )

            if attachment_type:
                return (
                    f"[{attachment_type.upper()}]"
                )

        if attachments:
            return "[ATTACHMENT]"

    return None


def _message_type(
    message: dict[str, Any],
) -> str:
    """Return a compact Instagram message type."""

    if _clean_string(message.get("text")):
        return "text"

    if message.get("quick_reply"):
        return "quick_reply"

    attachments = message.get(
        "attachments"
    )

    if isinstance(attachments, list) and attachments:
        first = attachments[0]

        if isinstance(first, dict):
            return (
                _clean_string(
                    first.get("type")
                )
                or "attachment"
            )

        return "attachment"

    return "unknown"


def _parse_timestamp(
    value: object,
) -> datetime:
    """
    Convert Instagram's millisecond Unix timestamp to UTC.

    Instagram Messaging webhook timestamps are typically expressed
    in milliseconds.
    """

    try:
        timestamp = int(str(value))
    except (TypeError, ValueError):
        return datetime.now(UTC)

    if timestamp > 10_000_000_000:
        timestamp /= 1000

    return datetime.fromtimestamp(
        timestamp,
        tz=UTC,
    )


def _clean_string(
    value: object,
) -> str | None:
    """Normalize an optional string-like value."""

    if value is None:
        return None

    cleaned = str(value).strip()

    return cleaned or None
