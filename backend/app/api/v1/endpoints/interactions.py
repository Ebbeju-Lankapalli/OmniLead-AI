"""Customer interaction and communication-timeline API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.interaction import (
    InteractionCreate,
    InteractionCreateRequest,
    InteractionPatchRequest,
    InteractionResponse,
    InteractionUpdate,
)
from app.services.interaction_service import InteractionService

router = APIRouter(
    prefix="/interactions",
    tags=["interactions"],
)


@router.get(
    "",
    response_model=list[InteractionResponse],
)
def list_interactions(
    current_user: CurrentUser,
    db: DatabaseSession,
    customer_id: UUID | None = None,
    lead_id: UUID | None = None,
    conversation_id: UUID | None = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[InteractionResponse]:
    """Return organization-scoped interactions."""

    interactions = InteractionService(
        db
    ).list_by_organization(
        current_user.organization_id,
        customer_id=customer_id,
        lead_id=lead_id,
        conversation_id=conversation_id,
        offset=offset,
        limit=limit,
    )

    return [
        InteractionResponse.model_validate(
            interaction
        )
        for interaction in interactions
    ]


@router.post(
    "",
    response_model=InteractionResponse,
    status_code=201,
)
def create_interaction(
    payload: InteractionCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> InteractionResponse:
    """Create an authenticated customer interaction."""

    interaction = InteractionService(
        db
    ).create(
        InteractionCreate(
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            **payload.model_dump(),
        )
    )

    return InteractionResponse.model_validate(
        interaction
    )


@router.get(
    "/conversation/{conversation_id}",
    response_model=list[InteractionResponse],
)
def conversation_timeline(
    conversation_id: UUID,
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
) -> list[InteractionResponse]:
    """Return a chronological conversation timeline."""

    interactions = InteractionService(
        db
    ).list_by_conversation(
        current_user.organization_id,
        conversation_id,
        offset=offset,
        limit=limit,
    )

    return [
        InteractionResponse.model_validate(
            interaction
        )
        for interaction in interactions
    ]


@router.get(
    "/lead/{lead_id}",
    response_model=list[InteractionResponse],
)
def lead_timeline(
    lead_id: UUID,
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
) -> list[InteractionResponse]:
    """Return interaction history for a lead."""

    interactions = InteractionService(
        db
    ).list_by_lead(
        current_user.organization_id,
        lead_id,
        offset=offset,
        limit=limit,
    )

    return [
        InteractionResponse.model_validate(
            interaction
        )
        for interaction in interactions
    ]


@router.get(
    "/{interaction_id}",
    response_model=InteractionResponse,
)
def get_interaction(
    interaction_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> InteractionResponse:
    """Return one organization-scoped interaction."""

    interaction = InteractionService(
        db
    ).get(
        current_user.organization_id,
        interaction_id,
    )

    return InteractionResponse.model_validate(
        interaction
    )


@router.patch(
    "/{interaction_id}",
    response_model=InteractionResponse,
)
def update_interaction(
    interaction_id: UUID,
    payload: InteractionPatchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> InteractionResponse:
    """Update safe mutable interaction fields."""

    interaction = InteractionService(
        db
    ).update(
        current_user.organization_id,
        interaction_id,
        InteractionUpdate(
            **payload.model_dump(
                exclude_unset=True,
            )
        ),
    )

    return InteractionResponse.model_validate(
        interaction
    )
