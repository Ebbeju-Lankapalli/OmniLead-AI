"""Follow-up management API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.db.types import FollowUpStatus
from app.schemas.followup import (
    FollowUpCompleteRequest,
    FollowUpCreate,
    FollowUpCreateRequest,
    FollowUpPatchRequest,
    FollowUpRescheduleRequest,
    FollowUpResponse,
    FollowUpUpdate,
)
from app.services.followup_service import FollowUpService

router = APIRouter(
    prefix="/followups",
    tags=["followups"],
)


@router.get(
    "",
    response_model=list[FollowUpResponse],
)
def list_followups(
    current_user: CurrentUser,
    db: DatabaseSession,
    status: FollowUpStatus | None = None,
    lead_id: UUID | None = None,
    customer_id: UUID | None = None,
    assigned_to_user_id: UUID | None = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[FollowUpResponse]:
    """Return organization-scoped follow-ups."""

    followups = FollowUpService(
        db
    ).list_by_organization(
        current_user.organization_id,
        status=status,
        lead_id=lead_id,
        customer_id=customer_id,
        assigned_to_user_id=assigned_to_user_id,
        offset=offset,
        limit=limit,
    )

    return [
        FollowUpResponse.model_validate(followup)
        for followup in followups
    ]


@router.get(
    "/assigned-to-me",
    response_model=list[FollowUpResponse],
)
def assigned_to_me(
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
) -> list[FollowUpResponse]:
    """Return follow-ups assigned to the authenticated user."""

    followups = FollowUpService(
        db
    ).list_assigned_to(
        current_user.organization_id,
        current_user.id,
        offset=offset,
        limit=limit,
    )

    return [
        FollowUpResponse.model_validate(followup)
        for followup in followups
    ]


@router.get(
    "/due",
    response_model=list[FollowUpResponse],
)
def due_followups(
    current_user: CurrentUser,
    db: DatabaseSession,
    due_at: datetime,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[FollowUpResponse]:
    """Return scheduled follow-ups due by a timestamp."""

    followups = FollowUpService(
        db
    ).list_due(
        current_user.organization_id,
        due_at=due_at,
        limit=limit,
    )

    return [
        FollowUpResponse.model_validate(followup)
        for followup in followups
    ]


@router.get(
    "/overdue",
    response_model=list[FollowUpResponse],
)
def overdue_followups(
    current_user: CurrentUser,
    db: DatabaseSession,
    now: datetime,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[FollowUpResponse]:
    """Return scheduled follow-ups whose time has passed."""

    followups = FollowUpService(
        db
    ).list_overdue(
        current_user.organization_id,
        now=now,
        limit=limit,
    )

    return [
        FollowUpResponse.model_validate(followup)
        for followup in followups
    ]


@router.post(
    "",
    response_model=FollowUpResponse,
    status_code=201,
)
def create_followup(
    payload: FollowUpCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Create a follow-up and its reminder notification."""

    followup = FollowUpService(
        db
    ).create(
        FollowUpCreate(
            organization_id=current_user.organization_id,
            created_by_user_id=current_user.id,
            status=FollowUpStatus.SCHEDULED,
            **payload.model_dump(),
        )
    )

    return FollowUpResponse.model_validate(
        followup
    )


@router.get(
    "/{followup_id}",
    response_model=FollowUpResponse,
)
def get_followup(
    followup_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Return one organization-scoped follow-up."""

    followup = FollowUpService(
        db
    ).get(
        current_user.organization_id,
        followup_id,
    )

    return FollowUpResponse.model_validate(
        followup
    )


@router.patch(
    "/{followup_id}",
    response_model=FollowUpResponse,
)
def update_followup(
    followup_id: UUID,
    payload: FollowUpPatchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Update safe mutable fields of a follow-up."""

    followup = FollowUpService(
        db
    ).update(
        current_user.organization_id,
        followup_id,
        FollowUpUpdate(
            **payload.model_dump(
                exclude_unset=True,
            )
        ),
    )

    return FollowUpResponse.model_validate(
        followup
    )


@router.post(
    "/{followup_id}/complete",
    response_model=FollowUpResponse,
)
def complete_followup(
    followup_id: UUID,
    payload: FollowUpCompleteRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Mark a follow-up as completed."""

    followup = FollowUpService(
        db
    ).complete(
        current_user.organization_id,
        followup_id,
        payload,
    )

    return FollowUpResponse.model_validate(
        followup
    )


@router.post(
    "/{followup_id}/cancel",
    response_model=FollowUpResponse,
)
def cancel_followup(
    followup_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Cancel a scheduled follow-up."""

    followup = FollowUpService(
        db
    ).cancel(
        current_user.organization_id,
        followup_id,
    )

    return FollowUpResponse.model_validate(
        followup
    )


@router.post(
    "/{followup_id}/reschedule",
    response_model=FollowUpResponse,
    status_code=201,
)
def reschedule_followup(
    followup_id: UUID,
    payload: FollowUpRescheduleRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> FollowUpResponse:
    """Reschedule while preserving the original record."""

    replacement = FollowUpService(
        db
    ).reschedule(
        current_user.organization_id,
        followup_id,
        payload,
    )

    return FollowUpResponse.model_validate(
        replacement
    )
