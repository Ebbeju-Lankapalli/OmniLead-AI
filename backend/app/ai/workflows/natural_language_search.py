"""Natural-language lead-search workflow."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.contracts.search_filters import (
    NaturalLanguageSearchFiltersResult,
)
from app.ai.providers.base import AIProvider
from app.schemas.ai import AIExecutionRequest
from app.schemas.search import (
    LeadSearchFilters,
    NaturalLanguageSearchRequest,
    ParsedSearchResponse,
    SearchDateRange,
    SearchRequest,
    SearchResponse,
    SearchScoreRange,
    SearchSort,
)
from app.services.ai_execution_service import AIExecutionService
from app.services.search_service import SearchService


class NaturalLanguageSearchWorkflow:
    """Parse natural-language lead searches and execute safe queries."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
    ) -> None:
        self.execution = AIExecutionService(
            db,
            provider,
        )
        self.search_service = SearchService(db)

    def parse(
        self,
        request: NaturalLanguageSearchRequest,
        *,
        now: datetime | None = None,
        force_refresh: bool = False,
    ) -> ParsedSearchResponse:
        """Convert a natural-language search into validated filters."""

        current_time = (
            now
            or datetime.now().astimezone()
        )

        response = self.execution.execute(
            AIExecutionRequest(
                organization_id=request.organization_id,
                analysis_type="NATURAL_LANGUAGE_SEARCH",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "natural_language_search",
                },
            ),
            prompt_values={
                "query": request.query,
                "current_time": current_time.isoformat(),
            },
        )

        parsed = NaturalLanguageSearchFiltersResult.model_validate(
            response.result
        )

        # Gemini may sometimes convert ordinary semantic concepts
        # into CRM tags even when the user never requested tag filtering.
        #
        # Example:
        # "find customers interested in renewable energy"
        #
        # This should use semantic retrieval, not require an existing
        # "renewable energy" CRM tag. Preserve tag filters only when the
        # user explicitly refers to tags.
        query_lower = request.query.casefold()

        explicit_tag_request = any(
            marker in query_lower
            for marker in (
                "tag ",
                "tagged ",
                "tags ",
                "with tag",
                "with the tag",
            )
        )

        parsed_tags = (
            parsed.tags
            if explicit_tag_request
            else []
        )

        filters = LeadSearchFilters(
            sources=parsed.sources,
            purchase_intents=parsed.purchase_intents,
            lead_score=(
                SearchScoreRange(
                    minimum=parsed.lead_score.minimum,
                    maximum=parsed.lead_score.maximum,
                )
                if parsed.lead_score is not None
                else None
            ),
            priority_score=(
                SearchScoreRange(
                    minimum=parsed.priority_score.minimum,
                    maximum=parsed.priority_score.maximum,
                )
                if parsed.priority_score is not None
                else None
            ),
            followup_risk_score=(
                SearchScoreRange(
                    minimum=parsed.followup_risk_score.minimum,
                    maximum=parsed.followup_risk_score.maximum,
                )
                if parsed.followup_risk_score is not None
                else None
            ),
            next_followup_at=(
                SearchDateRange(
                    start=parsed.next_followup_at.start,
                    end=parsed.next_followup_at.end,
                )
                if parsed.next_followup_at is not None
                else None
            ),
            last_contact_at=(
                SearchDateRange(
                    start=parsed.last_contact_at.start,
                    end=parsed.last_contact_at.end,
                )
                if parsed.last_contact_at is not None
                else None
            ),
            tags=parsed_tags,
            has_assignee=parsed.has_assignee,
            has_next_followup=parsed.has_next_followup,
            is_archived=parsed.is_archived,
        )

        return ParsedSearchResponse(
            original_query=request.query,
            interpreted_query=parsed.interpreted_query,
            filters=filters,
            sort=SearchSort(
                field=parsed.sort_field,
                direction=parsed.sort_direction,
            ),
            semantic_search=parsed.semantic_search,
            confidence=parsed.confidence,
            explanation=parsed.explanation,
        )

    def search(
        self,
        request: NaturalLanguageSearchRequest,
        *,
        page: int = 1,
        page_size: int = 20,
        now: datetime | None = None,
        force_refresh: bool = False,
    ) -> SearchResponse:
        """Parse natural language and execute the resulting safe search."""

        parsed = self.parse(
            request,
            now=now,
            force_refresh=force_refresh,
        )

        return self.search_service.search(
            SearchRequest(
                organization_id=request.organization_id,
                query=request.query,
                filters=parsed.filters,
                semantic_search=parsed.semantic_search,
                sort=parsed.sort,
                page=page,
                page_size=page_size,
            )
        )
