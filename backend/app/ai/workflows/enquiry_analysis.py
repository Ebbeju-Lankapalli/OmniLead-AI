"""End-to-end AI intelligence workflow for an existing lead."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.contracts.intent import IntentAnalysisResult
from app.ai.contracts.next_action import NextActionResult
from app.ai.contracts.qualification import QualificationResult
from app.ai.providers.base import AIProvider
from app.ai.scoring.followup_risk import (
    FollowUpRiskResult,
    calculate_followup_risk,
)
from app.ai.scoring.lead_score import (
    LeadScoreResult,
    calculate_lead_score,
)
from app.ai.scoring.priority_score import (
    PriorityScoreResult,
    calculate_priority_score,
)
from app.core.exceptions import AIServiceError
from app.db.types import PurchaseIntent
from app.schemas.ai import AIExecutionRequest
from app.schemas.lead import (
    LeadAIInsightUpdate,
    LeadScoreUpdate,
)
from app.services.ai_execution_service import AIExecutionService
from app.services.lead_service import LeadService


@dataclass(slots=True)
class EnquiryIntelligenceResult:
    """Final structured result of the lead-intelligence workflow."""

    lead_id: UUID

    purchase_intent: PurchaseIntent
    qualification_score: int

    lead_score: int
    priority_score: int
    followup_risk_score: int

    next_best_action: str
    next_best_action_reason: str

    requires_review: bool

    score_breakdown: dict[str, Any]

    intent_analysis_id: UUID
    qualification_analysis_id: UUID
    next_action_analysis_id: UUID


class EnquiryAnalysisWorkflow:
    """Run AI-assisted intelligence and persist it onto a lead."""

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

    def run(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        content: str,
        customer_context: str = "",
        product_context: str = "",
        conversation_context: str = "",
        now: datetime | None = None,
        force_refresh: bool = False,
    ) -> EnquiryIntelligenceResult:
        """Run intent, qualification, scoring, and next-action analysis."""

        cleaned_content = content.strip()

        if not cleaned_content:
            raise AIServiceError(
                "Enquiry content cannot be empty."
            )

        lead = self.leads.get(
            organization_id,
            lead_id,
        )

        generated_at = (
            now
            or datetime.now().astimezone()
        )

        intent_response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=lead.customer_id,
                lead_id=lead.id,
                analysis_type="INTENT_ANALYSIS",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "enquiry_analysis",
                },
            ),
            prompt_values={
                "content": cleaned_content,
            },
        )

        intent = IntentAnalysisResult.model_validate(
            intent_response.result
        )

        qualification_response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=lead.customer_id,
                lead_id=lead.id,
                analysis_type="LEAD_QUALIFICATION",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "enquiry_analysis",
                },
            ),
            prompt_values={
                "content": cleaned_content,
                "customer_context": (
                    customer_context.strip()
                    or "No additional customer context available."
                ),
                "product_context": (
                    product_context.strip()
                    or "No additional product context available."
                ),
            },
        )

        qualification = QualificationResult.model_validate(
            qualification_response.result
        )

        lead_score = calculate_lead_score(
            purchase_intent=intent.purchase_intent,
            qualification_score=(
                qualification.qualification_score
            ),
            confidence=self._combined_confidence(
                intent.confidence,
                qualification.confidence,
            ),
            has_requirement=bool(
                qualification.requirement
            ),
            has_budget_signal=bool(
                qualification.budget_signal
            ),
            has_timeline_signal=bool(
                qualification.timeline_signal
            ),
        )

        risk = calculate_followup_risk(
            now=generated_at,
            last_contact_at=lead.last_contact_at,
            next_followup_at=lead.next_followup_at,
            high_intent=(
                intent.purchase_intent
                == PurchaseIntent.HIGH_INTENT
            ),
            assigned=(
                lead.assigned_to_user_id
                is not None
            ),
        )

        priority = calculate_priority_score(
            lead_score=lead_score.score,
            purchase_intent=intent.purchase_intent,
            followup_risk_score=risk.score,
            urgency=qualification.urgency,
        )

        lead_context = self._build_lead_context(
            lead=lead,
            purchase_intent=intent.purchase_intent,
            qualification=qualification,
            lead_score=lead_score,
            priority=priority,
            risk=risk,
        )

        next_action_response = self.execution.execute(
            AIExecutionRequest(
                organization_id=organization_id,
                customer_id=lead.customer_id,
                lead_id=lead.id,
                analysis_type="NEXT_ACTION",
                force_refresh=force_refresh,
                metadata={
                    "workflow": "enquiry_analysis",
                },
            ),
            prompt_values={
                "lead_context": lead_context,
                "conversation_context": (
                    conversation_context.strip()
                    or cleaned_content
                ),
            },
        )

        next_action = NextActionResult.model_validate(
            next_action_response.result
        )

        score_breakdown = {
            "lead_score": lead_score.breakdown,
            "priority_score": priority.breakdown,
            "followup_risk": risk.breakdown,
            "qualification_score": (
                qualification.qualification_score
            ),
            "intent_confidence": intent.confidence,
            "qualification_confidence": (
                qualification.confidence
            ),
            "next_action_confidence": (
                next_action.confidence
            ),
        }

        self.leads.update_scores(
            organization_id,
            lead.id,
            LeadScoreUpdate(
                lead_score=lead_score.score,
                priority_score=priority.score,
                followup_risk_score=risk.score,
                score_breakdown=score_breakdown,
            ),
        )

        self.leads.update_ai_insights(
            organization_id,
            lead.id,
            LeadAIInsightUpdate(
                purchase_intent=intent.purchase_intent,
                qualification_summary=qualification.summary,
                next_best_action=next_action.action,
                next_best_action_reason=next_action.reason,
            ),
        )

        requires_review = any(
            (
                intent_response.requires_review,
                qualification_response.requires_review,
                next_action_response.requires_review,
            )
        )

        return EnquiryIntelligenceResult(
            lead_id=lead.id,
            purchase_intent=intent.purchase_intent,
            qualification_score=(
                qualification.qualification_score
            ),
            lead_score=lead_score.score,
            priority_score=priority.score,
            followup_risk_score=risk.score,
            next_best_action=next_action.action,
            next_best_action_reason=next_action.reason,
            requires_review=requires_review,
            score_breakdown=score_breakdown,
            intent_analysis_id=(
                intent_response.analysis_id
            ),
            qualification_analysis_id=(
                qualification_response.analysis_id
            ),
            next_action_analysis_id=(
                next_action_response.analysis_id
            ),
        )

    @staticmethod
    def _combined_confidence(
        intent_confidence: float,
        qualification_confidence: float,
    ) -> float:
        """Return conservative combined confidence."""

        return min(
            max(
                (
                    intent_confidence
                    + qualification_confidence
                )
                / 2,
                0.0,
            ),
            1.0,
        )

    @staticmethod
    def _build_lead_context(
        *,
        lead,
        purchase_intent: PurchaseIntent,
        qualification: QualificationResult,
        lead_score: LeadScoreResult,
        priority: PriorityScoreResult,
        risk: FollowUpRiskResult,
    ) -> str:
        """Build deterministic context for next-action generation."""

        return (
            f"Lead ID: {lead.id}\n"
            f"Source: {lead.source}\n"
            f"Purchase intent: {purchase_intent.value}\n"
            f"Qualification score: "
            f"{qualification.qualification_score}\n"
            f"Qualification summary: "
            f"{qualification.summary}\n"
            f"Requirement: "
            f"{qualification.requirement or 'Unknown'}\n"
            f"Urgency: "
            f"{qualification.urgency or 'Unknown'}\n"
            f"Budget signal: "
            f"{qualification.budget_signal or 'Unknown'}\n"
            f"Timeline signal: "
            f"{qualification.timeline_signal or 'Unknown'}\n"
            f"Lead score: {lead_score.score}\n"
            f"Priority score: {priority.score}\n"
            f"Follow-up risk score: {risk.score}"
        )
