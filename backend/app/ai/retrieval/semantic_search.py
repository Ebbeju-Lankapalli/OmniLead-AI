"""Semantic lead retrieval through embedded CRM interactions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from app.repositories.interactions import InteractionRepository


class LeadSemanticSearchService:
    """
    Find leads using semantic similarity across their interactions.

    Multiple matching interactions belonging to the same lead are collapsed
    to that lead's highest similarity score.
    """

    def __init__(
        self,
        db: Session,
        provider: SentenceTransformerEmbeddingProvider | None = None,
    ) -> None:
        self.provider = (
            provider
            or SentenceTransformerEmbeddingProvider()
        )
        self.interactions = InteractionRepository(db)

    def search(
        self,
        organization_id: UUID,
        query: str,
        *,
        limit: int = 20,
    ) -> dict[UUID, float]:
        """Return lead IDs mapped to their best semantic similarity."""

        cleaned_query = query.strip()

        if not cleaned_query:
            return {}

        query_embedding = self.provider.embed_text(
            cleaned_query
        )

        matches = self.interactions.semantic_search(
            organization_id,
            query_embedding,
            limit=limit,
        )

        lead_scores: dict[UUID, float] = {}

        for interaction, similarity in matches:
            lead_id = interaction.lead_id

            if lead_id is None:
                continue

            previous = lead_scores.get(
                lead_id
            )

            if (
                previous is None
                or similarity > previous
            ):
                lead_scores[lead_id] = similarity

        return lead_scores
