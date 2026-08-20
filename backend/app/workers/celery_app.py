"""Celery application configuration for OmniLead AI."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "omnilead_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.embedding_tasks",
        "app.workers.tasks.ai_tasks",
        "app.workers.tasks.assignment_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.reminder_tasks",
        "app.workers.tasks.transcription_tasks",
        "app.workers.tasks.webhook_tasks",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "escalate-risky-leads-every-five-minutes": {
            "task": "omnilead.assignments.escalate_due",
            "schedule": 300.0,
            "args": (),
        },
        "deliver-due-reminders-every-minute": {
            "task": "omnilead.reminders.deliver_due",
            "schedule": 60.0,
            "args": (100,),
        },
        "deliver-due-email-notifications-every-minute": {
            "task": "omnilead.notifications.deliver_due_email",
            "schedule": 60.0,
            "args": (100,),
        },
    },
)


@celery_app.task(
    name="omnilead.health_check",
)
def celery_health_check() -> dict[str, str]:
    """Return a lightweight worker health response."""

    return {
        "status": "ok",
        "service": "OmniLead AI Celery",
    }
