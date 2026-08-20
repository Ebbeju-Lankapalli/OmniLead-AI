"""Conversation business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.conversation import Conversation
from app.repositories.conversations import ConversationRepository
from app.schemas.conversation import (
    ConversationCloseUpdate,
    ConversationCreate,
    ConversationLeadLinkUpdate,
    ConversationUpdate,
)
from app.services.customer_service import CustomerService
from app.services.lead_service import LeadService


class ConversationService:
    """Business operations for omnichannel conversations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = ConversationRepository(db)
        self.customers = CustomerService(db)
        self.leads = LeadService(db)

    def get(
        self,
        organization_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        """Return an organization-scoped conversation."""

        conversation = self.conversations.get(conversation_id)

        if (
            conversation is None
            or conversation.organization_id != organization_id
        ):
            raise NotFoundError(
                "Conversation not found.",
                details={
                    "conversation_id": str(conversation_id),
                },
            )

        return conversation

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        open_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Conversation]:
        """Return filtered conversations for an organization."""

        return self.conversations.list_by_organization(
            organization_id,
            customer_id=customer_id,
            lead_id=lead_id,
            open_only=open_only,
            offset=offset,
            limit=limit,
        )

    def create(
        self,
        payload: ConversationCreate,
        *,
        commit: bool = True,
    ) -> Conversation:
        """Create an omnichannel customer conversation."""

        self.customers.get(
            payload.organization_id,
            payload.customer_id,
        )

        if payload.lead_id is not None:
            lead = self.leads.get(
                payload.organization_id,
                payload.lead_id,
            )

            if lead.customer_id != payload.customer_id:
                raise ValidationError(
                    "Conversation customer does not match lead customer."
                )

        if payload.external_conversation_id is not None:
            existing = self.conversations.get_by_external_id(
                payload.organization_id,
                payload.channel,
                payload.external_conversation_id,
            )

            if existing is not None:
                raise ConflictError(
                    "External conversation already exists.",
                    details={
                        "conversation_id": str(existing.id),
                        "external_conversation_id": (
                            payload.external_conversation_id
                        ),
                    },
                )

        values = payload.model_dump()

        if values["started_at"] is None:
            values.pop("started_at")

        conversation = Conversation(**values)

        try:
            self.conversations.add(conversation)

            if commit:
                self.db.commit()
                self.db.refresh(conversation)
            else:
                self.db.flush()

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "External conversation already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return conversation

    def update(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        payload: ConversationUpdate,
    ) -> Conversation:
        """Update mutable conversation fields."""

        conversation = self.get(
            organization_id,
            conversation_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return conversation

        if "lead_id" in values:
            lead_id = values["lead_id"]

            if lead_id is not None:
                lead = self.leads.get(
                    organization_id,
                    lead_id,
                )

                if lead.customer_id != conversation.customer_id:
                    raise ValidationError(
                        "Conversation customer does not match lead customer."
                    )

        if (
            "external_conversation_id" in values
            and values["external_conversation_id"] is not None
        ):
            existing = self.conversations.get_by_external_id(
                organization_id,
                conversation.channel,
                values["external_conversation_id"],
            )

            if (
                existing is not None
                and existing.id != conversation.id
            ):
                raise ConflictError(
                    "External conversation already exists.",
                    details={
                        "conversation_id": str(existing.id),
                    },
                )

        try:
            self.conversations.update(
                conversation,
                **values,
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "External conversation already exists."
            ) from exc
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(conversation)

        return conversation

    def link_lead(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        payload: ConversationLeadLinkUpdate,
    ) -> Conversation:
        """Link or unlink a conversation from a lead."""

        conversation = self.get(
            organization_id,
            conversation_id,
        )

        if payload.lead_id is not None:
            lead = self.leads.get(
                organization_id,
                payload.lead_id,
            )

            if lead.customer_id != conversation.customer_id:
                raise ValidationError(
                    "Conversation customer does not match lead customer."
                )

        try:
            self.conversations.update(
                conversation,
                lead_id=payload.lead_id,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(conversation)

        return conversation

    def close(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        payload: ConversationCloseUpdate | None = None,
    ) -> Conversation:
        """Close a conversation."""

        conversation = self.get(
            organization_id,
            conversation_id,
        )

        closed_at = (
            payload.closed_at
            if payload is not None
            and payload.closed_at is not None
            else datetime.now().astimezone()
        )

        try:
            self.conversations.update(
                conversation,
                closed_at=closed_at,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(conversation)

        return conversation

    def reopen(
        self,
        organization_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        """Reopen a closed conversation."""

        conversation = self.get(
            organization_id,
            conversation_id,
        )

        try:
            self.conversations.update(
                conversation,
                closed_at=None,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(conversation)

        return conversation

    def touch_last_message(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        occurred_at: datetime,
        *,
        commit: bool = True,
    ) -> Conversation:
        """Advance the conversation's most recent-message timestamp."""

        conversation = self.get(
            organization_id,
            conversation_id,
        )

        if (
            conversation.last_message_at is None
            or occurred_at > conversation.last_message_at
        ):
            self.conversations.update(
                conversation,
                last_message_at=occurred_at,
            )

        try:
            self.db.flush()

            if commit:
                self.db.commit()
                self.db.refresh(conversation)
        except Exception:
            self.db.rollback()
            raise

        return conversation
