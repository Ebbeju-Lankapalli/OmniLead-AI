"""Authenticated notification API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.notification import (
    NotificationCountResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def list_notifications(
    current_user: CurrentUser,
    db: DatabaseSession,
    unread_only: bool = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[NotificationResponse]:
    """Return notifications belonging to the authenticated user."""

    notifications = NotificationService(
        db
    ).list_for_user(
        current_user.organization_id,
        current_user.id,
        unread_only=unread_only,
        offset=offset,
        limit=limit,
    )

    return [
        NotificationResponse.model_validate(
            notification
        )
        for notification in notifications
    ]


@router.get(
    "/unread",
    response_model=list[NotificationResponse],
)
def list_unread_notifications(
    current_user: CurrentUser,
    db: DatabaseSession,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[NotificationResponse]:
    """Return unread notifications for the authenticated user."""

    notifications = NotificationService(
        db
    ).list_for_user(
        current_user.organization_id,
        current_user.id,
        unread_only=True,
        offset=offset,
        limit=limit,
    )

    return [
        NotificationResponse.model_validate(
            notification
        )
        for notification in notifications
    ]


@router.get(
    "/counts",
    response_model=NotificationCountResponse,
)
def notification_counts(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationCountResponse:
    """Return header notification counters."""

    total, unread, pending = NotificationService(
        db
    ).get_counts(
        current_user.organization_id,
        current_user.id,
    )

    return NotificationCountResponse(
        total=total,
        unread=unread,
        pending=pending,
    )


@router.post(
    "/read-all",
    response_model=NotificationCountResponse,
)
def mark_all_notifications_read(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationCountResponse:
    """Mark all notifications belonging to the user as read."""

    service = NotificationService(db)

    service.mark_all_read(
        current_user.organization_id,
        current_user.id,
    )

    total, unread, pending = service.get_counts(
        current_user.organization_id,
        current_user.id,
    )

    return NotificationCountResponse(
        total=total,
        unread=unread,
        pending=pending,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationResponse:
    """Return one notification belonging to the authenticated user."""

    notification = NotificationService(
        db
    ).get_for_user(
        current_user.organization_id,
        current_user.id,
        notification_id,
    )

    return NotificationResponse.model_validate(
        notification
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationResponse:
    """Mark one notification as read."""

    notification = NotificationService(
        db
    ).mark_read_for_user(
        current_user.organization_id,
        current_user.id,
        notification_id,
    )

    return NotificationResponse.model_validate(
        notification
    )


@router.post(
    "/{notification_id}/unread",
    response_model=NotificationResponse,
)
def mark_notification_unread(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> NotificationResponse:
    """Mark one notification as unread."""

    notification = NotificationService(
        db
    ).mark_unread_for_user(
        current_user.organization_id,
        current_user.id,
        notification_id,
    )

    return NotificationResponse.model_validate(
        notification
    )
