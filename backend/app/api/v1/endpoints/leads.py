"""Lead-management API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.lead import (
    LeadAssignmentUpdate,
    LeadCreate,
    LeadCreateRequest,
    LeadResponse,
    LeadStatusResponse,
    LeadStatusUpdate,
    LeadUpdate,
)
from app.services.lead_service import LeadService
from app.services.lead_status_service import LeadStatusService

router = APIRouter(
    prefix="/leads",
    tags=["leads"],
)


@router.get(
    "/priority-queue",
    response_model=list[LeadResponse],
)
def priority_queue(
    current_user: CurrentUser,
    db: DatabaseSession,
    minimum_priority_score: Annotated[
        int,
        Query(ge=0, le=100),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 50,
) -> list[LeadResponse]:
    """Return highest-priority active leads."""

    leads = LeadService(
        db
    ).list_priority_queue(
        current_user.organization_id,
        minimum_priority_score=minimum_priority_score,
        limit=limit,
    )

    return [
        LeadResponse.model_validate(lead)
        for lead in leads
    ]


@router.get(
    "",
    response_model=list[LeadResponse],
)
def list_leads(
    current_user: CurrentUser,
    db: DatabaseSession,
    status_id: UUID | None = None,
    assigned_to_user_id: UUID | None = None,
    customer_id: UUID | None = None,
    product_id: UUID | None = None,
    include_archived: bool = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[LeadResponse]:
    """Return organization-scoped leads."""

    leads = LeadService(
        db
    ).list_by_organization(
        current_user.organization_id,
        status_id=status_id,
        assigned_to_user_id=assigned_to_user_id,
        customer_id=customer_id,
        product_id=product_id,
        include_archived=include_archived,
        offset=offset,
        limit=limit,
    )

    return [
        LeadResponse.model_validate(lead)
        for lead in leads
    ]


@router.post(
    "",
    response_model=LeadResponse,
    status_code=201,
)
def create_lead(
    payload: LeadCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Create a lead in the authenticated organization."""

    create_payload = LeadCreate(
        organization_id=current_user.organization_id,
        **payload.model_dump(),
    )

    lead = LeadService(
        db
    ).create(
        create_payload,
        assigned_by_user_id=current_user.id,
        assignment_reason="Lead created through API.",
    )

    return LeadResponse.model_validate(
        lead
    )


@router.get(
    "/statuses",
    response_model=list[LeadStatusResponse],
)
def list_lead_statuses(
    current_user: CurrentUser,
    db: DatabaseSession,
    active_only: bool = True,
) -> list[LeadStatusResponse]:
    """Return the authenticated organization's lifecycle statuses."""

    statuses = LeadStatusService(db).list_by_organization(
        current_user.organization_id,
        active_only=active_only,
    )

    return [
        LeadStatusResponse.model_validate(status)
        for status in statuses
    ]


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
)
def get_lead(
    lead_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Return one organization-scoped lead."""

    lead = LeadService(
        db
    ).get(
        current_user.organization_id,
        lead_id,
    )

    return LeadResponse.model_validate(
        lead
    )


@router.patch(
    "/{lead_id}",
    response_model=LeadResponse,
)
def update_lead(
    lead_id: UUID,
    payload: LeadUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Update mutable lead fields."""

    lead = LeadService(
        db
    ).update(
        current_user.organization_id,
        lead_id,
        payload,
        assigned_by_user_id=current_user.id,
        assignment_reason="Lead updated through API.",
    )

    return LeadResponse.model_validate(
        lead
    )


@router.patch(
    "/{lead_id}/status",
    response_model=LeadResponse,
)
def update_lead_status(
    lead_id: UUID,
    payload: LeadStatusUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Move a lead to another lifecycle status."""

    lead = LeadService(
        db
    ).update_status(
        current_user.organization_id,
        lead_id,
        payload,
    )

    return LeadResponse.model_validate(
        lead
    )


@router.patch(
    "/{lead_id}/assignment",
    response_model=LeadResponse,
)
def update_lead_assignment(
    lead_id: UUID,
    payload: LeadAssignmentUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Assign, reassign, or unassign a lead."""

    service = LeadService(db)

    if payload.assigned_to_user_id is None:
        lead = service.unassign(
            current_user.organization_id,
            lead_id,
        )
    else:
        lead = service.assign(
            current_user.organization_id,
            lead_id,
            payload.assigned_to_user_id,
            assigned_by_user_id=current_user.id,
            reason="Lead assignment updated through API.",
        )

    return LeadResponse.model_validate(
        lead
    )


@router.post(
    "/{lead_id}/archive",
    response_model=LeadResponse,
)
def archive_lead(
    lead_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Archive a lead without deleting its history."""

    lead = LeadService(
        db
    ).archive(
        current_user.organization_id,
        lead_id,
    )

    return LeadResponse.model_validate(
        lead
    )


@router.post(
    "/{lead_id}/restore",
    response_model=LeadResponse,
)
def restore_lead(
    lead_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Restore an archived lead."""

    lead = LeadService(
        db
    ).restore(
        current_user.organization_id,
        lead_id,
    )

    return LeadResponse.model_validate(
        lead
    )
