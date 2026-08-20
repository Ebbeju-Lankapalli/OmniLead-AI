"""Conversation and inbox API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.conversation import (
    ConversationCloseUpdate,
    ConversationCreate,
    ConversationCreateRequest,
    ConversationLeadLinkUpdate,
    ConversationPatchRequest,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.conversation_service import ConversationService

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    current_user: CurrentUser,
    db: DatabaseSession,
    customer_id: UUID | None = None,
    lead_id: UUID | None = None,
    open_only: bool = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[ConversationResponse]:
    """Return organization-scoped conversations."""

    conversations = ConversationService(
        db
    ).list_by_organization(
        current_user.organization_id,
        customer_id=customer_id,
        lead_id=lead_id,
        open_only=open_only,
        offset=offset,
        limit=limit,
    )

    return [
        ConversationResponse.model_validate(
            conversation
        )
        for conversation in conversations
    ]


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=201,
)
def create_conversation(
    payload: ConversationCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Create an organization-scoped conversation."""

    conversation = ConversationService(
        db
    ).create(
        ConversationCreate(
            organization_id=current_user.organization_id,
            **payload.model_dump(),
        )
    )

    return ConversationResponse.model_validate(
        conversation
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Return one organization-scoped conversation."""

    conversation = ConversationService(
        db
    ).get(
        current_user.organization_id,
        conversation_id,
    )

    return ConversationResponse.model_validate(
        conversation
    )


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def update_conversation(
    conversation_id: UUID,
    payload: ConversationPatchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Update safe mutable conversation fields."""

    conversation = ConversationService(
        db
    ).update(
        current_user.organization_id,
        conversation_id,
        ConversationUpdate(
            **payload.model_dump(
                exclude_unset=True,
            )
        ),
    )

    return ConversationResponse.model_validate(
        conversation
    )


@router.patch(
    "/{conversation_id}/lead",
    response_model=ConversationResponse,
)
def link_conversation_lead(
    conversation_id: UUID,
    payload: ConversationLeadLinkUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Link or unlink a conversation from a lead."""

    conversation = ConversationService(
        db
    ).link_lead(
        current_user.organization_id,
        conversation_id,
        payload,
    )

    return ConversationResponse.model_validate(
        conversation
    )


@router.post(
    "/{conversation_id}/close",
    response_model=ConversationResponse,
)
def close_conversation(
    conversation_id: UUID,
    payload: ConversationCloseUpdate | None,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Close an active conversation."""

    conversation = ConversationService(
        db
    ).close(
        current_user.organization_id,
        conversation_id,
        payload,
    )

    return ConversationResponse.model_validate(
        conversation
    )


@router.post(
    "/{conversation_id}/reopen",
    response_model=ConversationResponse,
)
def reopen_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ConversationResponse:
    """Reopen a closed conversation."""

    conversation = ConversationService(
        db
    ).reopen(
        current_user.organization_id,
        conversation_id,
    )

    return ConversationResponse.model_validate(
        conversation
    )
