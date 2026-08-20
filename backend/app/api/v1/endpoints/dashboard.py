"""Operational dashboard API endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> DashboardResponse:
    """Return the authenticated organization's operational dashboard."""

    return DashboardService(
        db
    ).get_dashboard(
        current_user.organization_id,
    )
