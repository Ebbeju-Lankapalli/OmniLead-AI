"""Raw omnichannel enquiry API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DatabaseSession
from app.core.exceptions import ValidationError
from app.db.types import EnquiryStatus, LeadSource
from app.schemas.enquiry import (
    EnquiryConvertRequest,
    EnquiryCreate,
    EnquiryCreateRequest,
    EnquiryLinkUpdate,
    EnquiryResponse,
    EnquiryStatusUpdate,
    EnquiryUpdate,
)
from app.schemas.lead import LeadCreate, LeadResponse
from app.services.enquiry_service import EnquiryService

router = APIRouter(
    prefix="/enquiries",
    tags=["enquiries"],
)


@router.post(
    "",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enquiry(
    payload: EnquiryCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Create a raw enquiry for the authenticated organization."""

    enquiry = EnquiryService(
        db
    ).create(
        EnquiryCreate(
            organization_id=current_user.organization_id,
            **payload.model_dump(),
        )
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.get(
    "",
    response_model=list[EnquiryResponse],
)
def list_enquiries(
    current_user: CurrentUser,
    db: DatabaseSession,
    status_filter: Annotated[
        EnquiryStatus | None,
        Query(alias="status"),
    ] = None,
    source: LeadSource | None = None,
    customer_id: UUID | None = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[EnquiryResponse]:
    """Return enquiries belonging to the authenticated organization."""

    enquiries = EnquiryService(
        db
    ).list_by_organization(
        current_user.organization_id,
        status=status_filter,
        source=source.value if source is not None else None,
        customer_id=customer_id,
        offset=offset,
        limit=limit,
    )

    return [
        EnquiryResponse.model_validate(
            enquiry
        )
        for enquiry in enquiries
    ]


@router.get(
    "/review-queue",
    response_model=list[EnquiryResponse],
)
def list_review_queue(
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
) -> list[EnquiryResponse]:
    """Return enquiries waiting for human review."""

    enquiries = EnquiryService(
        db
    ).list_by_organization(
        current_user.organization_id,
        status=EnquiryStatus.NEEDS_REVIEW,
        offset=offset,
        limit=limit,
    )

    return [
        EnquiryResponse.model_validate(
            enquiry
        )
        for enquiry in enquiries
    ]


@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
)
def get_enquiry(
    enquiry_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Return one organization-scoped enquiry."""

    enquiry = EnquiryService(
        db
    ).get(
        current_user.organization_id,
        enquiry_id,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.patch(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
)
def update_enquiry(
    enquiry_id: UUID,
    payload: EnquiryUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Update mutable enquiry fields."""

    enquiry = EnquiryService(
        db
    ).update(
        current_user.organization_id,
        enquiry_id,
        payload,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.patch(
    "/{enquiry_id}/status",
    response_model=EnquiryResponse,
)
def update_enquiry_status(
    enquiry_id: UUID,
    payload: EnquiryStatusUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Update the enquiry processing state."""

    enquiry = EnquiryService(
        db
    ).update_status(
        current_user.organization_id,
        enquiry_id,
        payload,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.patch(
    "/{enquiry_id}/links",
    response_model=EnquiryResponse,
)
def link_enquiry(
    enquiry_id: UUID,
    payload: EnquiryLinkUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Link an enquiry to resolved CRM records."""

    enquiry = EnquiryService(
        db
    ).link(
        current_user.organization_id,
        enquiry_id,
        payload,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.post(
    "/{enquiry_id}/needs-review",
    response_model=EnquiryResponse,
)
def mark_enquiry_needs_review(
    enquiry_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Move an enquiry into the human-review queue."""

    enquiry = EnquiryService(
        db
    ).mark_needs_review(
        current_user.organization_id,
        enquiry_id,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.post(
    "/{enquiry_id}/ai-analyzed",
    response_model=EnquiryResponse,
)
def mark_enquiry_ai_analyzed(
    enquiry_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Mark an enquiry as successfully AI analyzed."""

    enquiry = EnquiryService(
        db
    ).mark_ai_analyzed(
        current_user.organization_id,
        enquiry_id,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.post(
    "/{enquiry_id}/general-enquiry",
    response_model=EnquiryResponse,
)
def mark_general_enquiry(
    enquiry_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> EnquiryResponse:
    """Classify an enquiry as a non-lead general enquiry."""

    enquiry = EnquiryService(
        db
    ).mark_general_enquiry(
        current_user.organization_id,
        enquiry_id,
    )

    return EnquiryResponse.model_validate(
        enquiry
    )


@router.post(
    "/{enquiry_id}/convert",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
)
def convert_enquiry_to_lead(
    enquiry_id: UUID,
    payload: EnquiryConvertRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> LeadResponse:
    """Convert a customer-linked enquiry to a lead exactly once."""

    service = EnquiryService(db)

    enquiry = service.get(
        current_user.organization_id,
        enquiry_id,
    )

    if enquiry.customer_id is None:
        raise ValidationError(
            "Enquiry must be linked to a customer before conversion."
        )

    lead = service.convert_to_lead(
        current_user.organization_id,
        enquiry_id,
        LeadCreate(
            organization_id=current_user.organization_id,
            customer_id=enquiry.customer_id,
            source_enquiry_id=enquiry_id,
            **payload.model_dump(),
        ),
        assigned_by_user_id=current_user.id,
        assignment_reason="Converted from enquiry",
    )

    return LeadResponse.model_validate(
        lead
    )
