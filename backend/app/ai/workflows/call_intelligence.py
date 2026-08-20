"""AI workflow for call-transcript intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.contracts.call_analysis import CallAnalysisResult
from app.ai.providers.base import AIProvider
from app.core.exceptions import AIServiceError
from app.schemas.ai import AIExecutionRequest
from app.schemas.lead import LeadAIInsightUpdate, LeadUpdate
from app.services.ai_execution_service import AIExecutionService
from app.services.call_service import CallService
from app.services.lead_service import LeadService


@dataclass(slots=True)
class CallIntelligenceWorkflowResult:
    """Final structured call-intelligence result."""

    call_recording_id: UUID
    customer_id: UUID
    lead_id: UUID | None

    summary: str
    purchase_intent: str | None
    sentiment: str | None
    requirement: str | None

    objections: list[str]
    commitments: list[str]
    action_items: list[str]
    customer_questions: list[str]
    key_moments: list[str]

    confidence: float
    requires_review: bool

    analysis_id: UUID


class CallIntelligenceWorkflow:
    """Analyze a completed call transcript with structured AI."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
    ) -> None:
        self.db = db
        self.calls = CallService(db)
        self.leads = LeadService(db)
        self.execution = AIExecutionService(
            db,
            provider,
        )

    def run(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        *,
        force_refresh: bool = False,
    ) -> CallIntelligenceWorkflowResult:
        """Analyze a persisted call transcript."""

        recording = self.calls.get(
            organization_id,
            call_recording_id,
        )

        transcript = (
            recording.transcript.strip()
            if recording.transcript
            else ""
        )

        if not transcript:
            raise AIServiceError(
                "Call recording has no transcript to analyze.",
                details={
                    "call_recording_id": str(recording.id),
                },
            )

        if recording.transcription_status != "COMPLETED":
            raise AIServiceError(
                "Call transcription is not completed.",
                details={
                    "call_recording_id": str(recording.id),
                    "transcription_status": (
                        recording.transcription_status
                    ),
                },
            )

        response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=recording.customer_id,
                lead_id=recording.lead_id,
                conversation_id=recording.conversation_id,
                call_recording_id=recording.id,
                analysis_type="CALL_ANALYSIS",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "call_intelligence",
                    "transcript_language": (
                        recording.transcript_language
                    ),
                    "duration_seconds": (
                        recording.duration_seconds
                    ),
                },
            ),
            prompt_values={
                "transcript": transcript,
            },
        )

        analysis = CallAnalysisResult.model_validate(
            response.result
        )

        if recording.lead_id is not None:
            lead = self.leads.get(
                organization_id,
                recording.lead_id,
            )

            if analysis.requirement:
                self.leads.update(
                    organization_id,
                    lead.id,
                    LeadUpdate(
                        requirement=analysis.requirement,
                    ),
                )

            self.leads.update_ai_insights(
                organization_id,
                lead.id,
                LeadAIInsightUpdate(
                    purchase_intent=analysis.purchase_intent,
                    conversation_summary=analysis.summary,
                ),
            )

        return CallIntelligenceWorkflowResult(
            call_recording_id=recording.id,
            customer_id=recording.customer_id,
            lead_id=recording.lead_id,
            summary=analysis.summary,
            purchase_intent=(
                analysis.purchase_intent.value
                if analysis.purchase_intent is not None
                else None
            ),
            sentiment=analysis.sentiment,
            requirement=analysis.requirement,
            objections=analysis.objections,
            commitments=analysis.commitments,
            action_items=analysis.action_items,
            customer_questions=analysis.customer_questions,
            key_moments=analysis.key_moments,
            confidence=analysis.confidence,
            requires_review=response.requires_review,
            analysis_id=response.analysis_id,
        )
