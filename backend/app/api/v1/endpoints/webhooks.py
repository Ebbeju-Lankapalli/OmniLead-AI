"""Meta webhook API endpoints."""

from __future__ import annotations

import json
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request

from app.api.deps import DatabaseSession
from app.core.config import settings
from app.core.exceptions import ConfigurationError, ValidationError
from app.integrations.meta.instagram import (
    INSTAGRAM_WEBHOOK_OBJECT,
    parse_instagram_webhook,
)
from app.integrations.meta.signatures import (
    META_SIGNATURE_HEADER,
    validate_meta_signature,
)
from app.integrations.meta.webhooks import (
    verify_webhook_subscription,
)
from app.integrations.meta.whatsapp import (
    WHATSAPP_WEBHOOK_OBJECT,
    parse_whatsapp_webhook,
)
from app.workers.tasks.webhook_tasks import (
    process_meta_webhook,
)

router = APIRouter(
    prefix="/webhooks/meta",
    tags=["meta-webhooks"],
)


@router.get("")
def verify_meta_webhook(
    mode: Annotated[
        str | None,
        Query(alias="hub.mode"),
    ] = None,
    verify_token: Annotated[
        str | None,
        Query(alias="hub.verify_token"),
    ] = None,
    challenge: Annotated[
        str | None,
        Query(alias="hub.challenge"),
    ] = None,
) -> str:
    """Verify a Meta webhook subscription request."""

    return verify_webhook_subscription(
        mode=mode,
        verify_token=verify_token,
        challenge=challenge,
    )


@router.post("")
async def receive_meta_webhook(
    request: Request,
    db: DatabaseSession,
    signature: Annotated[
        str | None,
        Header(
            alias=META_SIGNATURE_HEADER,
        ),
    ] = None,
) -> dict[str, Any]:
    """
    Receive and persist WhatsApp or Instagram webhook messages.

    Meta signs the raw request body using X-Hub-Signature-256.
    The body is therefore validated before JSON parsing.
    """

    raw_body = await request.body()

    validate_meta_signature(
        raw_body,
        signature,
    )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValidationError(
            "Meta webhook payload is not valid JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise ValidationError(
            "Meta webhook payload must be a JSON object."
        )

    organization_id_raw = (
        settings.META_ORGANIZATION_ID.strip()
    )

    if not organization_id_raw:
        raise ConfigurationError(
            "META_ORGANIZATION_ID is not configured."
        )

    try:
        organization_id = UUID(
            organization_id_raw
        )
    except ValueError as exc:
        raise ConfigurationError(
            "META_ORGANIZATION_ID is not a valid UUID."
        ) from exc

    webhook_object = payload.get("object")

    if webhook_object == WHATSAPP_WEBHOOK_OBJECT:
        messages = parse_whatsapp_webhook(
            payload
        )
    elif webhook_object == INSTAGRAM_WEBHOOK_OBJECT:
        messages = parse_instagram_webhook(
            payload
        )
    else:
        return {
            "status": "ignored",
            "reason": "unsupported_meta_object",
            "object": webhook_object,
            "messages_received": 0,
            "messages_ingested": 0,
            "duplicates": 0,
        }

    task = process_meta_webhook.delay(
        str(organization_id),
        payload,
    )

    return {
        "status": "accepted",
        "object": webhook_object,
        "messages_received": len(messages),
        "task_id": task.id,
    }
