"""Celery tasks for scheduled OmniLead AI reminders."""

from __future__ import annotations

from datetime import UTC, datetime

from app.db.session import get_session_factory
from app.db.types import (
    NotificationChannel,
    NotificationStatus,
)
from app.models.followup import FollowUp
from app.repositories.notifications import NotificationRepository
from app.schemas.notification import NotificationStatusUpdate
from app.services.notification_service import NotificationService
from app.workers.celery_app import celery_app


@celery_app.task(
    name="omnilead.reminders.deliver_due",
)
def deliver_due_reminders(
    limit: int = 100,
) -> dict[str, object]:
    """
    Mark due in-app reminder notifications as delivered.

    External channels such as EMAIL are intentionally left for their
    dedicated delivery workers.
    """

    session_factory = get_session_factory()
    db = session_factory()

    try:
        now = datetime.now(UTC)

        repository = NotificationRepository(db)
        service = NotificationService(db)

        pending = repository.list_pending_delivery(
            due_at=now,
            limit=limit,
        )

        sent_ids: list[str] = []
        skipped_ids: list[str] = []

        for notification in pending:
            if (
                notification.channel
                != NotificationChannel.IN_APP.value
            ):
                skipped_ids.append(
                    str(notification.id)
                )
                continue

            service.update_status(
                notification.organization_id,
                notification.id,
                NotificationStatusUpdate(
                    status=NotificationStatus.SENT,
                    sent_at=now,
                ),
            )

            if notification.followup_id is not None:
                followup = db.get(
                    FollowUp,
                    notification.followup_id,
                )

                if followup is not None:
                    followup.reminder_sent_at = now
                    db.commit()

            sent_ids.append(
                str(notification.id)
            )

        return {
            "checked": len(pending),
            "sent": len(sent_ids),
            "skipped": len(skipped_ids),
            "sent_notification_ids": sent_ids,
            "skipped_notification_ids": skipped_ids,
            "processed_at": now.isoformat(),
        }

    finally:
        db.close()
