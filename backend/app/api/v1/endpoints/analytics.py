"""Historical analytics API endpoint."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "",
    response_model=AnalyticsResponse,
)
def get_analytics(
    current_user: CurrentUser,
    db: DatabaseSession,
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> AnalyticsResponse:
    """Return historical analytics for an inclusive date range."""

    return AnalyticsService(
        db
    ).get_analytics(
        current_user.organization_id,
        start_date=start_date,
        end_date=end_date,
    )
