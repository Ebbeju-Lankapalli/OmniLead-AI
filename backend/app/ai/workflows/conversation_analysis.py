"""AI workflow for conversation summarization and objection analysis."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.contracts.objection import ObjectionAnalysisResult
from app.ai.contracts.summary import ConversationSummaryResult
from app.ai.providers.base import AIProvider
from app.core.exceptions import AIServiceError
from app.schemas.ai import AIExecutionRequest
from app.schemas.conversation import ConversationUpdate
from app.schemas.lead import LeadAIInsightUpdate
from app.services.ai_execution_service import AIExecutionService
from app.services.conversation_service import ConversationService
from app.services.interaction_service import InteractionService
from app.services.lead_service import LeadService


@dataclass(slots=True)
class ConversationAnalysisWorkflowResult:
    """Final result of conversation summarization and objection analysis."""

    conversation_id: UUID
    lead_id: UUID | None

    summary: str
    objections_detected: bool

    summary_confidence: float
    objection_confidence: float

    requires_review: bool

    summary_analysis_id: UUID
    objection_analysis_id: UUID

    summary_result: ConversationSummaryResult
    objection_result: ObjectionAnalysisResult


class ConversationAnalysisWorkflow:
    """Analyze a persisted conversation and update CRM summaries."""

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
        self.conversations = ConversationService(db)
        self.interactions = InteractionService(db)
        self.leads = LeadService(db)

    def run(
        self,
        organization_id: UUID,
        conversation_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> ConversationAnalysisWorkflowResult:
        """Summarize conversation history and detect customer objections."""

        conversation = self.conversations.get(
            organization_id,
            conversation_id,
        )

        timeline = self.interactions.list_by_conversation(
            organization_id,
            conversation.id,
            offset=0,
            limit=100,
        )

        transcript = self._build_transcript(
            timeline
        )

        if not transcript:
            raise AIServiceError(
                "Conversation contains no analyzable interaction content.",
                details={
                    "conversation_id": str(conversation.id),
                },
            )

        summary_response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=conversation.customer_id,
                lead_id=conversation.lead_id,
                conversation_id=conversation.id,
                analysis_type="CONVERSATION_SUMMARY",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "conversation_analysis",
                    "interaction_count": len(timeline),
                },
            ),
            prompt_values={
                "conversation": transcript,
            },
        )

        summary = ConversationSummaryResult.model_validate(
            summary_response.result
        )

        objection_response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=conversation.customer_id,
                lead_id=conversation.lead_id,
                conversation_id=conversation.id,
                analysis_type="OBJECTION_ANALYSIS",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "conversation_analysis",
                    "interaction_count": len(timeline),
                },
            ),
            prompt_values={
                "content": transcript,
            },
        )

        objections = ObjectionAnalysisResult.model_validate(
            objection_response.result
        )

        self.conversations.update(
            organization_id,
            conversation.id,
            ConversationUpdate(
                summary=summary.summary,
            ),
        )

        if conversation.lead_id is not None:
            self.leads.update_ai_insights(
                organization_id,
                conversation.lead_id,
                LeadAIInsightUpdate(
                    conversation_summary=summary.summary,
                ),
            )

        requires_review = any(
            (
                summary_response.requires_review,
                objection_response.requires_review,
            )
        )

        return ConversationAnalysisWorkflowResult(
            conversation_id=conversation.id,
            lead_id=conversation.lead_id,
            summary=summary.summary,
            objections_detected=objections.objections_detected,
            summary_confidence=summary.confidence,
            objection_confidence=objections.confidence,
            requires_review=requires_review,
            summary_analysis_id=summary_response.analysis_id,
            objection_analysis_id=objection_response.analysis_id,
            summary_result=summary,
            objection_result=objections,
        )

    @staticmethod
    def _build_transcript(
        interactions,
    ) -> str:
        """Build a compact chronological transcript from interactions."""

        lines: list[str] = []

        for interaction in interactions:
            content = (
                interaction.content.strip()
                if interaction.content
                else ""
            )

            if not content:
                continue

            direction = (
                interaction.direction
                or "UNKNOWN"
            )

            if direction == "INBOUND":
                speaker = "CUSTOMER"
            elif direction == "OUTBOUND":
                speaker = "SALES"
            elif direction == "INTERNAL":
                speaker = "INTERNAL"
            else:
                speaker = direction

            timestamp = (
                interaction.occurred_at.isoformat()
            )

            lines.append(
                f"[{timestamp}] "
                f"{speaker} "
                f"({interaction.channel}/"
                f"{interaction.interaction_type}): "
                f"{content}"
            )

        return "\n".join(lines).strip()
