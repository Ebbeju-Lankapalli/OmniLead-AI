"""Lead repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.db.types import LeadSource, PurchaseIntent
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    """Data-access operations for sales leads."""

    model = Lead

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status_id: UUID | None = None,
        assigned_to_user_id: UUID | None = None,
        customer_id: UUID | None = None,
        product_id: UUID | None = None,
        source: LeadSource | str | None = None,
        purchase_intent: PurchaseIntent | str | None = None,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return filtered leads for one organization."""

        statement = select(Lead).where(
            Lead.organization_id == organization_id
        )

        if status_id is not None:
            statement = statement.where(
                Lead.status_id == status_id
            )

        if assigned_to_user_id is not None:
            statement = statement.where(
                Lead.assigned_to_user_id == assigned_to_user_id
            )

        if customer_id is not None:
            statement = statement.where(
                Lead.customer_id == customer_id
            )

        if product_id is not None:
            statement = statement.where(
                Lead.product_id == product_id
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
                    Lead.source == normalized_source
                )

        if purchase_intent is not None:
            normalized_intent = (
                purchase_intent.value
                if isinstance(purchase_intent, PurchaseIntent)
                else purchase_intent.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_intent:
                statement = statement.where(
                    Lead.purchase_intent == normalized_intent
                )

        if not include_archived:
            statement = statement.where(
                Lead.archived_at.is_(None)
            )

        statement = (
            statement
            .order_by(
                Lead.priority_score.desc().nullslast(),
                Lead.next_followup_at.asc().nullslast(),
                Lead.id,
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
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return lead history for one customer."""

        return self.list_by_organization(
            organization_id,
            customer_id=customer_id,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )

    def list_assigned_to(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return leads assigned to one team member."""

        return self.list_by_organization(
            organization_id,
            assigned_to_user_id=user_id,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )

    def list_unassigned(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return active leads without an assignee."""

        statement = (
            select(Lead)
            .where(
                Lead.organization_id == organization_id,
                Lead.assigned_to_user_id.is_(None),
                Lead.archived_at.is_(None),
            )
            .order_by(
                Lead.priority_score.desc().nullslast(),
                Lead.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_priority_queue(
        self,
        organization_id: UUID,
        *,
        minimum_priority_score: int = 0,
        limit: int = 50,
    ) -> Sequence[Lead]:
        """Return active leads ordered by highest priority."""

        bounded_score = min(max(minimum_priority_score, 0), 100)

        statement = (
            select(Lead)
            .where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
                Lead.priority_score.is_not(None),
                Lead.priority_score >= bounded_score,
            )
            .order_by(
                Lead.priority_score.desc(),
                Lead.followup_risk_score.desc().nullslast(),
                Lead.next_followup_at.asc().nullslast(),
                Lead.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_followups_due(
        self,
        organization_id: UUID,
        *,
        due_at: datetime,
        assigned_to_user_id: UUID | None = None,
        limit: int = 100,
    ) -> Sequence[Lead]:
        """Return active leads whose next follow-up is due."""

        statement = select(Lead).where(
            Lead.organization_id == organization_id,
            Lead.archived_at.is_(None),
            Lead.next_followup_at.is_not(None),
            Lead.next_followup_at <= due_at,
        )

        if assigned_to_user_id is not None:
            statement = statement.where(
                Lead.assigned_to_user_id == assigned_to_user_id
            )

        statement = (
            statement
            .order_by(
                Lead.next_followup_at.asc(),
                Lead.priority_score.desc().nullslast(),
                Lead.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def get_by_source_enquiry(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
    ) -> Lead | None:
        """Return the lead created from an enquiry, if any."""

        statement = select(Lead).where(
            Lead.organization_id == organization_id,
            Lead.source_enquiry_id == enquiry_id,
        )

        return self.db.scalar(statement)

    def get_status_by_key(
        self,
        organization_id: UUID,
        key: str,
    ) -> LeadStatus | None:
        """Return one organization-scoped lead status by key."""

        normalized_key = (
            key.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not normalized_key:
            return None

        statement = select(LeadStatus).where(
            LeadStatus.organization_id == organization_id,
            LeadStatus.key == normalized_key,
        )

        return self.db.scalar(statement)

    def list_statuses(
        self,
        organization_id: UUID,
        *,
        active_only: bool = True,
    ) -> Sequence[LeadStatus]:
        """Return lead lifecycle statuses in display order."""

        statement = select(LeadStatus).where(
            LeadStatus.organization_id == organization_id
        )

        if active_only:
            statement = statement.where(
                LeadStatus.is_active.is_(True)
            )

        statement = statement.order_by(
            LeadStatus.display_order,
            LeadStatus.name,
            LeadStatus.id,
        )

        return self.db.scalars(statement).all()

    def count_active(
        self,
        organization_id: UUID,
    ) -> int:
        """Return count of non-archived, non-terminal leads."""

        statement = (
            select(Lead.id)
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
                LeadStatus.is_terminal.is_(False),
            )
        )

        return len(self.db.scalars(statement).all())

    def count_converted(
        self,
        organization_id: UUID,
    ) -> int:
        """Return count of leads in a won status."""

        statement = (
            select(Lead.id)
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                LeadStatus.is_won.is_(True),
            )
        )

        return len(self.db.scalars(statement).all())
