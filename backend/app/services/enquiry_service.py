"""Enquiry business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.types import EnquiryStatus
from app.models.conversation import Conversation
from app.models.enquiry import Enquiry
from app.models.interaction import Interaction
from app.repositories.conversations import ConversationRepository
from app.repositories.enquiries import EnquiryRepository
from app.repositories.interactions import InteractionRepository
from app.schemas.enquiry import (
    EnquiryCreate,
    EnquiryLinkUpdate,
    EnquiryStatusUpdate,
    EnquiryUpdate,
)
from app.schemas.lead import LeadCreate
from app.services.customer_service import CustomerService
from app.services.lead_service import LeadService


class EnquiryService:
    """Business operations for raw omnichannel enquiries."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.enquiries = EnquiryRepository(db)
        self.conversations = ConversationRepository(db)
        self.interactions = InteractionRepository(db)
        self.customers = CustomerService(db)
        self.leads = LeadService(db)

    def get(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Enquiry:
        """Return an organization-scoped enquiry."""

        enquiry = self.enquiries.get(enquiry_id)

        if (
            enquiry is None
            or enquiry.organization_id != organization_id
        ):
            raise NotFoundError(
                "Enquiry not found.",
                details={
                    "enquiry_id": str(enquiry_id),
                },
            )

        return enquiry

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status: EnquiryStatus | str | None = None,
        source: str | None = None,
        customer_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Enquiry]:
        """Return filtered enquiries for one organization."""

        return self.enquiries.list_by_organization(
            organization_id,
            status=status,
            source=source,
            customer_id=customer_id,
            offset=offset,
            limit=limit,
        )

    def create(
        self,
        payload: EnquiryCreate,
    ) -> Enquiry:
        """Persist an incoming enquiry before downstream processing."""

        if payload.external_reference_id is not None:
            existing = self.enquiries.get_by_external_reference(
                payload.organization_id,
                payload.source,
                payload.external_reference_id,
            )

            if existing is not None:
                raise ConflictError(
                    "This external enquiry has already been received.",
                    details={
                        "enquiry_id": str(existing.id),
                        "external_reference_id": (
                            payload.external_reference_id
                        ),
                    },
                )

        if payload.customer_id is not None:
            self.customers.get(
                payload.organization_id,
                payload.customer_id,
            )

        if payload.conversation_id is not None:
            self._validate_conversation(
                payload.organization_id,
                payload.conversation_id,
            )

        if payload.interaction_id is not None:
            self._validate_interaction(
                payload.organization_id,
                payload.interaction_id,
            )

        values = payload.model_dump()

        if values["received_at"] is None:
            values.pop("received_at")

        enquiry = Enquiry(**values)

        try:
            self.enquiries.add(enquiry)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(enquiry)

        return enquiry

    def update(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        payload: EnquiryUpdate,
    ) -> Enquiry:
        """Update mutable enquiry processing fields."""

        enquiry = self.get(
            organization_id,
            enquiry_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return enquiry

        if "customer_id" in values:
            customer_id = values["customer_id"]

            if customer_id is not None:
                self.customers.get(
                    organization_id,
                    customer_id,
                )

        if "conversation_id" in values:
            conversation_id = values["conversation_id"]

            if conversation_id is not None:
                self._validate_conversation(
                    organization_id,
                    conversation_id,
                )

        if "interaction_id" in values:
            interaction_id = values["interaction_id"]

            if interaction_id is not None:
                self._validate_interaction(
                    organization_id,
                    interaction_id,
                )

        try:
            self.enquiries.update(
                enquiry,
                **values,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(enquiry)

        return enquiry

    def update_status(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        payload: EnquiryStatusUpdate,
    ) -> Enquiry:
        """Update only the enquiry processing status."""

        enquiry = self.get(
            organization_id,
            enquiry_id,
        )

        try:
            self.enquiries.update(
                enquiry,
                status=payload.status.value,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(enquiry)

        return enquiry

    def link(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        payload: EnquiryLinkUpdate,
    ) -> Enquiry:
        """Link an enquiry to resolved CRM records."""

        enquiry = self.get(
            organization_id,
            enquiry_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if "customer_id" in values:
            customer_id = values["customer_id"]

            if customer_id is not None:
                self.customers.get(
                    organization_id,
                    customer_id,
                )

        if "conversation_id" in values:
            conversation_id = values["conversation_id"]

            if conversation_id is not None:
                conversation = self._validate_conversation(
                    organization_id,
                    conversation_id,
                )

                customer_id = values.get(
                    "customer_id",
                    enquiry.customer_id,
                )

                if (
                    customer_id is not None
                    and conversation.customer_id != customer_id
                ):
                    raise ValidationError(
                        "Conversation customer does not match "
                        "the enquiry customer."
                    )

        if "interaction_id" in values:
            interaction_id = values["interaction_id"]

            if interaction_id is not None:
                interaction = self._validate_interaction(
                    organization_id,
                    interaction_id,
                )

                customer_id = values.get(
                    "customer_id",
                    enquiry.customer_id,
                )

                if (
                    customer_id is not None
                    and interaction.customer_id != customer_id
                ):
                    raise ValidationError(
                        "Interaction customer does not match "
                        "the enquiry customer."
                    )

        try:
            self.enquiries.update(
                enquiry,
                **values,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(enquiry)

        return enquiry

    def mark_ai_analyzed(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Enquiry:
        """Mark an enquiry as successfully AI analyzed."""

        return self.update_status(
            organization_id,
            enquiry_id,
            EnquiryStatusUpdate(
                status=EnquiryStatus.AI_ANALYZED,
            ),
        )

    def mark_needs_review(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Enquiry:
        """Send an enquiry to the human-review queue."""

        return self.update_status(
            organization_id,
            enquiry_id,
            EnquiryStatusUpdate(
                status=EnquiryStatus.NEEDS_REVIEW,
            ),
        )

    def mark_general_enquiry(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Enquiry:
        """Classify an enquiry as non-lead general enquiry."""

        return self.update_status(
            organization_id,
            enquiry_id,
            EnquiryStatusUpdate(
                status=EnquiryStatus.GENERAL_ENQUIRY,
            ),
        )

    def convert_to_lead(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        payload: LeadCreate,
        *,
        assigned_by_user_id: UUID | None = None,
        assignment_reason: str | None = None,
    ):
        """Convert an enquiry into a sales lead exactly once."""

        enquiry = self.get(
            organization_id,
            enquiry_id,
        )

        existing_lead = self.leads.leads.get_by_source_enquiry(
            organization_id,
            enquiry_id,
        )

        if existing_lead is not None:
            raise ConflictError(
                "This enquiry has already been converted to a lead.",
                details={
                    "lead_id": str(existing_lead.id),
                    "enquiry_id": str(enquiry_id),
                },
            )

        if payload.organization_id != organization_id:
            raise ValidationError(
                "Lead organization does not match enquiry organization."
            )

        if payload.source_enquiry_id != enquiry_id:
            raise ValidationError(
                "Lead source_enquiry_id must match the enquiry being converted."
            )

        if enquiry.customer_id is None:
            raise ValidationError(
                "Enquiry must be linked to a customer before conversion."
            )

        if payload.customer_id != enquiry.customer_id:
            raise ValidationError(
                "Lead customer must match the enquiry customer."
            )

        lead = self.leads.create(
            payload,
            assigned_by_user_id=assigned_by_user_id,
            assignment_reason=assignment_reason,
            commit=False,
        )

        try:
            self.enquiries.update(
                enquiry,
                status=EnquiryStatus.CONVERTED_TO_LEAD.value,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(enquiry)

        return lead

    def _validate_conversation(
        self,
        organization_id: UUID,
        conversation_id: UUID,
    ) -> Conversation:
        """Validate an organization-scoped conversation."""

        conversation = self.conversations.get(
            conversation_id
        )

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

    def _validate_interaction(
        self,
        organization_id: UUID,
        interaction_id: UUID,
    ) -> Interaction:
        """Validate an organization-scoped interaction."""

        interaction = self.interactions.get(
            interaction_id
        )

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
