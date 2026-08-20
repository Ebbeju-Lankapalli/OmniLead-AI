"""Follow-up scheduling business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.db.types import (
    FollowUpStatus,
    NotificationChannel,
    NotificationStatus,
)
from app.models.followup import FollowUp
from app.repositories.customers import CustomerRepository
from app.repositories.followups import FollowUpRepository
from app.repositories.leads import LeadRepository
from app.repositories.users import UserRepository
from app.schemas.followup import (
    FollowUpCompleteRequest,
    FollowUpCreate,
    FollowUpRescheduleRequest,
    FollowUpUpdate,
)
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService


class FollowUpService:
    """Business operations for sales follow-ups."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.followups = FollowUpRepository(db)
        self.leads = LeadRepository(db)
        self.customers = CustomerRepository(db)
        self.users = UserRepository(db)
        self.notifications = NotificationService(db)

    def get(
        self,
        organization_id: UUID,
        followup_id: UUID,
    ) -> FollowUp:
        """Return an organization-scoped follow-up."""

        followup = self.followups.get(followup_id)

        if (
            followup is None
            or followup.organization_id != organization_id
        ):
            raise NotFoundError(
                "Follow-up not found.",
                details={
                    "followup_id": str(followup_id),
                },
            )

        return followup

    def create(
        self,
        payload: FollowUpCreate,
    ) -> FollowUp:
        """Create a follow-up and reminder atomically."""

        lead = self._validate_relationships(
            payload.organization_id,
            payload.lead_id,
            payload.customer_id,
            payload.assigned_to_user_id,
            payload.created_by_user_id,
        )

        followup = FollowUp(
            **payload.model_dump()
        )

        try:
            self.followups.add(followup)
            self.db.flush()

            self._create_reminder(
                followup,
            )

            self._sync_lead_next_followup(
                lead,
            )

            self.db.commit()
            self.db.refresh(followup)

        except Exception:
            self.db.rollback()
            raise

        return followup

    def update(
        self,
        organization_id: UUID,
        followup_id: UUID,
        payload: FollowUpUpdate,
    ) -> FollowUp:
        """Update mutable follow-up fields."""

        followup = self.get(
            organization_id,
            followup_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return followup

        if "assigned_to_user_id" in values:
            user_id = values["assigned_to_user_id"]

            if user_id is None:
                raise ValidationError(
                    "Follow-up assignee cannot be null."
                )

            self._validate_user(
                organization_id,
                user_id,
            )

        try:
            self.followups.update(
                followup,
                **values,
            )
            self.db.flush()

            if (
                "scheduled_at" in values
                or "reminder_minutes_before" in values
                or "assigned_to_user_id" in values
            ):
                self.notifications.cancel_for_followup(
                    organization_id,
                    followup.id,
                    commit=False,
                )

                if followup.status == FollowUpStatus.SCHEDULED.value:
                    self._create_reminder(
                        followup,
                    )

            lead = self.leads.get(followup.lead_id)

            if lead is not None:
                self._sync_lead_next_followup(
                    lead,
                )

            self.db.commit()
            self.db.refresh(followup)

        except Exception:
            self.db.rollback()
            raise

        return followup

    def complete(
        self,
        organization_id: UUID,
        followup_id: UUID,
        payload: FollowUpCompleteRequest,
    ) -> FollowUp:
        """Mark a follow-up as completed."""

        followup = self.get(
            organization_id,
            followup_id,
        )

        if followup.status == FollowUpStatus.COMPLETED.value:
            return followup

        try:
            self.followups.update(
                followup,
                status=FollowUpStatus.COMPLETED.value,
                completed_at=payload.completed_at,
                outcome=payload.outcome,
                notes=payload.notes,
            )

            self.db.flush()

            self.notifications.cancel_for_followup(
                organization_id,
                followup.id,
                commit=False,
            )

            lead = self.leads.get(followup.lead_id)

            if lead is not None:
                self._sync_lead_next_followup(
                    lead,
                )

            self.db.commit()
            self.db.refresh(followup)

        except Exception:
            self.db.rollback()
            raise

        return followup

    def cancel(
        self,
        organization_id: UUID,
        followup_id: UUID,
    ) -> FollowUp:
        """Cancel a scheduled follow-up."""

        followup = self.get(
            organization_id,
            followup_id,
        )

        if followup.status == FollowUpStatus.CANCELLED.value:
            return followup

        try:
            self.followups.update(
                followup,
                status=FollowUpStatus.CANCELLED.value,
            )

            self.db.flush()

            self.notifications.cancel_for_followup(
                organization_id,
                followup.id,
                commit=False,
            )

            lead = self.leads.get(followup.lead_id)

            if lead is not None:
                self._sync_lead_next_followup(
                    lead,
                )

            self.db.commit()
            self.db.refresh(followup)

        except Exception:
            self.db.rollback()
            raise

        return followup

    def reschedule(
        self,
        organization_id: UUID,
        followup_id: UUID,
        payload: FollowUpRescheduleRequest,
    ) -> FollowUp:
        """Reschedule by preserving the original follow-up record."""

        original = self.get(
            organization_id,
            followup_id,
        )

        if original.status != FollowUpStatus.SCHEDULED.value:
            raise ValidationError(
                "Only scheduled follow-ups can be rescheduled."
            )

        assigned_to_user_id = (
            payload.assigned_to_user_id
            or original.assigned_to_user_id
        )

        self._validate_user(
            organization_id,
            assigned_to_user_id,
        )

        try:
            self.followups.update(
                original,
                status=FollowUpStatus.RESCHEDULED.value,
            )

            self.db.flush()

            self.notifications.cancel_for_followup(
                organization_id,
                original.id,
                commit=False,
            )

            replacement = FollowUp(
                organization_id=organization_id,
                lead_id=original.lead_id,
                customer_id=original.customer_id,
                assigned_to_user_id=assigned_to_user_id,
                created_by_user_id=original.created_by_user_id,
                followup_type=(
                    payload.followup_type.value
                    if payload.followup_type is not None
                    else original.followup_type
                ),
                scheduled_at=payload.scheduled_at,
                status=FollowUpStatus.SCHEDULED.value,
                reminder_minutes_before=(
                    payload.reminder_minutes_before
                    if payload.reminder_minutes_before is not None
                    else original.reminder_minutes_before
                ),
                notes=payload.notes,
                rescheduled_from_id=original.id,
            )

            self.followups.add(replacement)
            self.db.flush()

            self._create_reminder(
                replacement,
            )

            lead = self.leads.get(original.lead_id)

            if lead is not None:
                self._sync_lead_next_followup(
                    lead,
                )

            self.db.commit()
            self.db.refresh(original)
            self.db.refresh(replacement)

        except Exception:
            self.db.rollback()
            raise

        return replacement

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        status: FollowUpStatus | str | None = None,
        lead_id: UUID | None = None,
        customer_id: UUID | None = None,
        assigned_to_user_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return filtered follow-ups for an organization."""

        return self.followups.list_by_organization(
            organization_id,
            status=status,
            lead_id=lead_id,
            customer_id=customer_id,
            assigned_to_user_id=assigned_to_user_id,
            offset=offset,
            limit=limit,
        )

    def list_assigned_to(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return follow-ups assigned to a user."""

        return self.followups.list_assigned_to(
            organization_id,
            user_id,
            offset=offset,
            limit=limit,
        )

    def list_due(
        self,
        organization_id: UUID,
        *,
        due_at: datetime,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return scheduled follow-ups due by a timestamp."""

        return self.followups.list_due(
            organization_id,
            due_at=due_at,
            limit=limit,
        )

    def list_overdue(
        self,
        organization_id: UUID,
        *,
        now: datetime,
        limit: int = 100,
    ) -> Sequence[FollowUp]:
        """Return overdue follow-ups."""

        return self.followups.list_overdue(
            organization_id,
            now=now,
            limit=limit,
        )

    def _create_reminder(
        self,
        followup: FollowUp,
    ) -> None:
        """Create the pending reminder notification for a follow-up."""

        reminder_at = (
            followup.scheduled_at
            - timedelta(
                minutes=followup.reminder_minutes_before
            )
        )

        base_payload = {
            "organization_id": followup.organization_id,
            "user_id": followup.assigned_to_user_id,
            "lead_id": followup.lead_id,
            "followup_id": followup.id,
            "notification_type": "FOLLOWUP_REMINDER",
            "title": "Follow-up due soon",
            "message": (
                "You have an upcoming "
                f"{followup.followup_type.lower()} follow-up."
            ),
            "status": NotificationStatus.PENDING,
            "scheduled_for": reminder_at,
            "notification_metadata": {
                "followup_id": str(followup.id),
                "lead_id": str(followup.lead_id),
            },
        }

        self.notifications.create(
            NotificationCreate(
                **base_payload,
                channel=NotificationChannel.IN_APP,
            ),
            commit=False,
        )

        if settings.EMAIL_NOTIFICATIONS_ENABLED:
            self.notifications.create(
                NotificationCreate(
                    **base_payload,
                    channel=NotificationChannel.EMAIL,
                ),
                commit=False,
            )

    def _sync_lead_next_followup(
        self,
        lead,
    ) -> None:
        """Synchronize leads.next_followup_at from scheduled follow-ups."""

        next_followup = self.followups.get_next_for_lead(
            lead.organization_id,
            lead.id,
        )

        lead.next_followup_at = (
            next_followup.scheduled_at
            if next_followup is not None
            else None
        )

        self.db.flush()

    def _validate_relationships(
        self,
        organization_id: UUID,
        lead_id: UUID,
        customer_id: UUID,
        assigned_to_user_id: UUID,
        created_by_user_id: UUID | None,
    ):
        """Validate follow-up CRM relationships."""

        lead = self.leads.get(lead_id)

        if (
            lead is None
            or lead.organization_id != organization_id
        ):
            raise NotFoundError(
                "Lead not found."
            )

        customer = self.customers.get(customer_id)

        if (
            customer is None
            or customer.organization_id != organization_id
        ):
            raise NotFoundError(
                "Customer not found."
            )

        if lead.customer_id != customer_id:
            raise ValidationError(
                "Follow-up customer does not match lead customer."
            )

        self._validate_user(
            organization_id,
            assigned_to_user_id,
        )

        if created_by_user_id is not None:
            self._validate_user(
                organization_id,
                created_by_user_id,
            )

        return lead

    def _validate_user(
        self,
        organization_id: UUID,
        user_id: UUID,
    ):
        """Validate an active organization user."""

        user = self.users.get(user_id)

        if (
            user is None
            or user.organization_id != organization_id
        ):
            raise NotFoundError(
                "User not found.",
                details={
                    "user_id": str(user_id),
                },
            )

        if not user.is_active:
            raise ValidationError(
                "Inactive user cannot receive a follow-up.",
                details={
                    "user_id": str(user_id),
                },
            )

        return user
