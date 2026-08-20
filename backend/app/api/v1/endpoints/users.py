"""Organization team-member API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, CurrentUser, DatabaseSession
from app.schemas.user import (
    TeamMemberUpdate,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_team_members(
    current_user: CurrentUser,
    db: DatabaseSession,
    active_only: bool = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[UserResponse]:
    """Return team members in the authenticated organization."""

    users = UserService(
        db
    ).list_by_organization(
        current_user.organization_id,
        active_only=active_only,
        offset=offset,
        limit=limit,
    )

    return [
        UserResponse.model_validate(user)
        for user in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_team_member(
    user_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> UserResponse:
    """Return one organization-scoped team member."""

    user = UserService(
        db
    ).get(
        current_user.organization_id,
        user_id,
    )

    return UserResponse.model_validate(
        user
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_team_member(
    user_id: UUID,
    payload: TeamMemberUpdate,
    current_user: AdminUser,
    db: DatabaseSession,
) -> UserResponse:
    """Update a team member as an organization admin."""

    user = UserService(
        db
    ).update_team_member(
        current_user.organization_id,
        user_id,
        payload,
        acting_user_id=current_user.id,
    )

    return UserResponse.model_validate(
        user
    )
