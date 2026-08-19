"""Interaction repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.db.types import (
    ConversationChannel,
    InteractionDirection,
    InteractionType,
)
from app.models.interaction import EMBEDDING_DIMENSION, Interaction
from app.repositories.base import BaseRepository


class InteractionRepository(BaseRepository[Interaction]):
    """Data-access operations for customer interactions."""

    model = Interaction

    def get_by_external_message_id(
        self,
        organization_id: UUID,
        channel: ConversationChannel | str,
        external_message_id: str,
    ) -> Interaction | None:
        """Return an interaction by channel and external message ID."""

        normalized_message_id = external_message_id.strip()

        if not normalized_message_id:
            return None

        normalized_channel = (
            channel.value
            if isinstance(channel, ConversationChannel)
            else channel.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not normalized_channel:
            return None

        statement = select(Interaction).where(
            Interaction.organization_id == organization_id,
            Interaction.channel == normalized_channel,
            Interaction.external_message_id == normalized_message_id,
        )

        return self.db.scalar(statement)

    def external_message_exists(
        self,
        organization_id: UUID,
        channel: ConversationChannel | str,
        external_message_id: str,
    ) -> bool:
        """Return whether an external message was already persisted."""

        normalized_message_id = external_message_id.strip()

        if not normalized_message_id:
            return False

        normalized_channel = (
            channel.value
            if isinstance(channel, ConversationChannel)
            else channel.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not normalized_channel:
            return False

        statement = (
            select(Interaction.id)
            .where(
                Interaction.organization_id == organization_id,
                Interaction.channel == normalized_channel,
                Interaction.external_message_id == normalized_message_id,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        conversation_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        interaction_type: InteractionType | str | None = None,
        direction: InteractionDirection | str | None = None,
        channel: ConversationChannel | str | None = None,
        occurred_from: datetime | None = None,
        occurred_to: datetime | None = None,
        newest_first: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return filtered interactions for an organization."""

        statement = select(Interaction).where(
            Interaction.organization_id == organization_id
        )

        if customer_id is not None:
            statement = statement.where(
                Interaction.customer_id == customer_id
            )

        if lead_id is not None:
            statement = statement.where(
                Interaction.lead_id == lead_id
            )

        if conversation_id is not None:
            statement = statement.where(
                Interaction.conversation_id == conversation_id
            )

        if actor_user_id is not None:
            statement = statement.where(
                Interaction.actor_user_id == actor_user_id
            )

        if interaction_type is not None:
            normalized_type = (
                interaction_type.value
                if isinstance(interaction_type, InteractionType)
                else interaction_type.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_type:
                statement = statement.where(
                    Interaction.interaction_type == normalized_type
                )

        if direction is not None:
            normalized_direction = (
                direction.value
                if isinstance(direction, InteractionDirection)
                else direction.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_direction:
                statement = statement.where(
                    Interaction.direction == normalized_direction
                )

        if channel is not None:
            normalized_channel = (
                channel.value
                if isinstance(channel, ConversationChannel)
                else channel.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_channel:
                statement = statement.where(
                    Interaction.channel == normalized_channel
                )

        if occurred_from is not None:
            statement = statement.where(
                Interaction.occurred_at >= occurred_from
            )

        if occurred_to is not None:
            statement = statement.where(
                Interaction.occurred_at <= occurred_to
            )

        if newest_first:
            statement = statement.order_by(
                Interaction.occurred_at.desc(),
                Interaction.id,
            )
        else:
            statement = statement.order_by(
                Interaction.occurred_at.asc(),
                Interaction.id,
            )

        statement = (
            statement
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_by_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        newest_first: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return the chronological interaction history for a customer."""

        return self.list_by_organization(
            organization_id,
            customer_id=customer_id,
            newest_first=newest_first,
            offset=offset,
            limit=limit,
        )

    def list_by_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        newest_first: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return interaction history associated with a lead."""

        return self.list_by_organization(
            organization_id,
            lead_id=lead_id,
            newest_first=newest_first,
            offset=offset,
            limit=limit,
        )

    def list_by_conversation(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        *,
        newest_first: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return a conversation timeline."""

        return self.list_by_organization(
            organization_id,
            conversation_id=conversation_id,
            newest_first=newest_first,
            offset=offset,
            limit=limit,
        )

    def get_latest_for_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> Interaction | None:
        """Return the customer's latest interaction."""

        statement = (
            select(Interaction)
            .where(
                Interaction.organization_id == organization_id,
                Interaction.customer_id == customer_id,
            )
            .order_by(
                Interaction.occurred_at.desc(),
                Interaction.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def list_without_embedding(
        self,
        organization_id: UUID,
        *,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return interactions that still need semantic embeddings."""

        statement = (
            select(Interaction)
            .where(
                Interaction.organization_id == organization_id,
                Interaction.embedding.is_(None),
                Interaction.content.is_not(None),
            )
            .order_by(
                Interaction.occurred_at.asc(),
                Interaction.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def semantic_search(
        self,
        organization_id: UUID,
        query_embedding: list[float],
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        limit: int = 20,
    ) -> list[tuple[Interaction, float]]:
        """
        Return interactions ordered by pgvector cosine similarity.

        Similarity is represented from approximately -1 to 1, where larger
        values indicate more semantically similar embeddings.
        """

        if len(query_embedding) != EMBEDDING_DIMENSION:
            raise ValueError(
                "Query embedding must contain exactly "
                f"{EMBEDDING_DIMENSION} dimensions."
            )

        distance = Interaction.embedding.cosine_distance(
            query_embedding
        ).label("distance")

        statement = select(
            Interaction,
            distance,
        ).where(
            Interaction.organization_id == organization_id,
            Interaction.embedding.is_not(None),
        )

        if customer_id is not None:
            statement = statement.where(
                Interaction.customer_id == customer_id
            )

        if lead_id is not None:
            statement = statement.where(
                Interaction.lead_id == lead_id
            )

        statement = (
            statement
            .order_by(distance.asc())
            .limit(max(limit, 0))
        )

        rows = self.db.execute(statement).all()

        results: list[tuple[Interaction, float]] = []

        for interaction, cosine_distance in rows:
            similarity = 1.0 - float(cosine_distance)
            results.append((interaction, similarity))

        return results
