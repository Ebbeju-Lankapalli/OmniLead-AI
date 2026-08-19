"""Conversation repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.db.types import ConversationChannel
from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Data-access operations for omnichannel conversations."""

    model = Conversation

    def get_by_external_id(
        self,
        organization_id: UUID,
        channel: ConversationChannel | str,
        external_conversation_id: str,
    ) -> Conversation | None:
        """Return a conversation by channel and external thread ID."""

        normalized_external_id = external_conversation_id.strip()

        if not normalized_external_id:
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

        statement = select(Conversation).where(
            Conversation.organization_id == organization_id,
            Conversation.channel == normalized_channel,
            Conversation.external_conversation_id
            == normalized_external_id,
        )

        return self.db.scalar(statement)

    def external_id_exists(
        self,
        organization_id: UUID,
        channel: ConversationChannel | str,
        external_conversation_id: str,
    ) -> bool:
        """Return whether an external conversation already exists."""

        normalized_external_id = external_conversation_id.strip()

        if not normalized_external_id:
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
            select(Conversation.id)
            .where(
                Conversation.organization_id == organization_id,
                Conversation.channel == normalized_channel,
                Conversation.external_conversation_id
                == normalized_external_id,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        channel: ConversationChannel | str | None = None,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        open_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        """Return filtered conversations for one organization."""

        statement = select(Conversation).where(
            Conversation.organization_id == organization_id
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
                    Conversation.channel == normalized_channel
                )

        if customer_id is not None:
            statement = statement.where(
                Conversation.customer_id == customer_id
            )

        if lead_id is not None:
            statement = statement.where(
                Conversation.lead_id == lead_id
            )

        if open_only:
            statement = statement.where(
                Conversation.closed_at.is_(None)
            )

        statement = (
            statement
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.started_at.desc(),
                Conversation.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_by_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        open_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        """Return conversation history for one customer."""

        return self.list_by_organization(
            organization_id,
            customer_id=customer_id,
            open_only=open_only,
            offset=offset,
            limit=limit,
        )

    def list_by_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        open_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        """Return conversations linked to one lead."""

        return self.list_by_organization(
            organization_id,
            lead_id=lead_id,
            open_only=open_only,
            offset=offset,
            limit=limit,
        )

    def list_open(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        """Return currently open conversations."""

        return self.list_by_organization(
            organization_id,
            open_only=True,
            offset=offset,
            limit=limit,
        )

    def get_latest_for_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> Conversation | None:
        """Return the most recently active conversation for a customer."""

        statement = (
            select(Conversation)
            .where(
                Conversation.organization_id == organization_id,
                Conversation.customer_id == customer_id,
            )
            .order_by(
                Conversation.last_message_at.desc().nullslast(),
                Conversation.started_at.desc(),
                Conversation.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)
