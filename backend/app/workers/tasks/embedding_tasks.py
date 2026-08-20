"""Celery tasks for CRM interaction embeddings."""

from __future__ import annotations

from uuid import UUID

from app.ai.retrieval.embeddings import (
    InteractionEmbeddingService,
)
from app.db.session import get_session_factory
from app.workers.celery_app import celery_app


@celery_app.task(
    name="omnilead.embeddings.embed_pending",
)
def embed_pending_interactions(
    organization_id: str,
    limit: int = 100,
) -> dict[str, object]:
    """Generate embeddings for interactions missing vectors."""

    parsed_organization_id = UUID(
        organization_id
    )

    session_factory = get_session_factory()
    db = session_factory()

    try:
        result = InteractionEmbeddingService(
            db
        ).embed_pending(
            parsed_organization_id,
            limit=limit,
        )

        return {
            "organization_id": organization_id,
            "processed": result.processed,
            "skipped": result.skipped,
            "interaction_ids": [
                str(interaction_id)
                for interaction_id
                in result.interaction_ids
            ],
        }

    finally:
        db.close()
