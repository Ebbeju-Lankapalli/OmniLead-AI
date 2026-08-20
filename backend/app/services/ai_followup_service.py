"""AI-assisted follow-up scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.contracts.followup import FollowUpRecommendationResult
from app.ai.providers.base import AIProvider
from app.core.exceptions import ValidationError
from app.models.followup import FollowUp
from app.schemas.ai import AIExecutionRequest
from app.schemas.followup import FollowUpCreate
from app.services.ai_execution_service import AIExecutionService
from app.services.followup_service import FollowUpService
from app.services.lead_service import LeadService


@dataclass(slots=True)
class AIFollowUpResult:
    """Outcome of an AI-assisted follow-up recommendation."""

    analysis_id: UUID | None

    should_follow_up: bool
    requires_review: bool

    recommendation: FollowUpRecommendationResult

    followup_created: bool
    followup: FollowUp | None = None

    reason: str | None = None


class AIFollowUpService:
    """Generate and optionally schedule AI-recommended follow-ups."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
    ) -> None:
        self.db = db
        self.execution = AIExecutionService(
            db,
            provider,
        )
        self.leads = LeadService(db)
        self.followups = FollowUpService(db)

    def recommend_and_schedule(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        lead_context: str,
        conversation_context: str,
        now: datetime | None = None,
        auto_schedule: bool = True,
        force_refresh: bool = False,
    ) -> AIFollowUpResult:
        """Generate a recommendation and safely create a follow-up."""

        lead = self.leads.get(
            organization_id,
            lead_id,
        )

        generated_at = (
            now
            or datetime.now().astimezone()
        )

        if auto_schedule:
            existing = (
                self.followups.followups.get_next_for_lead(
                    organization_id,
                    lead.id,
                )
            )

            if existing is not None:
                return AIFollowUpResult(
                    analysis_id=None,
                    should_follow_up=True,
                    requires_review=False,
                    recommendation=FollowUpRecommendationResult(
                        should_follow_up=True,
                        followup_type=None,
                        recommended_delay_minutes=None,
                        confidence=1.0,
                        reason=(
                            "Existing scheduled follow-up found. "
                            "AI execution skipped."
                        ),
                    ),
                    followup_created=False,
                    followup=existing,
                    reason=(
                        "Lead already has a scheduled follow-up. "
                        "AI recommendation was not executed."
                    ),
                )

        response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=lead.customer_id,
                lead_id=lead.id,
                analysis_type="FOLLOWUP_RECOMMENDATION",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "ai_followup",
                },
            ),
            prompt_values={
                "lead_context": lead_context.strip()
                or "No additional lead context available.",
                "conversation_context": (
                    conversation_context.strip()
                    or "No recent conversation context available."
                ),
            },
        )

        recommendation = (
            FollowUpRecommendationResult.model_validate(
                response.result
            )
        )

        if not recommendation.should_follow_up:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=False,
                requires_review=response.requires_review,
                recommendation=recommendation,
                followup_created=False,
                reason="AI determined that no follow-up is required.",
            )

        if response.requires_review:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=True,
                requires_review=True,
                recommendation=recommendation,
                followup_created=False,
                reason=(
                    "AI recommendation requires human review "
                    "before scheduling."
                ),
            )

        if not auto_schedule:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=True,
                requires_review=False,
                recommendation=recommendation,
                followup_created=False,
                reason="Automatic scheduling is disabled.",
            )

        if lead.assigned_to_user_id is None:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=True,
                requires_review=False,
                recommendation=recommendation,
                followup_created=False,
                reason=(
                    "Lead has no assigned salesperson. "
                    "Follow-up was not automatically scheduled."
                ),
            )

        if recommendation.followup_type is None:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=True,
                requires_review=False,
                recommendation=recommendation,
                followup_created=False,
                reason=(
                    "AI did not provide a follow-up type."
                ),
            )

        if recommendation.recommended_delay_minutes is None:
            return AIFollowUpResult(
                analysis_id=response.analysis_id,
                should_follow_up=True,
                requires_review=False,
                recommendation=recommendation,
                followup_created=False,
                reason=(
                    "AI did not provide a scheduling delay."
                ),
            )

        if recommendation.recommended_delay_minutes < 0:
            raise ValidationError(
                "AI follow-up delay cannot be negative."
            )

        scheduled_at = generated_at + timedelta(
            minutes=(
                recommendation.recommended_delay_minutes
            )
        )

        followup = self.followups.create(
            FollowUpCreate(
                organization_id=organization_id,
                lead_id=lead.id,
                customer_id=lead.customer_id,
                assigned_to_user_id=(
                    lead.assigned_to_user_id
                ),
                created_by_user_id=None,
                followup_type=(
                    recommendation.followup_type
                ),
                scheduled_at=scheduled_at,
                reminder_minutes_before=30,
                notes=(
                    recommendation.suggested_message
                    or recommendation.reason
                ),
            )
        )

        return AIFollowUpResult(
            analysis_id=response.analysis_id,
            should_follow_up=True,
            requires_review=False,
            recommendation=recommendation,
            followup_created=True,
            followup=followup,
            reason="AI-recommended follow-up scheduled.",
        )
