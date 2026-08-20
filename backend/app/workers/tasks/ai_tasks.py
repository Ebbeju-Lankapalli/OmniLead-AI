"""Background AI workflow tasks."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.ai.providers.gemini import GeminiProvider
from app.ai.workflows.conversation_analysis import (
    ConversationAnalysisWorkflow,
)
from app.ai.workflows.enquiry_analysis import (
    EnquiryAnalysisWorkflow,
)
from app.db.session import get_session_factory
from app.services.ai_followup_service import AIFollowUpService
from app.workers.celery_app import celery_app


def _json_safe(value: Any) -> Any:
    """Convert workflow results into Celery JSON-safe values."""

    if value is None:
        return None

    if isinstance(value, BaseModel):
        return value.model_dump(
            mode="json",
        )

    if is_dataclass(value):
        return _json_safe(
            asdict(value)
        )

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(
        value,
        (datetime, date),
    ):
        return value.isoformat()

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    return value


@celery_app.task(
    name="omnilead.ai.analyze_lead",
)
def analyze_lead_task(
    organization_id: str,
    lead_id: str,
    content: str,
    customer_context: str = "",
    product_context: str = "",
    conversation_context: str = "",
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Run lead intelligence in the background."""

    session_factory = get_session_factory()
    db = session_factory()

    try:
        from app.core.exceptions import AIServiceError

        provider = GeminiProvider()

        try:
            result = EnquiryAnalysisWorkflow(
                db,
                provider,
            ).run(
                UUID(organization_id),
                UUID(lead_id),
                content=content,
                customer_context=customer_context,
                product_context=product_context,
                conversation_context=conversation_context,
                force_refresh=force_refresh,
            )

        except AIServiceError as exc:
            return {
                "status": "degraded",
                "workflow": "lead_analysis",
                "organization_id": organization_id,
                "lead_id": lead_id,
                "reason": (
                    "Lead AI intelligence is temporarily unavailable. "
                    "The lead remains available for manual sales handling."
                ),
                "error_code": exc.error_code,
            }

        return {
            "status": "completed",
            "workflow": "lead_analysis",
            "organization_id": organization_id,
            "lead_id": lead_id,
            "result": _json_safe(result),
        }

    finally:
        db.close()


