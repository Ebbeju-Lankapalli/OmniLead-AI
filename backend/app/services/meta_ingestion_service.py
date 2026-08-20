"""Atomic Meta webhook ingestion into the OmniLead AI CRM."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.types import (
    EnquiryStatus,
    InteractionDirection,
    InteractionType,
)
from app.integrations.meta.normalizer import NormalizedMetaMessage
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.enquiry import Enquiry
from app.models.interaction import Interaction
from app.repositories.conversations import ConversationRepository
from app.repositories.enquiries import EnquiryRepository
from app.repositories.interactions import InteractionRepository
from app.services.identity_resolution_service import (
    IdentityResolutionService,
)


@dataclass(frozen=True, slots=True)
class MetaIngestionResult:
    """CRM records produced from one normalized Meta message."""

    customer: Customer
    conversation: Conversation
    interaction: Interaction
    enquiry: Enquiry

    customer_created: bool
    conversation_created: bool
    interaction_created: bool
    enquiry_created: bool

    duplicate: bool


class MetaIngestionService:
    """
    Persist normalized Meta messages into the OmniLead CRM.

    One inbound message is mapped to:

    Customer
        -> Conversation
        -> Interaction
        -> Enquiry

    The complete new-message ingestion path is committed atomically.
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

        self.identities = IdentityResolutionService(
            db
        )
        self.conversations = ConversationRepository(
            db
        )
        self.interactions = InteractionRepository(
            db
        )
        self.enquiries = EnquiryRepository(
            db
        )

    def ingest(
        self,
        organization_id: UUID,
        message: NormalizedMetaMessage,
    ) -> MetaIngestionResult:
        """Persist one normalized inbound Meta message."""

        existing_interaction = (
            self.interactions.get_by_external_message_id(
                organization_id,
                message.channel,
                message.external_message_id,
            )
        )

        if existing_interaction is not None:
            return self._build_duplicate_result(
                organization_id,
                message,
                existing_interaction,
            )

        customer_created = False
        conversation_created = False
        interaction_created = False
        enquiry_created = False

        try:
            customer = self.identities.resolve(
                organization_id,
                message.sender_identity_type,
                message.sender_identity_value,
            )

            if customer is None:
                customer = self._create_customer(
                    organization_id,
                    message,
                )
                customer_created = True

            else:
                self._enrich_customer(
                    customer,
                    message,
                )

            conversation = (
                self.conversations.get_by_external_id(
                    organization_id,
                    message.channel,
                    message.external_conversation_id,
                )
            )

            if conversation is None:
                conversation = Conversation(
                    organization_id=organization_id,
                    customer_id=customer.id,
                    channel=message.channel.value,
                    external_conversation_id=(
                        message.external_conversation_id
                    ),
                    title=self._conversation_title(
                        message
                    ),
                    started_at=message.occurred_at,
                    last_message_at=message.occurred_at,
                    conversation_metadata={
                        "provider": "META",
                        "recipient_external_id": (
                            message.recipient_external_id
                        ),
                    },
                )

                self.db.add(conversation)
                self.db.flush()

                conversation_created = True

            else:
                if (
                    conversation.customer_id
                    != customer.id
                ):
                    raise ValueError(
                        "Meta conversation identity resolved "
                        "to a different customer."
                    )

                if (
                    conversation.last_message_at is None
                    or message.occurred_at
                    > conversation.last_message_at
                ):
                    conversation.last_message_at = (
                        message.occurred_at
                    )

            interaction = Interaction(
                organization_id=organization_id,
                customer_id=customer.id,
                conversation_id=conversation.id,
                interaction_type=(
                    InteractionType.MESSAGE.value
                ),
                direction=(
                    InteractionDirection.INBOUND.value
                ),
                channel=message.channel.value,
                content=message.message_text,
                external_message_id=(
                    message.external_message_id
                ),
                occurred_at=message.occurred_at,
                interaction_metadata=(
                    self._interaction_metadata(
                        message
                    )
                ),
            )

            self.db.add(interaction)
            self.db.flush()

            interaction_created = True

            enquiry = Enquiry(
                organization_id=organization_id,
                customer_id=customer.id,
                conversation_id=conversation.id,
                interaction_id=interaction.id,
                source=message.source.value,
                original_source=message.source.value,
                external_reference_id=(
                    message.external_message_id
                ),
                customer_name_raw=message.sender_name,
                contact_raw=(
                    message.sender_identity_value
                ),
                message_text=message.message_text,
                status=EnquiryStatus.NEW.value,
                received_at=message.occurred_at,
                campaign_id=message.campaign_id,
                ad_id=message.ad_id,
                ad_name=message.ad_name,
                enquiry_metadata=(
                    self._enquiry_metadata(
                        message
                    )
                ),
            )

            self.db.add(enquiry)
            self.db.flush()

            enquiry_created = True

            if (
                message.occurred_at
                > customer.last_seen_at
            ):
                customer.last_seen_at = (
                    message.occurred_at
                )

            self.db.commit()

        except IntegrityError:
            self.db.rollback()

            existing_interaction = (
                self.interactions
                .get_by_external_message_id(
                    organization_id,
                    message.channel,
                    message.external_message_id,
                )
            )

            if existing_interaction is not None:
                return self._build_duplicate_result(
                    organization_id,
                    message,
                    existing_interaction,
                )

            raise

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)
        self.db.refresh(conversation)
        self.db.refresh(interaction)
        self.db.refresh(enquiry)

        return MetaIngestionResult(
            customer=customer,
            conversation=conversation,
            interaction=interaction,
            enquiry=enquiry,
            customer_created=customer_created,
            conversation_created=(
                conversation_created
            ),
            interaction_created=(
                interaction_created
            ),
            enquiry_created=enquiry_created,
            duplicate=False,
        )

    def _create_customer(
        self,
        organization_id: UUID,
        message: NormalizedMetaMessage,
    ) -> Customer:
        """Create a unified customer for a new Meta identity."""

        primary_phone = None

        if (
            message.sender_identity_type
            == "WHATSAPP"
        ):
            primary_phone = (
                self.identities
                .normalize_identity_value(
                    "WHATSAPP",
                    message.sender_identity_value,
                )
            )

        customer = Customer(
            organization_id=organization_id,
            full_name=message.sender_name,
            primary_phone=primary_phone,
            first_seen_at=message.occurred_at,
            last_seen_at=message.occurred_at,
        )

        self.db.add(customer)
        self.db.flush()

        self.identities.add_identity(
            organization_id,
            customer.id,
            identity_type=(
                message.sender_identity_type
            ),
            identity_value=(
                message.sender_identity_value
            ),
            display_value=(
                message.sender_identity_value
            ),
            is_primary=True,
            is_verified=True,
            source="META",
            metadata={
                "channel": message.channel.value,
            },
            commit=False,
        )

        return customer

    @staticmethod
    def _enrich_customer(
        customer: Customer,
        message: NormalizedMetaMessage,
    ) -> None:
        """Fill safe missing customer information from Meta."""

        if (
            not customer.full_name
            and message.sender_name
        ):
            customer.full_name = (
                message.sender_name
            )

    def _build_duplicate_result(
        self,
        organization_id: UUID,
        message: NormalizedMetaMessage,
        interaction: Interaction,
    ) -> MetaIngestionResult:
        """Return the CRM records created by an earlier delivery."""

        conversation = (
            interaction.conversation
        )

        if conversation is None:
            conversation = (
                self.conversations.get(
                    interaction.conversation_id
                )
                if interaction.conversation_id
                is not None
                else None
            )

        if conversation is None:
            raise RuntimeError(
                "Duplicate Meta interaction has no "
                "associated conversation."
            )

        customer = interaction.customer

        enquiry = (
            self.enquiries
            .get_by_external_reference(
                organization_id,
                message.source,
                message.external_message_id,
            )
        )

        if enquiry is None:
            raise RuntimeError(
                "Duplicate Meta interaction has no "
                "associated enquiry."
            )

        return MetaIngestionResult(
            customer=customer,
            conversation=conversation,
            interaction=interaction,
            enquiry=enquiry,
            customer_created=False,
            conversation_created=False,
            interaction_created=False,
            enquiry_created=False,
            duplicate=True,
        )

    @staticmethod
    def _conversation_title(
        message: NormalizedMetaMessage,
    ) -> str | None:
        """Build a useful inbox title."""

        if message.sender_name:
            return (
                f"{message.sender_name} · "
                f"{message.channel.value.title()}"
            )

        return None

    @staticmethod
    def _interaction_metadata(
        message: NormalizedMetaMessage,
    ) -> dict:
        """Build interaction metadata without losing provider context."""

        return {
            **message.metadata,
            "provider": "META",
            "source": message.source.value,
            "recipient_external_id": (
                message.recipient_external_id
            ),
            "campaign_id": message.campaign_id,
            "ad_id": message.ad_id,
            "ad_name": message.ad_name,
        }

    @staticmethod
    def _enquiry_metadata(
        message: NormalizedMetaMessage,
    ) -> dict:
        """Build raw-enquiry metadata."""

        return {
            "provider": "META",
            "channel": message.channel.value,
            "identity_type": (
                message.sender_identity_type
            ),
            "recipient_external_id": (
                message.recipient_external_id
            ),
            "normalized_message_metadata": (
                message.metadata
            ),
        }
