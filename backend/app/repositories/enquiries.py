"""Enquiry repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.db.types import EnquiryStatus, LeadSource
from app.models.enquiry import Enquiry
from app.repositories.base import BaseRepository


class EnquiryRepository(BaseRepository[Enquiry]):
    """Data-access operations for incoming enquiries."""

    model = Enquiry

    def get_by_external_reference(
        self,
        organization_id: UUID,
        source: LeadSource | str,
        external_reference_id: str,
    ) -> Enquiry | None:
        """Return an enquiry by source and external reference ID."""

        normalized_reference = external_reference_id.strip()

        if not normalized_reference:
            return None

        normalized_source = (
            source.value
            if isinstance(source, LeadSource)
            else source.strip().upper().replace("-", "_").replace(" ", "_")
        )

        if not normalized_source:
            return None

        statement = select(Enquiry).where(
            Enquiry.organization_id == organization_id,
            Enquiry.source == normalized_source,
            Enquiry.external_reference_id == normalized_reference,
        )

        return self.db.scalar(statement)

    def external_reference_exists(
        self,
        organization_id: UUID,
        source: LeadSource | str,
        external_reference_id: str,
    ) -> bool:
        """Return whether an external enquiry reference already exists."""

        normalized_reference = external_reference_id.strip()

        if not normalized_reference:
            return False

        normalized_source = (
            source.value
            if isinstance(source, LeadSource)
            else source.strip().upper().replace("-", "_").replace(" ", "_")
        )

        if not normalized_source:
            return False

        statement = (
            select(Enquiry.id)
            .where(
                Enquiry.organization_id == organization_id,
                Enquiry.source == normalized_source,
                Enquiry.external_reference_id == normalized_reference,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status: EnquiryStatus | str | None = None,
        source: LeadSource | str | None = None,
        customer_id: UUID | None = None,
        received_from: datetime | None = None,
        received_to: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Enquiry]:
        """Return filtered enquiries for one organization."""

        statement = select(Enquiry).where(
            Enquiry.organization_id == organization_id
        )

        if status is not None:
            normalized_status = (
                status.value
                if isinstance(status, EnquiryStatus)
                else status.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_status:
                statement = statement.where(
                    Enquiry.status == normalized_status
                )

        if source is not None:
            normalized_source = (
                source.value
                if isinstance(source, LeadSource)
                else source.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_source:
                statement = statement.where(
                    Enquiry.source == normalized_source
                )

        if customer_id is not None:
            statement = statement.where(
                Enquiry.customer_id == customer_id
            )

        if received_from is not None:
            statement = statement.where(
                Enquiry.received_at >= received_from
            )

        if received_to is not None:
            statement = statement.where(
                Enquiry.received_at <= received_to
            )

        statement = (
            statement
            .order_by(
                Enquiry.received_at.desc(),
                Enquiry.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_needing_review(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Enquiry]:
        """Return enquiries waiting for human review."""

        return self.list_by_organization(
            organization_id,
            status=EnquiryStatus.NEEDS_REVIEW,
            offset=offset,
            limit=limit,
        )

    def list_new(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Enquiry]:
        """Return new unprocessed enquiries."""

        return self.list_by_organization(
            organization_id,
            status=EnquiryStatus.NEW,
            offset=offset,
            limit=limit,
        )

    def list_by_customer(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Enquiry]:
        """Return enquiry history for one customer."""

        return self.list_by_organization(
            organization_id,
            customer_id=customer_id,
            offset=offset,
            limit=limit,
        )
