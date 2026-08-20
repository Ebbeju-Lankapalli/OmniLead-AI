"""Persistent AI analysis and human-review business logic."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.guards.confidence import (
    DEFAULT_REVIEW_THRESHOLD,
    evaluate_confidence,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.ai_analysis import AIAnalysis
from app.models.ai_feedback import AIFeedback
from app.models.customer import Customer
from app.models.enquiry import Enquiry
from app.models.lead import Lead
from app.models.organization import Organization
from app.repositories.ai_analyses import (
    AIAnalysisRepository,
    AIFeedbackRepository,
)
from app.repositories.users import UserRepository
from app.schemas.ai import (
    AIAnalysisCreate,
    AIAnalysisUpdate,
    AIFeedbackCreate,
    AIReviewQueueItem,
    AIReviewQueueResponse,
)


class AIService:
    """Persist and review auditable OmniLead AI analyses."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.analyses = AIAnalysisRepository(db)
        self.feedback = AIFeedbackRepository(db)
        self.users = UserRepository(db)

    def get_analysis(
        self,
        organization_id: UUID,
        analysis_id: UUID,
    ) -> AIAnalysis:
        """Return an organization-scoped AI analysis."""

        analysis = self.analyses.get(analysis_id)

        if (
            analysis is None
            or analysis.organization_id != organization_id
        ):
            raise NotFoundError(
                "AI analysis not found.",
                details={
                    "analysis_id": str(analysis_id),
                },
            )

        return analysis

    def create_analysis(
        self,
        payload: AIAnalysisCreate,
        *,
        deduplicate: bool = True,
        commit: bool = True,
    ) -> AIAnalysis:
        """Create an auditable AI analysis record."""

        self._validate_organization(
            payload.organization_id
        )

        self._validate_entity_links(payload)

        if (
            deduplicate
            and payload.input_hash is not None
        ):
            existing = self.analyses.get_by_input_hash(
                payload.organization_id,
                payload.analysis_type,
                payload.input_hash,
            )

            if existing is not None:
                return existing

        analysis = AIAnalysis(
            **payload.model_dump()
        )

        try:
            self.analyses.add(analysis)

            if commit:
                self.db.commit()
                self.db.refresh(analysis)
            else:
                self.db.flush()

        except Exception:
            self.db.rollback()
            raise

        return analysis

    def update_analysis(
        self,
        organization_id: UUID,
        analysis_id: UUID,
        payload: AIAnalysisUpdate,
        *,
        commit: bool = True,
    ) -> AIAnalysis:
        """Update result and observability fields."""

        analysis = self.get_analysis(
            organization_id,
            analysis_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return analysis

        try:
            self.analyses.update(
                analysis,
                **values,
            )

            if commit:
                self.db.commit()
                self.db.refresh(analysis)
            else:
                self.db.flush()

        except Exception:
            self.db.rollback()
            raise

        return analysis

    def complete_analysis(
        self,
        organization_id: UUID,
        analysis_id: UUID,
        *,
        result: dict[str, Any],
        confidence: float | Decimal | None = None,
        latency_ms: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> AIAnalysis:
        """Mark an AI analysis as successfully completed."""

        decimal_confidence = self._decimal_confidence(
            confidence
        )

        return self.update_analysis(
            organization_id,
            analysis_id,
            AIAnalysisUpdate(
                result=result,
                model_confidence=decimal_confidence,
                status="COMPLETED",
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                error_code=None,
                error_message=None,
            ),
        )

    def fail_analysis(
        self,
        organization_id: UUID,
        analysis_id: UUID,
        *,
        error_code: str,
        error_message: str,
        latency_ms: int | None = None,
    ) -> AIAnalysis:
        """Mark an AI analysis as failed."""

        return self.update_analysis(
            organization_id,
            analysis_id,
            AIAnalysisUpdate(
                status="FAILED",
                latency_ms=latency_ms,
                error_code=error_code,
                error_message=error_message,
            ),
        )

    def get_cached_analysis(
        self,
        organization_id: UUID,
        analysis_type: str,
        input_hash: str,
    ) -> AIAnalysis | None:
        """Return a matching previously completed AI result."""

        analysis = self.analyses.get_by_input_hash(
            organization_id,
            analysis_type,
            input_hash,
        )

        if (
            analysis is None
            or analysis.status != "COMPLETED"
        ):
            return None

        return analysis

    def submit_feedback(
        self,
        payload: AIFeedbackCreate,
    ) -> AIFeedback:
        """Submit one human review for an AI analysis."""

        analysis = self.get_analysis(
            payload.organization_id,
            payload.ai_analysis_id,
        )

        reviewer = self.users.get(
            payload.reviewed_by_user_id
        )

        if (
            reviewer is None
            or reviewer.organization_id
            != payload.organization_id
        ):
            raise NotFoundError(
                "AI reviewer not found.",
                details={
                    "user_id": str(
                        payload.reviewed_by_user_id
                    ),
                },
            )

        if not reviewer.is_active:
            raise ValidationError(
                "Inactive user cannot review AI analysis."
            )

        if self.feedback.has_feedback(
            payload.organization_id,
            payload.ai_analysis_id,
        ):
            raise ConflictError(
                "AI analysis has already been reviewed.",
                details={
                    "analysis_id": str(analysis.id),
                },
            )

        if payload.original_result != analysis.result:
            raise ValidationError(
                "Feedback original_result does not match "
                "the persisted AI result."
            )

        feedback = AIFeedback(
            **payload.model_dump()
        )

        try:
            self.feedback.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)

        except Exception:
            self.db.rollback()
            raise

        return feedback

    def get_latest_feedback(
        self,
        organization_id: UUID,
        analysis_id: UUID,
    ) -> AIFeedback | None:
        """Return latest human feedback for an analysis."""

        self.get_analysis(
            organization_id,
            analysis_id,
        )

        return self.feedback.get_latest_for_analysis(
            organization_id,
            analysis_id,
        )

    def list_analyses(
        self,
        organization_id: UUID,
        *,
        analysis_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIAnalysis]:
        """Return filtered organization AI history."""

        self._validate_organization(
            organization_id
        )

        return self.analyses.list_by_organization(
            organization_id,
            analysis_type=analysis_type,
            status=status,
            offset=offset,
            limit=limit,
        )

    def review_queue(
        self,
        organization_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        include_reviewed: bool = False,
    ) -> AIReviewQueueResponse:
        """Return completed analyses for human-review workflows."""

        self._validate_organization(
            organization_id
        )

        if page < 1:
            raise ValidationError(
                "Review queue page must be at least 1."
            )

        if not 1 <= page_size <= 100:
            raise ValidationError(
                "Review queue page size must be between 1 and 100."
            )

        statement = (
            select(AIAnalysis)
            .where(
                AIAnalysis.organization_id == organization_id,
                AIAnalysis.status == "COMPLETED",
                (
                    AIAnalysis.model_confidence.is_(None)
                    | (
                        AIAnalysis.model_confidence
                        < DEFAULT_REVIEW_THRESHOLD
                    )
                ),
            )
        )

        if not include_reviewed:
            reviewed_ids = select(
                AIFeedback.ai_analysis_id
            ).where(
                AIFeedback.organization_id == organization_id
            )

            statement = statement.where(
                AIAnalysis.id.not_in(reviewed_ids)
            )

        count_statement = select(
            func.count()
        ).select_from(
            statement.order_by(None).subquery()
        )

        total_items = int(
            self.db.scalar(count_statement)
            or 0
        )

        offset = (page - 1) * page_size

        analyses = self.db.scalars(
            statement
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id,
            )
            .offset(offset)
            .limit(page_size)
        ).all()

        items = [
            self._review_queue_item(
                analysis
            )
            for analysis in analyses
        ]

        total_pages = (
            math.ceil(total_items / page_size)
            if total_items
            else 0
        )

        return AIReviewQueueResponse(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    @staticmethod
    def build_input_hash(
        *,
        analysis_type: str,
        content: Any,
    ) -> str:
        """Build deterministic SHA-256 hash for AI-input deduplication."""

        normalized_type = (
            analysis_type.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        canonical = json.dumps(
            {
                "analysis_type": normalized_type,
                "content": content,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    def _review_queue_item(
        self,
        analysis: AIAnalysis,
    ) -> AIReviewQueueItem:
        """Convert an analysis into a human-review queue item."""

        latest_feedback = (
            self.feedback.get_latest_for_analysis(
                analysis.organization_id,
                analysis.id,
            )
        )

        confidence = (
            float(analysis.model_confidence)
            if analysis.model_confidence is not None
            else None
        )

        decision = evaluate_confidence(
            confidence
        )

        customer_name = None

        if analysis.customer_id is not None:
            customer = self.db.get(
                Customer,
                analysis.customer_id,
            )

            if customer is not None:
                customer_name = customer.full_name

        lead_status_name = None

        if analysis.lead is not None:
            lead_status_name = (
                analysis.lead.status.name
                if analysis.lead.status is not None
                else None
            )

        return AIReviewQueueItem(
            analysis=analysis,
            customer_name=customer_name,
            lead_status_name=lead_status_name,
            result=analysis.result,
            has_feedback=latest_feedback is not None,
            feedback_decision=(
                latest_feedback.decision
                if latest_feedback is not None
                else None
            ),
            requires_review=decision.requires_review,
            review_reason=decision.reason,
        )

    def _validate_organization(
        self,
        organization_id: UUID,
    ) -> Organization:
        """Validate organization existence."""

        organization = self.db.get(
            Organization,
            organization_id,
        )

        if organization is None:
            raise NotFoundError(
                "Organization not found.",
                details={
                    "organization_id": str(
                        organization_id
                    ),
                },
            )

        return organization

    def _validate_entity_links(
        self,
        payload: AIAnalysisCreate,
    ) -> None:
        """Validate linked CRM entities belong to the same organization."""

        checks = (
            (
                "customer_id",
                payload.customer_id,
                Customer,
            ),
            (
                "lead_id",
                payload.lead_id,
                Lead,
            ),
            (
                "enquiry_id",
                payload.enquiry_id,
                Enquiry,
            ),
        )

        for field_name, entity_id, model in checks:
            if entity_id is None:
                continue

            entity = self.db.get(
                model,
                entity_id,
            )

            if (
                entity is None
                or entity.organization_id
                != payload.organization_id
            ):
                raise NotFoundError(
                    f"{field_name.removesuffix('_id').title()} not found.",
                    details={
                        field_name: str(entity_id),
                    },
                )

    @staticmethod
    def _decimal_confidence(
        confidence: float | Decimal | None,
    ) -> Decimal | None:
        """Convert confidence to database-safe Decimal."""

        if confidence is None:
            return None

        value = Decimal(
            str(confidence)
        )

        if value < 0 or value > 1:
            raise ValidationError(
                "AI confidence must be between 0 and 1."
            )

        return value.quantize(
            Decimal("0.0001")
        )