@celery_app.task(
    name="omnilead.ai.analyze_conversation",
)
def analyze_conversation_task(
    organization_id: str,
    conversation_id: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Run conversation intelligence in the background."""

    session_factory = get_session_factory()
    db = session_factory()

    try:
        from app.core.exceptions import AIServiceError

        provider = GeminiProvider()

        try:
            result = ConversationAnalysisWorkflow(
                db,
                provider,
            ).run(
                UUID(organization_id),
                UUID(conversation_id),
                force_refresh=force_refresh,
            )

        except AIServiceError as exc:
            return {
                "status": "degraded",
                "workflow": "conversation_analysis",
                "organization_id": organization_id,
                "conversation_id": conversation_id,
                "reason": (
                    "Conversation intelligence is temporarily unavailable. "
                    "The conversation remains available for manual review."
                ),
                "error_code": exc.error_code,
            }

        return {
            "status": "completed",
            "workflow": "conversation_analysis",
            "organization_id": organization_id,
            "conversation_id": conversation_id,
            "result": _json_safe(result),
        }

    finally:
        db.close()


@celery_app.task(
    name="omnilead.ai.recommend_followup",
)
def recommend_followup_task(
    organization_id: str,
    lead_id: str,
    lead_context: str,
    conversation_context: str,
    auto_schedule: bool = True,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Generate and optionally schedule an AI follow-up in the background."""

    session_factory = get_session_factory()
    db = session_factory()

    try:
        from app.core.exceptions import AIServiceError

        provider = GeminiProvider()

        try:
            result = AIFollowUpService(
                db,
                provider,
            ).recommend_and_schedule(
                UUID(organization_id),
                UUID(lead_id),
                lead_context=lead_context,
                conversation_context=conversation_context,
                auto_schedule=auto_schedule,
                force_refresh=force_refresh,
            )

        except AIServiceError as exc:
            return {
                "status": "degraded",
                "workflow": "followup_recommendation",
                "organization_id": organization_id,
                "lead_id": lead_id,
                "reason": (
                    "AI follow-up recommendation is temporarily "
                    "unavailable. The lead remains available for "
                    "manual follow-up."
                ),
                "error_code": exc.error_code,
            }

        return {
            "status": "completed",
            "workflow": "followup_recommendation",
            "organization_id": organization_id,
            "lead_id": lead_id,
            "result": {
                "analysis_id": (
                    str(result.analysis_id)
                    if result.analysis_id is not None
                    else None
                ),
                "should_follow_up": result.should_follow_up,
                "requires_review": result.requires_review,
                "recommendation": _json_safe(
                    result.recommendation
                ),
                "followup_created": result.followup_created,
                "followup_id": (
                    str(result.followup.id)
                    if result.followup is not None
                    else None
                ),
                "reason": result.reason,
            },
        }

    finally:
        db.close()


@celery_app.task(
    name="omnilead.ai.triage_enquiry",
)
def triage_enquiry_task(
    organization_id: str,
    enquiry_id: str,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Classify a newly received enquiry in the background."""

    from app.ai.contracts.enquiry_triage import (
        EnquiryTriageResult,
    )
    from app.core.exceptions import AIServiceError
    from app.schemas.ai import AIExecutionRequest
    from app.services.ai_execution_service import (
        AIExecutionService,
    )
    from app.services.enquiry_service import EnquiryService

    session_factory = get_session_factory()
    db = session_factory()

    try:
        organization_uuid = UUID(
            organization_id
        )
        enquiry_uuid = UUID(
            enquiry_id
        )

        enquiries = EnquiryService(
            db
        )

        enquiry = enquiries.get(
            organization_uuid,
            enquiry_uuid,
        )

        content = (
            enquiry.message_text
            or ""
        ).strip()

        if not content:
            updated = enquiries.mark_needs_review(
                organization_uuid,
                enquiry_uuid,
            )

            return {
                "status": "completed",
                "workflow": "enquiry_triage",
                "organization_id": organization_id,
                "enquiry_id": enquiry_id,
                "decision": "NEEDS_REVIEW",
                "reason": (
                    "Enquiry has no message content."
                ),
                "enquiry_status": updated.status,
            }

        customer_context_parts: list[str] = []

        if enquiry.customer_name_raw:
            customer_context_parts.append(
                f"Customer name: "
                f"{enquiry.customer_name_raw}"
            )

        if enquiry.contact_raw:
            customer_context_parts.append(
                f"Contact: {enquiry.contact_raw}"
            )

        customer_context_parts.append(
            f"Source: {enquiry.source}"
        )

        if enquiry.campaign_id:
            customer_context_parts.append(
                f"Campaign ID: "
                f"{enquiry.campaign_id}"
            )

        if enquiry.ad_id:
            customer_context_parts.append(
                f"Ad ID: {enquiry.ad_id}"
            )

        customer_context = "\n".join(
            customer_context_parts
        )

        provider = GeminiProvider()

        execution = AIExecutionService(
            db,
            provider,
        )

        try:
            response = execution.execute(
                AIExecutionRequest(
                    organization_id=organization_uuid,
                    customer_id=enquiry.customer_id,
                    enquiry_id=enquiry.id,
                    conversation_id=(
                        enquiry.conversation_id
                    ),
                    interaction_id=(
                        enquiry.interaction_id
                    ),
                    analysis_type="ENQUIRY_TRIAGE",
                    force_refresh=force_refresh,
                    metadata={
                        "workflow": "enquiry_triage",
                        "source": enquiry.source,
                    },
                ),
                prompt_values={
                    "content": content,
                    "customer_context": (
                        customer_context
                        or "No additional customer context available."
                    ),
                },
            )
        except AIServiceError as exc:
            updated = enquiries.mark_needs_review(
                organization_uuid,
                enquiry_uuid,
            )

            return {
                "status": "degraded",
                "workflow": "enquiry_triage",
                "organization_id": organization_id,
                "enquiry_id": enquiry_id,
                "decision": "NEEDS_REVIEW",
                "reason": (
                    "AI triage was unavailable. "
                    "Enquiry was routed to human review."
                ),
                "error_code": exc.error_code,
                "enquiry_status": updated.status,
            }

        result = (
            EnquiryTriageResult.model_validate(
                response.result
            )
        )

        decision = result.decision

        if (
            decision == "NEEDS_REVIEW"
            or response.requires_review
        ):
            updated = (
                enquiries.mark_needs_review(
                    organization_uuid,
                    enquiry_uuid,
                )
            )
            final_decision = (
                "NEEDS_REVIEW"
            )

        elif decision == "GENERAL_ENQUIRY":
            updated = (
                enquiries.mark_general_enquiry(
                    organization_uuid,
                    enquiry_uuid,
                )
            )
            final_decision = (
                "GENERAL_ENQUIRY"
            )

        else:
            from sqlalchemy import select

            from app.models.lead_status import LeadStatus
            from app.schemas.lead import LeadCreate

            new_status = db.execute(
                select(LeadStatus).where(
                    LeadStatus.organization_id
                    == organization_uuid,
                    LeadStatus.key == "NEW",
                    LeadStatus.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if new_status is None:
                updated = enquiries.mark_needs_review(
                    organization_uuid,
                    enquiry_uuid,
                )

                return {
                    "status": "degraded",
                    "workflow": "enquiry_triage",
                    "organization_id": organization_id,
                    "enquiry_id": enquiry_id,
                    "decision": "NEEDS_REVIEW",
                    "reason": (
                        "AI classified the enquiry as a sales lead, "
                        "but no active NEW lead status is configured."
                    ),
                    "enquiry_status": updated.status,
                }

            lead = enquiries.convert_to_lead(
                organization_uuid,
                enquiry_uuid,
                LeadCreate(
                    organization_id=organization_uuid,
                    customer_id=enquiry.customer_id,
                    status_id=new_status.id,
                    source_enquiry_id=enquiry.id,
                    source=enquiry.source,
                    original_source=(
                        enquiry.original_source
                        or enquiry.source
                    ),
                    campaign_id=enquiry.campaign_id,
                    ad_id=enquiry.ad_id,
                    requirement=result.requirement,
                    original_enquiry=content,
                ),
                assignment_reason=(
                    "Automatically converted by AI enquiry triage"
                ),
            )

            updated = enquiries.get(
                organization_uuid,
                enquiry_uuid,
            )

            from app.services.assignment_service import (
                AssignmentService,
            )

            lead = AssignmentService(
                db
            ).auto_assign_least_loaded(
                organization_uuid,
                lead.id,
                reason=(
                    "Automatically assigned after "
                    "AI enquiry conversion."
                ),
            )

            lead_ai_task = analyze_lead_task.delay(
                organization_id,
                str(lead.id),
                content,
                customer_context,
                "",
                content,
            )

            final_decision = "SALES_LEAD"

        return {
            "status": "completed",
            "workflow": "enquiry_triage",
            "organization_id": organization_id,
            "enquiry_id": enquiry_id,
            "analysis_id": str(
                response.analysis_id
            ),
            "decision": final_decision,
            "confidence": (
                float(result.confidence)
            ),
            "requires_review": (
                response.requires_review
            ),
            "enquiry_status": (
                updated.status
            ),
            "lead_id": (
                str(lead.id)
                if final_decision == "SALES_LEAD"
                else None
            ),
            "lead_ai_task_id": (
                lead_ai_task.id
                if final_decision == "SALES_LEAD"
                else None
            ),
            "result": _json_safe(
                result
            ),
        }

    finally:
        db.close()
