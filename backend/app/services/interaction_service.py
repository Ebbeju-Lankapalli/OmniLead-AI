"""Interaction and communication-timeline business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.types import InteractionDirection
from app.models.interaction import Interaction
from app.repositories.customers import CustomerRepository
from app.repositories.interactions import InteractionRepository
from app.repositories.leads import LeadRepository
from app.repositories.users import UserRepository
from app.schemas.interaction import (
    InteractionCreate,
    InteractionEmbeddingUpdate,
    InteractionUpdate,
)
from app.services.conversation_service import ConversationService


class InteractionService:
    """Business operations for customer communication interactions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.interactions = InteractionRepository(db)
        self.customers = CustomerRepository(db)
        self.leads = LeadRepository(db)
        self.users = UserRepository(db)
        self.conversations = ConversationService(db)

    def get(
        self,
        organization_id: UUID,
        interaction_id: UUID,
    ) -> Interaction:
        """Return an organization-scoped interaction."""

        interaction = self.interactions.get(interaction_id)

        if (
            interaction is None
            or interaction.organization_id != organization_id
        ):
            raise NotFoundError(
                "Interaction not found.",
                details={
                    "interaction_id": str(interaction_id),
                },
            )

        return interaction

    def create(
        self,
        payload: InteractionCreate,
    ) -> Interaction:
        """
        Persist an interaction and synchronize its CRM timeline atomically.
        """

        customer = self.customers.get(payload.customer_id)

        if (
            customer is None
            or customer.organization_id != payload.organization_id
        ):
            raise NotFoundError(
                "Customer not found.",
                details={
                    "customer_id": str(payload.customer_id),
                },
            )

        lead = None

        if payload.lead_id is not None:
            lead = self.leads.get(payload.lead_id)

            if (
                lead is None
                or lead.organization_id != payload.organization_id
            ):
                raise NotFoundError(
                    "Lead not found.",
                    details={
                        "lead_id": str(payload.lead_id),
                    },
                )

            if lead.customer_id != payload.customer_id:
                raise ValidationError(
                    "Interaction customer does not match lead customer."
                )

        conversation = None

        if payload.conversation_id is not None:
            conversation = self.conversations.get(
                payload.organization_id,
                payload.conversation_id,
            )

            if conversation.customer_id != payload.customer_id:
                raise ValidationError(
                    "Interaction customer does not match "
                    "conversation customer."
                )

            if (
                payload.lead_id is not None
                and conversation.lead_id is not None
                and conversation.lead_id != payload.lead_id
            ):
                raise ValidationError(
                    "Interaction lead does not match conversation lead."
                )

            if (
                payload.lead_id is None
                and conversation.lead_id is not None
            ):
                lead = self.leads.get(conversation.lead_id)

        if payload.actor_user_id is not None:
            actor = self.users.get(payload.actor_user_id)

            if (
                actor is None
                or actor.organization_id != payload.organization_id
            ):
                raise NotFoundError(
                    "Interaction actor not found.",
                    details={
                        "user_id": str(payload.actor_user_id),
                    },
                )

        if payload.external_message_id is not None:
            existing = self.interactions.get_by_external_message_id(
                payload.organization_id,
                payload.channel,
                payload.external_message_id,
            )

            if existing is not None:
                raise ConflictError(
                    "External message has already been processed.",
                    details={
                        "interaction_id": str(existing.id),
                        "external_message_id": (
                            payload.external_message_id
                        ),
                    },
                )

        values = payload.model_dump()

        if values["occurred_at"] is None:
            values.pop("occurred_at")

        if (
            values.get("lead_id") is None
            and conversation is not None
            and conversation.lead_id is not None
        ):
            values["lead_id"] = conversation.lead_id

        interaction = Interaction(**values)

        try:
            self.interactions.add(interaction)
            self.db.flush()

            occurred_at = interaction.occurred_at

            if conversation is not None:
                if (
                    conversation.last_message_at is None
                    or occurred_at > conversation.last_message_at
                ):
                    conversation.last_message_at = occurred_at

                if (
                    conversation.lead_id is None
                    and interaction.lead_id is not None
                ):
                    conversation.lead_id = interaction.lead_id

            if occurred_at > customer.last_seen_at:
                customer.last_seen_at = occurred_at

            if (
                lead is not None
                and payload.direction != InteractionDirection.INTERNAL
                and (
                    lead.last_contact_at is None
                    or occurred_at > lead.last_contact_at
                )
            ):
                lead.last_contact_at = occurred_at

            self.db.commit()
            self.db.refresh(interaction)

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "External message has already been processed."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return interaction

    def update(
        self,
        organization_id: UUID,
        interaction_id: UUID,
        payload: InteractionUpdate,
    ) -> Interaction:
        """Update mutable interaction fields."""

        interaction = self.get(
            organization_id,
            interaction_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return interaction

        if "lead_id" in values:
            lead_id = values["lead_id"]

            if lead_id is not None:
                lead = self.leads.get(lead_id)

                if (
                    lead is None
                    or lead.organization_id != organization_id
                ):
                    raise NotFoundError(
                        "Lead not found."
                    )

                if lead.customer_id != interaction.customer_id:
                    raise ValidationError(
                        "Interaction customer does not match lead customer."
                    )

        if "conversation_id" in values:
            conversation_id = values["conversation_id"]

            if conversation_id is not None:
                conversation = self.conversations.get(
                    organization_id,
                    conversation_id,
                )

                if (
                    conversation.customer_id
                    != interaction.customer_id
                ):
                    raise ValidationError(
                        "Interaction customer does not match "
                        "conversation customer."
                    )

        if "actor_user_id" in values:
            actor_user_id = values["actor_user_id"]

            if actor_user_id is not None:
                actor = self.users.get(actor_user_id)

                if (
                    actor is None
                    or actor.organization_id != organization_id
                ):
                    raise NotFoundError(
                        "Interaction actor not found."
                    )

        if (
            "external_message_id" in values
            and values["external_message_id"] is not None
        ):
            existing = (
                self.interactions.get_by_external_message_id(
                    organization_id,
                    interaction.channel,
                    values["external_message_id"],
                )
            )

            if (
                existing is not None
                and existing.id != interaction.id
            ):
                raise ConflictError(
                    "External message has already been processed."
                )

        try:
            self.interactions.update(
                interaction,
                **values,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "External message has already been processed."
            ) from exc
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(interaction)

        return interaction

    def update_embedding(
        self,
        organization_id: UUID,
        interaction_id: UUID,
        payload: InteractionEmbeddingUpdate,
    ) -> Interaction:
        """Persist a semantic-search embedding."""

        interaction = self.get(
            organization_id,
            interaction_id,
        )

        try:
            self.interactions.update(
                interaction,
                embedding=payload.embedding,
                embedding_model=payload.embedding_model,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(interaction)

        return interaction

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        conversation_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return filtered interactions for an organization."""

        return self.interactions.list_by_organization(
            organization_id,
            customer_id=customer_id,
            lead_id=lead_id,
            conversation_id=conversation_id,
            newest_first=True,
            offset=offset,
            limit=limit,
        )

    def list_by_conversation(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return a chronological conversation timeline."""

        self.conversations.get(
            organization_id,
            conversation_id,
        )

        return self.interactions.list_by_conversation(
            organization_id,
            conversation_id,
            newest_first=False,
            offset=offset,
            limit=limit,
        )

    def list_by_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Interaction]:
        """Return interaction history for a lead."""

        return self.interactions.list_by_lead(
            organization_id,
            lead_id,
            newest_first=True,
            offset=offset,
            limit=limit,
        )

    def semantic_search(
        self,
        organization_id: UUID,
        query_embedding: list[float],
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        limit: int = 20,
    ) -> list[tuple[Interaction, float]]:
        """Search interaction content using pgvector cosine similarity."""

        return self.interactions.semantic_search(
            organization_id,
            query_embedding,
            customer_id=customer_id,
            lead_id=lead_id,
            limit=limit,
        )
