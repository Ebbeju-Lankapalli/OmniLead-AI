"""Celery tasks for external notification delivery."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.config import settings
from app.db.session import get_session_factory
from app.db.types import (
    NotificationChannel,
    NotificationStatus,
)
from app.integrations.email.resend import ResendEmailClient
from app.repositories.notifications import NotificationRepository
from app.schemas.notification import NotificationStatusUpdate
from app.services.notification_service import NotificationService
from app.workers.celery_app import celery_app


@celery_app.task(
    name="omnilead.notifications.deliver_due_email",
)
def deliver_due_email_notifications(
    limit: int = 100,
) -> dict[str, object]:
    """Deliver due EMAIL notifications through Resend."""

    now = datetime.now(UTC)

    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return {
            "enabled": False,
            "checked": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "sent_notification_ids": [],
            "failed_notification_ids": [],
            "skipped_notification_ids": [],
            "processed_at": now.isoformat(),
            "reason": "EMAIL_NOTIFICATIONS_ENABLED is false.",
        }

    session_factory = get_session_factory()
    db = session_factory()

    try:
        repository = NotificationRepository(db)
        service = NotificationService(db)
        email_client = ResendEmailClient()

        pending = repository.list_pending_delivery(
            due_at=now,
            limit=limit,
        )

        sent_ids: list[str] = []
        failed_ids: list[str] = []
        skipped_ids: list[str] = []

        for notification in pending:
            if (
                notification.channel
                != NotificationChannel.EMAIL.value
            ):
                skipped_ids.append(
                    str(notification.id)
                )
                continue

            user = notification.user

            if (
                user is None
                or not user.email
                or not user.is_active
            ):
                service.update_status(
                    notification.organization_id,
                    notification.id,
                    NotificationStatusUpdate(
                        status=NotificationStatus.FAILED,
                    ),
                )

                failed_ids.append(
                    str(notification.id)
                )
                continue

            try:
                delivery = email_client.send(
                    to=user.email,
                    subject=notification.title,
                    text=notification.message,
                )

                metadata = dict(
                    notification.notification_metadata
                    or {}
                )

                metadata["email_provider"] = (
                    delivery.provider
                )

                if delivery.message_id is not None:
                    metadata["email_message_id"] = (
                        delivery.message_id
                    )

                notification.notification_metadata = (
                    metadata
                )

                db.flush()

                service.update_status(
                    notification.organization_id,
                    notification.id,
                    NotificationStatusUpdate(
                        status=NotificationStatus.SENT,
                        sent_at=now,
                    ),
                )

                sent_ids.append(
                    str(notification.id)
                )

            except Exception:
                db.rollback()

                notification = repository.get(
                    notification.id
                )

                if notification is not None:
                    service.update_status(
                        notification.organization_id,
                        notification.id,
                        NotificationStatusUpdate(
                            status=NotificationStatus.FAILED,
                        ),
                    )

                failed_ids.append(
                    str(notification.id)
                )

        return {
            "enabled": True,
            "checked": len(pending),
            "sent": len(sent_ids),
            "failed": len(failed_ids),
            "skipped": len(skipped_ids),
            "sent_notification_ids": sent_ids,
            "failed_notification_ids": failed_ids,
            "skipped_notification_ids": skipped_ids,
            "processed_at": now.isoformat(),
        }

    finally:
        db.close()
