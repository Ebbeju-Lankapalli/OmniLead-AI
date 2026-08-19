"""Notification repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select

from app.db.types import NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data-access operations for user notifications."""

    model = Notification

    def list_by_user(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        status: NotificationStatus | str | None = None,
        channel: NotificationChannel | str | None = None,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Return notifications for one user."""

        statement = select(Notification).where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
        )

        if status is not None:
            normalized_status = (
                status.value
                if isinstance(status, NotificationStatus)
                else status.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_status:
                statement = statement.where(
                    Notification.status == normalized_status
                )

        if channel is not None:
            normalized_channel = (
                channel.value
                if isinstance(channel, NotificationChannel)
                else channel.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_channel:
                statement = statement.where(
                    Notification.channel == normalized_channel
                )

        if unread_only:
            statement = statement.where(
                Notification.read_at.is_(None)
            )

        statement = (
            statement
            .order_by(
                Notification.created_at.desc(),
                Notification.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_unread(
        self,
        organization_id: UUID,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Return unread notifications for one user."""

        return self.list_by_user(
            organization_id,
            user_id,
            unread_only=True,
            offset=offset,
            limit=limit,
        )

    def count_unread(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> int:
        """Return unread notification count for one user."""

        statement = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )

        return int(self.db.scalar(statement) or 0)

    def list_pending_delivery(
        self,
        *,
        due_at: datetime,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Return pending notifications ready for delivery."""

        statement = (
            select(Notification)
            .where(
                Notification.status == NotificationStatus.PENDING.value,
                (
                    Notification.scheduled_for.is_(None)
                    | (Notification.scheduled_for <= due_at)
                ),
            )
            .order_by(
                Notification.scheduled_for.asc().nullsfirst(),
                Notification.created_at.asc(),
                Notification.id,
            )
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
    ) -> Sequence[Notification]:
        """Return notifications linked to a lead."""

        statement = (
            select(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.lead_id == lead_id,
            )
            .order_by(
                Notification.created_at.desc(),
                Notification.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_by_followup(
        self,
        organization_id: UUID,
        followup_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Notification]:
        """Return notifications linked to a follow-up."""

        statement = (
            select(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.followup_id == followup_id,
            )
            .order_by(
                Notification.created_at.desc(),
                Notification.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def get_latest_for_user(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        """Return the newest notification for one user."""

        statement = (
            select(Notification)
            .where(
                Notification.organization_id == organization_id,
                Notification.user_id == user_id,
            )
            .order_by(
                Notification.created_at.desc(),
                Notification.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)
