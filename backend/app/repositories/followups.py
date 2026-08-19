"""Follow-up repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.db.types import FollowUpStatus, FollowUpType
from app.models.followup import FollowUp
from app.repositories.base import BaseRepository


class FollowUpRepository(BaseRepository[FollowUp]):
    """Data-access operations for scheduled sales follow-ups."""

    model = FollowUp

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status: FollowUpStatus | str | None = None,
        followup_type: FollowUpType | str | None = None,
        lead_id: UUID | None = None,
        customer_id: UUID | None = None,
        assigned_to_user_id: UUID | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return filtered follow-ups for one organization."""

        statement = select(FollowUp).where(
            FollowUp.organization_id == organization_id
        )

        if status is not None:
            normalized_status = (
                status.value
                if isinstance(status, FollowUpStatus)
                else status.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_status:
                statement = statement.where(
                    FollowUp.status == normalized_status
                )

        if followup_type is not None:
            normalized_type = (
                followup_type.value
                if isinstance(followup_type, FollowUpType)
                else followup_type.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_type:
                statement = statement.where(
                    FollowUp.followup_type == normalized_type
                )

        if lead_id is not None:
            statement = statement.where(
                FollowUp.lead_id == lead_id
            )

        if customer_id is not None:
            statement = statement.where(
                FollowUp.customer_id == customer_id
            )

        if assigned_to_user_id is not None:
            statement = statement.where(
                FollowUp.assigned_to_user_id == assigned_to_user_id
            )

        if scheduled_from is not None:
            statement = statement.where(
                FollowUp.scheduled_at >= scheduled_from
            )

        if scheduled_to is not None:
            statement = statement.where(
                FollowUp.scheduled_at <= scheduled_to
            )

        statement = (
            statement
            .order_by(
                FollowUp.scheduled_at.asc(),
                FollowUp.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_by_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return follow-up history for one lead."""

        return self.list_by_organization(
            organization_id,
            lead_id=lead_id,
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
    ) -> Sequence[FollowUp]:
        """Return follow-up history for one customer."""

        return self.list_by_organization(
            organization_id,
            customer_id=customer_id,
            offset=offset,
            limit=limit,
        )

    def list_assigned_to(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        status: FollowUpStatus | str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return follow-ups assigned to a team member."""

        return self.list_by_organization(
            organization_id,
            status=status,
            assigned_to_user_id=user_id,
            offset=offset,
            limit=limit,
        )

    def list_due(
        self,
        organization_id: UUID,
        *,
        due_at: datetime,
        assigned_to_user_id: UUID | None = None,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return scheduled follow-ups due on or before a timestamp."""

        statement = select(FollowUp).where(
            FollowUp.organization_id == organization_id,
            FollowUp.status == FollowUpStatus.SCHEDULED.value,
            FollowUp.scheduled_at <= due_at,
        )

        if assigned_to_user_id is not None:
            statement = statement.where(
                FollowUp.assigned_to_user_id == assigned_to_user_id
            )

        statement = (
            statement
            .order_by(
                FollowUp.scheduled_at.asc(),
                FollowUp.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_overdue(
        self,
        organization_id: UUID,
        *,
        now: datetime,
        assigned_to_user_id: UUID | None = None,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return scheduled follow-ups whose scheduled time has passed."""

        return self.list_due(
            organization_id,
            due_at=now,
            assigned_to_user_id=assigned_to_user_id,
            limit=limit,
        )

    def list_due_between(
        self,
        organization_id: UUID,
        *,
        start: datetime,
        end: datetime,
        assigned_to_user_id: UUID | None = None,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return scheduled follow-ups within a time window."""

        statement = select(FollowUp).where(
            FollowUp.organization_id == organization_id,
            FollowUp.status == FollowUpStatus.SCHEDULED.value,
            FollowUp.scheduled_at >= start,
            FollowUp.scheduled_at <= end,
        )

        if assigned_to_user_id is not None:
            statement = statement.where(
                FollowUp.assigned_to_user_id == assigned_to_user_id
            )

        statement = (
            statement
            .order_by(
                FollowUp.scheduled_at.asc(),
                FollowUp.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_reminder_due(
        self,
        organization_id: UUID,
        *,
        now: datetime,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """
        Return scheduled follow-ups whose reminder window has been reached.

        Reminder due time is calculated as:
        scheduled_at - reminder_minutes_before.
        """

        candidates = self.db.scalars(
            select(FollowUp)
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.status == FollowUpStatus.SCHEDULED.value,
                FollowUp.reminder_sent_at.is_(None),
                FollowUp.scheduled_at >= now,
            )
            .order_by(
                FollowUp.scheduled_at.asc(),
                FollowUp.id,
            )
            .limit(max(limit * 5, limit))
        ).all()

        due: list[FollowUp] = []

        for followup in candidates:
            reminder_at = followup.scheduled_at - timedelta(
                minutes=followup.reminder_minutes_before
            )

            if reminder_at <= now:
                due.append(followup)

            if len(due) >= limit:
                break

        return due

    def get_next_for_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> FollowUp | None:
        """Return the next scheduled follow-up for a lead."""

        statement = (
            select(FollowUp)
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.lead_id == lead_id,
                FollowUp.status == FollowUpStatus.SCHEDULED.value,
            )
            .order_by(
                FollowUp.scheduled_at.asc(),
                FollowUp.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def get_latest_for_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> FollowUp | None:
        """Return the most recently scheduled follow-up for a lead."""

        statement = (
            select(FollowUp)
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.lead_id == lead_id,
            )
            .order_by(
                FollowUp.scheduled_at.desc(),
                FollowUp.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)
