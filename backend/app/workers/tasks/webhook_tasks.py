"""Background processing for Meta webhook payloads."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.db.session import get_session_factory
from app.integrations.meta.instagram import (
    INSTAGRAM_WEBHOOK_OBJECT,
    parse_instagram_webhook,
)
from app.integrations.meta.whatsapp import (
    WHATSAPP_WEBHOOK_OBJECT,
    parse_whatsapp_webhook,
)
from app.services.meta_ingestion_service import (
    MetaIngestionService,
)
from app.workers.celery_app import celery_app
from app.workers.tasks.ai_tasks import (
    triage_enquiry_task,
)


@celery_app.task(
    name="omnilead.webhooks.process_meta",
)
def process_meta_webhook(
    organization_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Parse and persist one validated Meta webhook payload."""

    organization_uuid = UUID(
        organization_id
    )

    webhook_object = payload.get(
        "object"
    )

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

    session_factory = get_session_factory()
    db = session_factory()

    try:
        ingestion = MetaIngestionService(
            db
        )

        ingested = 0
        duplicates = 0

        for message in messages:
            result = ingestion.ingest(
                organization_uuid,
                message,
            )

            if result.duplicate:
                duplicates += 1
            else:
                ingested += 1

                triage_enquiry_task.delay(
                    str(organization_uuid),
                    str(result.enquiry.id),
                )

        return {
            "status": "completed",
            "object": webhook_object,
            "organization_id": organization_id,
            "messages_received": len(messages),
            "messages_ingested": ingested,
            "duplicates": duplicates,
        }

    finally:
        db.close()
