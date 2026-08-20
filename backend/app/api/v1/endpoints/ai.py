"""AI intelligence and human-review API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.ai.providers.gemini import GeminiProvider
from app.ai.workflows.conversation_analysis import (
    ConversationAnalysisWorkflow,
)
from app.ai.workflows.enquiry_analysis import (
    EnquiryAnalysisWorkflow,
)
from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.ai import (
    AIAnalysisResponse,
    AIFeedbackCreate,
    AIFeedbackResponse,
    AIReviewQueueResponse,
)
from app.services.ai_followup_service import AIFollowUpService
from app.services.ai_service import AIService

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@router.get(
    "/analyses",
    response_model=list[AIAnalysisResponse],
)
def list_ai_analyses(
    current_user: CurrentUser,
    db: DatabaseSession,
    analysis_type: Annotated[
        str | None,
        Query(),
    ] = None,
    status: Annotated[
        str | None,
        Query(),
    ] = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[AIAnalysisResponse]:
    """Return organization-scoped AI analysis history."""

    analyses = AIService(
        db
    ).list_analyses(
        current_user.organization_id,
        analysis_type=analysis_type,
        status=status,
        offset=offset,
        limit=limit,
    )

    return [
        AIAnalysisResponse.model_validate(
            analysis
        )
        for analysis in analyses
    ]


@router.get(
    "/analyses/{analysis_id}",
    response_model=AIAnalysisResponse,
)
def get_ai_analysis(
    analysis_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> AIAnalysisResponse:
    """Return one organization-scoped AI analysis."""

    analysis = AIService(
        db
    ).get_analysis(
        current_user.organization_id,
        analysis_id,
    )

    return AIAnalysisResponse.model_validate(
        analysis
    )


@router.get(
    "/review-queue",
    response_model=AIReviewQueueResponse,
)
def get_ai_review_queue(
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
    include_reviewed: bool = False,
) -> AIReviewQueueResponse:
    """Return AI results awaiting human review."""

    return AIService(
        db
    ).review_queue(
        current_user.organization_id,
        page=page,
        page_size=page_size,
        include_reviewed=include_reviewed,
    )


@router.post(
    "/analyses/{analysis_id}/feedback",
    response_model=AIFeedbackResponse,
)
def submit_ai_feedback(
    analysis_id: UUID,
    payload: AIFeedbackCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> AIFeedbackResponse:
    """Submit human feedback for an AI analysis."""

    analysis = AIService(
        db
    ).get_analysis(
        current_user.organization_id,
        analysis_id,
    )

    feedback_payload = AIFeedbackCreate(
        organization_id=current_user.organization_id,
        ai_analysis_id=analysis.id,
        reviewed_by_user_id=current_user.id,
        decision=payload.decision,
        original_result=payload.original_result,
        final_result=payload.final_result,
        changed_fields=payload.changed_fields,
        feedback_notes=payload.feedback_notes,
    )

    feedback = AIService(
        db
    ).submit_feedback(
        feedback_payload
    )

    return AIFeedbackResponse.model_validate(
        feedback
    )


@router.post(
    "/leads/{lead_id}/analyze",
)
def analyze_lead(
    lead_id: UUID,
    content: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    customer_context: str = "",
    product_context: str = "",
    conversation_context: str = "",
    force_refresh: bool = False,
):
    """Run lead intelligence for an existing lead."""

    provider = GeminiProvider()

    return EnquiryAnalysisWorkflow(
        db,
        provider,
    ).run(
        current_user.organization_id,
        lead_id,
        content=content,
        customer_context=customer_context,
        product_context=product_context,
        conversation_context=conversation_context,
        force_refresh=force_refresh,
    )


@router.post(
    "/conversations/{conversation_id}/analyze",
)
def analyze_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
    force_refresh: bool = False,
):
    """Summarize and analyze an existing conversation."""

    provider = GeminiProvider()

    return ConversationAnalysisWorkflow(
        db,
        provider,
    ).run(
        current_user.organization_id,
        conversation_id,
        force_refresh=force_refresh,
    )


@router.post(
    "/leads/{lead_id}/followup",
)
def recommend_lead_followup(
    lead_id: UUID,
    lead_context: str,
    conversation_context: str,
    current_user: CurrentUser,
    db: DatabaseSession,
    auto_schedule: bool = True,
    force_refresh: bool = False,
):
    """Generate and optionally schedule an AI follow-up."""

    provider = GeminiProvider()

    return AIFollowUpService(
        db,
        provider,
    ).recommend_and_schedule(
        current_user.organization_id,
        lead_id,
        lead_context=lead_context,
        conversation_context=conversation_context,
        auto_schedule=auto_schedule,
        force_refresh=force_refresh,
    )
