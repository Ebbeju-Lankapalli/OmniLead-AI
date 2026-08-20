"""Authenticated organization settings API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DatabaseSession
from app.schemas.organization import (
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization_service import OrganizationService

router = APIRouter(
    prefix="/organization",
    tags=["organization"],
)


@router.get(
    "",
    response_model=OrganizationResponse,
)
def get_current_organization(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> OrganizationResponse:
    """Return the authenticated user's organization."""

    organization = OrganizationService(
        db
    ).get(
        current_user.organization_id
    )

    return OrganizationResponse.model_validate(
        organization
    )


@router.patch(
    "",
    response_model=OrganizationResponse,
)
def update_current_organization(
    payload: OrganizationUpdate,
    current_user: AdminUser,
    db: DatabaseSession,
) -> OrganizationResponse:
    """Update organization settings as an admin."""

    organization = OrganizationService(
        db
    ).update(
        current_user.organization_id,
        payload,
    )

    return OrganizationResponse.model_validate(
        organization
    )
