"""Notification business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.db.types import NotificationStatus
from app.models.followup import FollowUp
from app.models.notification import Notification
from app.repositories.leads import LeadRepository
from app.repositories.notifications import NotificationRepository
from app.repositories.users import UserRepository
from app.schemas.notification import (
    NotificationCreate,
    NotificationReadUpdate,
    NotificationScheduleUpdate,
    NotificationStatusUpdate,
    NotificationUpdate,
)


class NotificationService:
    """Business operations for OmniLead AI notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.notifications = NotificationRepository(db)
        self.users = UserRepository(db)
        self.leads = LeadRepository(db)

    def get(
        self,
        organization_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        """Return an organization-scoped notification."""

        notification = self.notifications.get(notification_id)

        if (
            notification is None
            or notification.organization_id != organization_id
        ):
            raise NotFoundError(
                "Notification not found.",
                details={
                    "notification_id": str(notification_id),
                },
            )

        return notification

    def get_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        """Return a notification belonging to one organization user."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        if notification.user_id != user_id:
            raise NotFoundError(
                "Notification not found.",
                details={
                    "notification_id": str(notification_id),
                },
            )

        return notification

    def create(
        self,
        payload: NotificationCreate,
        *,
        commit: bool = True,
    ) -> Notification:
        """Create a validated notification."""

        user = self.users.get(payload.user_id)

        if (
            user is None
            or user.organization_id != payload.organization_id
        ):
            raise NotFoundError(
                "Notification user not found.",
                details={
                    "user_id": str(payload.user_id),
                },
            )

        if payload.lead_id is not None:
            lead = self.leads.get(payload.lead_id)

            if (
                lead is None
                or lead.organization_id != payload.organization_id
            ):
                raise NotFoundError(
                    "Notification lead not found.",
                    details={
                        "lead_id": str(payload.lead_id),
                    },
                )

        if payload.followup_id is not None:
            followup = self.db.get(
                FollowUp,
                payload.followup_id,
            )

            if (
                followup is None
                or followup.organization_id != payload.organization_id
            ):
                raise NotFoundError(
                    "Notification follow-up not found.",
                    details={
                        "followup_id": str(payload.followup_id),
                    },
                )

            if followup.assigned_to_user_id != payload.user_id:
                raise ValidationError(
                    "Reminder notification user must match "
                    "the follow-up assignee."
                )

            if (
                payload.lead_id is not None
                and followup.lead_id != payload.lead_id
            ):
                raise ValidationError(
                    "Notification lead does not match follow-up lead."
                )

        notification = Notification(
            **payload.model_dump()
        )

        try:
            self.notifications.add(notification)

            if commit:
                self.db.commit()
                self.db.refresh(notification)
            else:
                self.db.flush()

        except Exception:
            self.db.rollback()
            raise

        return notification

    def update(
        self,
        organization_id: UUID,
        notification_id: UUID,
        payload: NotificationUpdate,
    ) -> Notification:
        """Update mutable notification fields."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return notification

        try:
            self.notifications.update(
                notification,
                **values,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(notification)

        return notification

    def update_status(
        self,
        organization_id: UUID,
        notification_id: UUID,
        payload: NotificationStatusUpdate,
    ) -> Notification:
        """Update notification delivery state."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        values = {
            "status": payload.status.value,
        }

        if payload.sent_at is not None:
            values["sent_at"] = payload.sent_at

        try:
            self.notifications.update(
                notification,
                **values,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(notification)

        return notification

    def mark_read(
        self,
        organization_id: UUID,
        notification_id: UUID,
        payload: NotificationReadUpdate | None = None,
    ) -> Notification:
        """Mark a notification as read."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        read_at = (
            payload.read_at
            if payload is not None
            and payload.read_at is not None
            else datetime.now().astimezone()
        )

        try:
            self.notifications.update(
                notification,
                read_at=read_at,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(notification)

        return notification

    def mark_unread(
        self,
        organization_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        """Mark a notification as unread."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        try:
            self.notifications.update(
                notification,
                read_at=None,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(notification)

        return notification

    def mark_read_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        """Mark one notification belonging to a user as read."""

        notification = self.get_for_user(
            organization_id,
            user_id,
            notification_id,
        )

        try:
            self.notifications.update(
                notification,
                read_at=datetime.now().astimezone(),
            )
            self.db.commit()
            self.db.refresh(notification)

        except Exception:
            self.db.rollback()
            raise

        return notification

    def mark_unread_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        """Mark one notification belonging to a user as unread."""

        notification = self.get_for_user(
            organization_id,
            user_id,
            notification_id,
        )

        try:
            self.notifications.update(
                notification,
                read_at=None,
            )
            self.db.commit()
            self.db.refresh(notification)

        except Exception:
            self.db.rollback()
            raise

        return notification

    def mark_all_read(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> int:
        """Mark all unread notifications for a user as read."""

        notifications = self.notifications.list_unread(
            organization_id,
            user_id,
            offset=0,
            limit=1000,
        )

        if not notifications:
            return 0

        read_at = datetime.now().astimezone()

        try:
            for notification in notifications:
                notification.read_at = read_at

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return len(notifications)

    def reschedule(
        self,
        organization_id: UUID,
        notification_id: UUID,
        payload: NotificationScheduleUpdate,
    ) -> Notification:
        """Change a notification delivery schedule."""

        notification = self.get(
            organization_id,
            notification_id,
        )

        try:
            self.notifications.update(
                notification,
                scheduled_for=payload.scheduled_for,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(notification)

        return notification

    def list_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Return notifications for a user."""

        return self.notifications.list_by_user(
            organization_id,
            user_id,
            unread_only=unread_only,
            offset=offset,
            limit=limit,
        )

    def count_unread(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> int:
        """Return unread notification count."""

        return self.notifications.count_unread(
            organization_id,
            user_id,
        )

    def get_counts(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> tuple[int, int, int]:
        """Return total, unread, and pending notification counts."""

        total = self.notifications.count_total(
            organization_id,
            user_id,
        )

        unread = self.notifications.count_unread(
            organization_id,
            user_id,
        )

        pending = self.notifications.count_pending(
            organization_id,
            user_id,
        )

        return total, unread, pending

    def cancel_for_followup(
        self,
        organization_id: UUID,
        followup_id: UUID,
        *,
        commit: bool = True,
    ) -> int:
        """Cancel pending notifications associated with a follow-up."""

        notifications = self.notifications.list_by_followup(
            organization_id,
            followup_id,
            limit=100,
        )

        cancelled = 0

        try:
            for notification in notifications:
                if notification.status != NotificationStatus.PENDING.value:
                    continue

                notification.status = NotificationStatus.CANCELLED.value
                cancelled += 1

            self.db.flush()

            if commit:
                self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        return cancelled
