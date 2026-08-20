"""Lead assignment and ownership-history business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.lead import Lead
from app.models.lead_assignment import LeadAssignment
from app.models.lead_status import LeadStatus
from app.repositories.leads import LeadRepository
from app.repositories.users import UserRepository


class AssignmentService:
    """Manage lead ownership and assignment history."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.leads = LeadRepository(db)
        self.users = UserRepository(db)

    def assign(
        self,
        organization_id: UUID,
        lead_id: UUID,
        assigned_to_user_id: UUID,
        *,
        assigned_by_user_id: UUID | None = None,
        reason: str | None = None,
        commit: bool = True,
    ) -> Lead:
        """Assign or reassign a lead and preserve ownership history."""

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found.",
                details={
                    "lead_id": str(lead_id),
                },
            )

        assigned_to = self.users.get(assigned_to_user_id)

        if (
            assigned_to is None
            or assigned_to.organization_id != organization_id
        ):
            raise NotFoundError(
                "Assigned user not found.",
                details={
                    "user_id": str(assigned_to_user_id),
                },
            )

        if not assigned_to.is_active:
            raise ValidationError(
                "Lead cannot be assigned to an inactive user.",
                details={
                    "user_id": str(assigned_to_user_id),
                },
            )

        if assigned_by_user_id is not None:
            assigned_by = self.users.get(assigned_by_user_id)

            if (
                assigned_by is None
                or assigned_by.organization_id != organization_id
            ):
                raise NotFoundError(
                    "Assigning user not found.",
                    details={
                        "user_id": str(assigned_by_user_id),
                    },
                )

        current_user_id = lead.assigned_to_user_id

        if current_user_id == assigned_to_user_id:
            return lead

        now = datetime.now().astimezone()

        previous_assignment = self._get_open_assignment(
            organization_id,
            lead_id,
        )

        try:
            if previous_assignment is not None:
                previous_assignment.ended_at = now

            assignment = LeadAssignment(
                organization_id=organization_id,
                lead_id=lead_id,
                assigned_from_id=current_user_id,
                assigned_to_id=assigned_to_user_id,
                assigned_by_id=assigned_by_user_id,
                reason=self._normalize_reason(reason),
                assigned_at=now,
            )

            self.db.add(assignment)

            self.leads.update(
                lead,
                assigned_to_user_id=assigned_to_user_id,
            )

            self.db.flush()

            if commit:
                self.db.commit()
                self.db.refresh(lead)

        except Exception:
            self.db.rollback()
            raise

        return lead

    def auto_assign_least_loaded(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        reason: str | None = None,
        commit: bool = True,
    ) -> Lead:
        """
        Automatically assign an unowned lead to the least-loaded active
        SALES user in the organization.

        Existing ownership is preserved. If no active SALES user exists,
        the lead remains unassigned.
        """

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found.",
                details={
                    "lead_id": str(lead_id),
                },
            )

        if lead.assigned_to_user_id is not None:
            return lead

        sales_users = [
            user
            for user in self.users.list_active(
                organization_id,
                limit=1000,
            )
            if user.role == "SALES"
        ]

        if not sales_users:
            return lead

        workloads: list[tuple[int, str, str, UUID]] = []

        for user in sales_users:
            active_leads = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Lead)
                    .join(
                        LeadStatus,
                        Lead.status_id == LeadStatus.id,
                    )
                    .where(
                        Lead.organization_id == organization_id,
                        Lead.assigned_to_user_id == user.id,
                        Lead.archived_at.is_(None),
                        LeadStatus.is_terminal.is_(False),
                    )
                )
                or 0
            )

            workloads.append(
                (
                    active_leads,
                    user.full_name.casefold(),
                    str(user.id),
                    user.id,
                )
            )

        selected_user_id = min(
            workloads
        )[3]

        return self.assign(
            organization_id,
            lead_id,
            selected_user_id,
            reason=(
                reason
                or "Automatically assigned to least-loaded sales user."
            ),
            commit=commit,
        )

    def escalate_if_needed(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        now: datetime | None = None,
        minimum_priority_score: int = 80,
        minimum_followup_risk_score: int = 70,
        unassigned_grace_hours: int = 2,
        overdue_grace_hours: int = 4,
        commit: bool = True,
    ) -> Lead:
        """
        Escalate a risky lead to an active ADMIN when attention is overdue.

        Escalation occurs when at least one of these conditions is met:
        - a high-priority lead remains unassigned beyond the grace period;
        - an assigned lead is both high-priority and high follow-up risk;
        - a scheduled follow-up is overdue beyond the configured grace period.

        Existing ADMIN ownership is preserved.
        """

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found.",
                details={
                    "lead_id": str(lead_id),
                },
            )

        if lead.archived_at is not None:
            return lead

        if lead.status is not None and lead.status.is_terminal:
            return lead

        current_time = now or datetime.now(UTC)

        priority_score = lead.priority_score or 0
        followup_risk_score = lead.followup_risk_score or 0

        high_priority = (
            priority_score >= minimum_priority_score
        )

        high_risk = (
            followup_risk_score
            >= minimum_followup_risk_score
        )

        unassigned_too_long = False

        if (
            lead.assigned_to_user_id is None
            and high_priority
        ):
            created_at = lead.created_at

            if created_at is not None:
                unassigned_too_long = (
                    current_time - created_at
                    >= timedelta(
                        hours=unassigned_grace_hours
                    )
                )

        overdue_followup = False

        if lead.next_followup_at is not None:
            overdue_followup = (
                current_time - lead.next_followup_at
                >= timedelta(
                    hours=overdue_grace_hours
                )
            )

        should_escalate = (
            unassigned_too_long
            or (
                high_priority
                and high_risk
            )
            or (
                high_priority
                and overdue_followup
            )
        )

        if not should_escalate:
            return lead

        if lead.assigned_to_user_id is not None:
            current_owner = self.users.get(
                lead.assigned_to_user_id
            )

            if (
                current_owner is not None
                and current_owner.organization_id
                == organization_id
                and current_owner.is_active
                and current_owner.role == "ADMIN"
            ):
                return lead

        admins = [
            user
            for user in self.users.list_active(
                organization_id,
                limit=1000,
            )
            if user.role == "ADMIN"
        ]

        if not admins:
            return lead

        admin = min(
            admins,
            key=lambda user: (
                user.full_name.casefold(),
                str(user.id),
            ),
        )

        reasons: list[str] = []

        if unassigned_too_long:
            reasons.append(
                "high-priority lead remained unassigned"
            )

        if high_risk:
            reasons.append(
                "high follow-up risk"
            )

        if overdue_followup:
            reasons.append(
                "follow-up overdue"
            )

        reason = (
            "Automatic escalation to ADMIN: "
            + ", ".join(reasons)
            + "."
        )

        return self.assign(
            organization_id,
            lead_id,
            admin.id,
            reason=reason,
            commit=commit,
        )

    def unassign(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        commit: bool = True,
    ) -> Lead:
        """Remove the current owner while preserving assignment history."""

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found.",
                details={
                    "lead_id": str(lead_id),
                },
            )

        if lead.assigned_to_user_id is None:
            return lead

        previous_assignment = self._get_open_assignment(
            organization_id,
            lead_id,
        )

        try:
            if previous_assignment is not None:
                previous_assignment.ended_at = (
                    datetime.now().astimezone()
                )

            self.leads.update(
                lead,
                assigned_to_user_id=None,
            )

            self.db.flush()

            if commit:
                self.db.commit()
                self.db.refresh(lead)

        except Exception:
            self.db.rollback()
            raise

        return lead

    def get_current_assignment(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> LeadAssignment | None:
        """Return the currently open assignment-history record."""

        return self._get_open_assignment(
            organization_id,
            lead_id,
        )

    def list_history(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[LeadAssignment]:
        """Return ownership history for one lead."""

        statement = (
            select(LeadAssignment)
            .where(
                LeadAssignment.organization_id == organization_id,
                LeadAssignment.lead_id == lead_id,
            )
            .order_by(
                LeadAssignment.assigned_at.desc(),
                LeadAssignment.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def _get_open_assignment(
        self,
        organization_id: UUID,
        lead_id: UUID,
    ) -> LeadAssignment | None:
        """Return the latest assignment that has not ended."""

        statement = (
            select(LeadAssignment)
            .where(
                LeadAssignment.organization_id == organization_id,
                LeadAssignment.lead_id == lead_id,
                LeadAssignment.ended_at.is_(None),
            )
            .order_by(
                LeadAssignment.assigned_at.desc(),
                LeadAssignment.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    @staticmethod
    def _normalize_reason(
        reason: str | None,
    ) -> str | None:
        """Normalize an optional assignment reason."""

        if reason is None:
            return None

        cleaned = reason.strip()
        return cleaned or None
