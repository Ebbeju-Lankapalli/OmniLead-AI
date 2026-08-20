"""AI workflow execution orchestration."""

from __future__ import annotations

import time
from contextlib import suppress
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.contracts.call_analysis import CallAnalysisResult
from app.ai.contracts.enquiry_triage import EnquiryTriageResult
from app.ai.contracts.extraction import ExtractionResult
from app.ai.contracts.followup import FollowUpRecommendationResult
from app.ai.contracts.intent import IntentAnalysisResult
from app.ai.contracts.next_action import NextActionResult
from app.ai.contracts.objection import ObjectionAnalysisResult
from app.ai.contracts.qualification import QualificationResult
from app.ai.contracts.search_filters import NaturalLanguageSearchFiltersResult
from app.ai.contracts.summary import ConversationSummaryResult
from app.ai.guards.confidence import evaluate_confidence
from app.ai.prompts.registry import get_prompt
from app.ai.providers.base import AIProvider
from app.core.exceptions import AIServiceError
from app.schemas.ai import (
    AIAnalysisCreate,
    AIExecutionRequest,
    AIExecutionResponse,
)
from app.services.ai_service import AIService

CONTRACTS: dict[str, type[BaseModel]] = {
    "INTENT_ANALYSIS": IntentAnalysisResult,
    "LEAD_QUALIFICATION": QualificationResult,
    "NEXT_ACTION": NextActionResult,
    "NATURAL_LANGUAGE_SEARCH": NaturalLanguageSearchFiltersResult,
    "CONVERSATION_SUMMARY": ConversationSummaryResult,
    "EXTRACTION": ExtractionResult,
    "ENQUIRY_TRIAGE": EnquiryTriageResult,
    "OBJECTION_ANALYSIS": ObjectionAnalysisResult,
    "FOLLOWUP_RECOMMENDATION": FollowUpRecommendationResult,
    "CALL_ANALYSIS": CallAnalysisResult,
}


class AIExecutionService:
    """Execute structured AI workflows with persistence and review guards."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
    ) -> None:
        self.db = db
        self.provider = provider
        self.ai = AIService(db)

    def execute(
        self,
        request: AIExecutionRequest,
        *,
        prompt_values: dict[str, Any],
    ) -> AIExecutionResponse:
        """Execute one supported AI workflow."""

        analysis_type = request.analysis_type

        response_schema = CONTRACTS.get(
            analysis_type
        )

        if response_schema is None:
            raise AIServiceError(
                "Unsupported AI analysis type.",
                details={
                    "analysis_type": analysis_type,
                },
            )

        prompt = get_prompt(
            analysis_type
        )

        rendered_prompt = prompt.render(
            **prompt_values
        )

        input_hash = AIService.build_input_hash(
            analysis_type=analysis_type,
            content={
                "prompt": rendered_prompt,
                "prompt_name": prompt.name,
                "prompt_version": prompt.version,
                "metadata": request.metadata,
            },
        )

        if not request.force_refresh:
            cached = self.ai.get_cached_analysis(
                request.organization_id,
                analysis_type,
                input_hash,
            )

            if cached is not None:
                confidence = (
                    float(cached.model_confidence)
                    if cached.model_confidence is not None
                    else None
                )

                confidence_decision = evaluate_confidence(
                    confidence
                )

                return AIExecutionResponse(
                    analysis_id=cached.id,
                    analysis_type=cached.analysis_type,
                    status=cached.status,
                    result=cached.result,
                    confidence=cached.model_confidence,
                    requires_review=(
                        confidence_decision.requires_review
                    ),
                )

        analysis = self.ai.create_analysis(
            AIAnalysisCreate(
                organization_id=request.organization_id,
                customer_id=request.customer_id,
                lead_id=request.lead_id,
                enquiry_id=request.enquiry_id,
                conversation_id=request.conversation_id,
                interaction_id=request.interaction_id,
                call_recording_id=request.call_recording_id,
                analysis_type=analysis_type,
                model_provider=self.provider.provider_name,
                model_name=getattr(
                    self.provider,
                    "model",
                    "unknown",
                ),
                prompt_name=prompt.name,
                prompt_version=prompt.version,
                input_hash=input_hash,
                result={},
                status="PENDING",
            ),
            deduplicate=not request.force_refresh,
        )

        if (
            analysis.status == "COMPLETED"
            and not request.force_refresh
        ):
            confidence = (
                float(analysis.model_confidence)
                if analysis.model_confidence is not None
                else None
            )

            decision = evaluate_confidence(
                confidence
            )

            return AIExecutionResponse(
                analysis_id=analysis.id,
                analysis_type=analysis.analysis_type,
                status=analysis.status,
                result=analysis.result,
                confidence=analysis.model_confidence,
                requires_review=decision.requires_review,
            )

        started = time.perf_counter()

        try:
            provider_response = (
                self.provider.generate_structured(
                    prompt=rendered_prompt,
                    response_schema=response_schema,
                    system_instruction=prompt.system_instruction,
                    temperature=prompt.temperature,
                )
            )

            latency_ms = int(
                (time.perf_counter() - started)
                * 1000
            )

            parsed = provider_response.parsed

            confidence = self._extract_confidence(
                parsed
            )

            usage = provider_response.usage

            completed = self.ai.complete_analysis(
                request.organization_id,
                analysis.id,
                result=parsed.model_dump(
                    mode="json"
                ),
                confidence=confidence,
                latency_ms=latency_ms,
                input_tokens=(
                    usage.input_tokens
                    if usage is not None
                    else None
                ),
                output_tokens=(
                    usage.output_tokens
                    if usage is not None
                    else None
                ),
            )

        except Exception as exc:
            latency_ms = int(
                (time.perf_counter() - started)
                * 1000
            )

            with suppress(Exception):
                self.ai.fail_analysis(
                    request.organization_id,
                    analysis.id,
                    error_code=(
                        exc.__class__.__name__
                        .upper()
                    ),
                    error_message=str(exc),
                    latency_ms=latency_ms,
                )

            if isinstance(
                exc,
                AIServiceError,
            ):
                raise

            raise AIServiceError(
                "AI workflow execution failed.",
                details={
                    "analysis_type": analysis_type,
                    "analysis_id": str(
                        analysis.id
                    ),
                    "error": str(exc),
                },
            ) from exc

        confidence_value = (
            float(completed.model_confidence)
            if completed.model_confidence is not None
            else None
        )

        decision = evaluate_confidence(
            confidence_value
        )

        return AIExecutionResponse(
            analysis_id=completed.id,
            analysis_type=completed.analysis_type,
            status=completed.status,
            result=completed.result,
            confidence=completed.model_confidence,
            requires_review=decision.requires_review,
        )

    @staticmethod
    def _extract_confidence(
        result: BaseModel,
    ) -> float | None:
        """Extract a standard confidence field from structured contracts."""

        confidence = getattr(
            result,
            "confidence",
            None,
        )

        if confidence is None:
            return None

        return float(confidence)

    def get_analysis(
        self,
        organization_id: UUID,
        analysis_id: UUID,
    ):
        """Return the persisted analysis behind an execution."""

        return self.ai.get_analysis(
            organization_id,
            analysis_id,
        )
