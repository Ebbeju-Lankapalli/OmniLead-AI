"""WhatsApp Cloud API webhook parsing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.db.types import ConversationChannel, LeadSource
from app.integrations.meta.normalizer import NormalizedMetaMessage

WHATSAPP_WEBHOOK_OBJECT = "whatsapp_business_account"


def parse_whatsapp_webhook(
    payload: dict[str, Any],
) -> list[NormalizedMetaMessage]:
    """
    Convert a WhatsApp Cloud API webhook payload into normalized messages.

    Delivery/read status notifications and unsupported webhook changes are
    intentionally ignored because they are not new customer enquiries.
    """

    if payload.get("object") != WHATSAPP_WEBHOOK_OBJECT:
        return []

    normalized: list[NormalizedMetaMessage] = []

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue

        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue

            if change.get("field") != "messages":
                continue

            value = change.get("value")

            if not isinstance(value, dict):
                continue

            metadata = value.get("metadata") or {}

            phone_number_id = metadata.get(
                "phone_number_id"
            )

            contacts = _contacts_by_whatsapp_id(
                value.get("contacts")
            )

            for message in value.get("messages", []):
                if not isinstance(message, dict):
                    continue

                parsed = _parse_message(
                    message,
                    contacts=contacts,
                    phone_number_id=phone_number_id,
                    webhook_value=value,
                )

                if parsed is not None:
                    normalized.append(parsed)

    return normalized


def _parse_message(
    message: dict[str, Any],
    *,
    contacts: dict[str, str | None],
    phone_number_id: str | None,
    webhook_value: dict[str, Any],
) -> NormalizedMetaMessage | None:
    """Normalize one inbound WhatsApp message."""

    message_id = _clean_string(
        message.get("id")
    )
    sender_id = _clean_string(
        message.get("from")
    )

    if not message_id or not sender_id:
        return None

    message_type = _clean_string(
        message.get("type")
    )

    text = _extract_message_text(
        message,
        message_type,
    )

    occurred_at = _parse_unix_timestamp(
        message.get("timestamp")
    )

    sender_name = contacts.get(sender_id)

    referral = message.get("referral")

    campaign_id = None
    ad_id = None
    ad_name = None

    if isinstance(referral, dict):
        ad_id = _clean_string(
            referral.get("source_id")
        )
        ad_name = _clean_string(
            referral.get("headline")
        )

        campaign_id = _clean_string(
            referral.get("ctwa_clid")
        )

    source = (
        LeadSource.META_AD_WHATSAPP
        if isinstance(referral, dict)
        else LeadSource.WHATSAPP
    )

    return NormalizedMetaMessage(
        channel=ConversationChannel.WHATSAPP,
        source=source,
        sender_identity_type="WHATSAPP",
        sender_identity_value=sender_id,
        external_message_id=message_id,
        external_conversation_id=sender_id,
        message_text=text,
        occurred_at=occurred_at,
        sender_name=sender_name,
        recipient_external_id=_clean_string(
            phone_number_id
        ),
        campaign_id=campaign_id,
        ad_id=ad_id,
        ad_name=ad_name,
        metadata={
            "provider": "META",
            "message_type": message_type,
            "phone_number_id": phone_number_id,
            "raw_message": message,
            "webhook_metadata": (
                webhook_value.get("metadata") or {}
            ),
        },
    )


def _contacts_by_whatsapp_id(
    contacts: object,
) -> dict[str, str | None]:
    """Return contact names keyed by WhatsApp ID."""

    result: dict[str, str | None] = {}

    if not isinstance(contacts, list):
        return result

    for contact in contacts:
        if not isinstance(contact, dict):
            continue

        whatsapp_id = _clean_string(
            contact.get("wa_id")
        )

        if not whatsapp_id:
            continue

        profile = contact.get("profile")

        name = None

        if isinstance(profile, dict):
            name = _clean_string(
                profile.get("name")
            )

        result[whatsapp_id] = name

    return result


def _extract_message_text(
    message: dict[str, Any],
    message_type: str | None,
) -> str | None:
    """
    Extract useful human-readable content from supported message types.

    Non-text media is represented by its caption where available, otherwise
    by a compact descriptive placeholder.
    """

    if message_type == "text":
        text = message.get("text")

        if isinstance(text, dict):
            return _clean_string(
                text.get("body")
            )

    if message_type in {
        "image",
        "video",
        "document",
        "audio",
    }:
        media = message.get(message_type)

        if isinstance(media, dict):
            caption = _clean_string(
                media.get("caption")
            )

            if caption:
                return caption

        return f"[{message_type.upper()}]"

    if message_type == "location":
        location = message.get("location")

        if isinstance(location, dict):
            name = _clean_string(
                location.get("name")
            )
            address = _clean_string(
                location.get("address")
            )

            pieces = [
                piece
                for piece in (name, address)
                if piece
            ]

            if pieces:
                return " - ".join(pieces)

        return "[LOCATION]"

    if message_type == "button":
        button = message.get("button")

        if isinstance(button, dict):
            return _clean_string(
                button.get("text")
            )

    if message_type == "interactive":
        interactive = message.get(
            "interactive"
        )

        if isinstance(interactive, dict):
            button_reply = interactive.get(
                "button_reply"
            )

            if isinstance(button_reply, dict):
                return _clean_string(
                    button_reply.get("title")
                )

            list_reply = interactive.get(
                "list_reply"
            )

            if isinstance(list_reply, dict):
                return _clean_string(
                    list_reply.get("title")
                )

    if message_type:
        return f"[{message_type.upper()}]"

    return None


def _parse_unix_timestamp(
    value: object,
) -> datetime:
    """Convert Meta's Unix timestamp into a timezone-aware datetime."""

    try:
        timestamp = int(str(value))
    except (TypeError, ValueError):
        return datetime.now(UTC)

    return datetime.fromtimestamp(
        timestamp,
        tz=UTC,
    )


def _clean_string(
    value: object,
) -> str | None:
    """Normalize an optional string-like payload value."""

    if value is None:
        return None

    cleaned = str(value).strip()

    return cleaned or None
