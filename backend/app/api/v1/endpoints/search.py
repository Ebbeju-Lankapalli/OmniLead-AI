"""Lead search API endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.ai.providers.gemini import GeminiProvider
from app.ai.workflows.natural_language_search import (
    NaturalLanguageSearchWorkflow,
)
from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.search import (
    NaturalLanguageSearchRequest,
    ParsedSearchResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.search_service import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
)
def search_leads(
    payload: SearchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> SearchResponse:
    """
    Search leads using validated structured filters.

    Organization scope is always taken from the authenticated user.
    Client-supplied organization IDs are never trusted.
    """

    scoped_payload = payload.model_copy(
        update={
            "organization_id": current_user.organization_id,
        }
    )

    return SearchService(
        db
    ).search(
        scoped_payload
    )


@router.post(
    "/natural-language",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
)
def natural_language_search(
    payload: NaturalLanguageSearchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    force_refresh: bool = False,
) -> SearchResponse:
    """
    Parse a natural-language query and execute the resulting search.

    The authenticated user's organization is always enforced.
    """

    scoped_payload = payload.model_copy(
        update={
            "organization_id": current_user.organization_id,
        }
    )

    provider = GeminiProvider()

    workflow = NaturalLanguageSearchWorkflow(
        db,
        provider,
    )

    return workflow.search(
        scoped_payload,
        page=page,
        page_size=page_size,
        force_refresh=force_refresh,
    )


@router.post(
    "/natural-language/parse",
    response_model=ParsedSearchResponse,
    status_code=status.HTTP_200_OK,
)
def parse_natural_language_search(
    payload: NaturalLanguageSearchRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
    force_refresh: bool = False,
) -> ParsedSearchResponse:
    """
    Parse natural-language lead search without executing it.

    Organization scope is always derived from the authenticated user.
    """

    scoped_payload = payload.model_copy(
        update={
            "organization_id": current_user.organization_id,
        }
    )

    provider = GeminiProvider()

    workflow = NaturalLanguageSearchWorkflow(
        db,
        provider,
    )

    return workflow.parse(
        scoped_payload,
        force_refresh=force_refresh,
    )
