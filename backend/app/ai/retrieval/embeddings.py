"""Interaction embedding generation and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers.embeddings import (
    SentenceTransformerEmbeddingProvider,
)
from app.repositories.interactions import InteractionRepository
from app.schemas.interaction import InteractionEmbeddingUpdate
from app.services.interaction_service import InteractionService


@dataclass(slots=True)
class EmbeddingBatchResult:
    """Summary of one interaction-embedding batch."""

    processed: int
    skipped: int

    interaction_ids: list[UUID]


class InteractionEmbeddingService:
    """Generate and persist embeddings for interaction content."""

    def __init__(
        self,
        db: Session,
        provider: SentenceTransformerEmbeddingProvider | None = None,
    ) -> None:
        self.db = db

        self.provider = (
            provider
            or SentenceTransformerEmbeddingProvider()
        )

        self.repository = InteractionRepository(db)
        self.interactions = InteractionService(db)

    def embed_interaction(
        self,
        organization_id: UUID,
        interaction_id: UUID,
    ):
        """Generate and persist one interaction embedding."""

        interaction = self.interactions.get(
            organization_id,
            interaction_id,
        )

        content = (
            interaction.content.strip()
            if interaction.content
            else ""
        )

        if not content:
            return interaction

        embedding = self.provider.embed_text(
            content
        )

        return self.interactions.update_embedding(
            organization_id,
            interaction.id,
            InteractionEmbeddingUpdate(
                embedding=embedding,
                embedding_model=self.provider.model_name,
            ),
        )

    def embed_pending(
        self,
        organization_id: UUID,
        *,
        limit: int = 100,
    ) -> EmbeddingBatchResult:
        """Generate embeddings for interactions missing vectors."""

        interactions = list(
            self.repository.list_without_embedding(
                organization_id,
                limit=limit,
            )
        )

        if not interactions:
            return EmbeddingBatchResult(
                processed=0,
                skipped=0,
                interaction_ids=[],
            )

        processable = []
        skipped = 0

        for interaction in interactions:
            content = (
                interaction.content.strip()
                if interaction.content
                else ""
            )

            if not content:
                skipped += 1
                continue

            processable.append(
                (
                    interaction,
                    content,
                )
            )

        if not processable:
            return EmbeddingBatchResult(
                processed=0,
                skipped=skipped,
                interaction_ids=[],
            )

        embeddings = self.provider.embed_texts(
            [
                content
                for _, content in processable
            ]
        )

        interaction_ids: list[UUID] = []

        try:
            for (
                interaction,
                _,
            ), embedding in zip(
                processable,
                embeddings,
                strict=True,
            ):
                interaction.embedding = embedding
                interaction.embedding_model = (
                    self.provider.model_name
                )

                interaction_ids.append(
                    interaction.id
                )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return EmbeddingBatchResult(
            processed=len(interaction_ids),
            skipped=skipped,
            interaction_ids=interaction_ids,
        )
