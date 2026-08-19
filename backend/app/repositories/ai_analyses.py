"""AI analysis and human-feedback repository."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select

from app.db.types import AIReviewDecision
from app.models.ai_analysis import AIAnalysis
from app.models.ai_feedback import AIFeedback
from app.repositories.base import BaseRepository


class AIAnalysisRepository(BaseRepository[AIAnalysis]):
    """Data-access operations for persisted AI analyses."""

    model = AIAnalysis

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        analysis_type: str | None = None,
        status: str | None = None,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        enquiry_id: UUID | None = None,
        conversation_id: UUID | None = None,
        interaction_id: UUID | None = None,
        call_recording_id: UUID | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIAnalysis]:
        """Return filtered AI analyses for one organization."""

        statement = select(AIAnalysis).where(
            AIAnalysis.organization_id == organization_id
        )

        if analysis_type is not None:
            normalized_type = self._normalize_enum_like(
                analysis_type
            )

            if normalized_type:
                statement = statement.where(
                    AIAnalysis.analysis_type == normalized_type
                )

        if status is not None:
            normalized_status = self._normalize_enum_like(
                status
            )

            if normalized_status:
                statement = statement.where(
                    AIAnalysis.status == normalized_status
                )

        if customer_id is not None:
            statement = statement.where(
                AIAnalysis.customer_id == customer_id
            )

        if lead_id is not None:
            statement = statement.where(
                AIAnalysis.lead_id == lead_id
            )

        if enquiry_id is not None:
            statement = statement.where(
                AIAnalysis.enquiry_id == enquiry_id
            )

        if conversation_id is not None:
            statement = statement.where(
                AIAnalysis.conversation_id == conversation_id
            )

        if interaction_id is not None:
            statement = statement.where(
                AIAnalysis.interaction_id == interaction_id
            )

        if call_recording_id is not None:
            statement = statement.where(
                AIAnalysis.call_recording_id == call_recording_id
            )

        if created_from is not None:
            statement = statement.where(
                AIAnalysis.created_at >= created_from
            )

        if created_to is not None:
            statement = statement.where(
                AIAnalysis.created_at <= created_to
            )

        statement = (
            statement
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_by_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        analysis_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIAnalysis]:
        """Return AI analysis history for one lead."""

        return self.list_by_organization(
            organization_id,
            lead_id=lead_id,
            analysis_type=analysis_type,
            offset=offset,
            limit=limit,
        )

    def list_by_enquiry(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        *,
        analysis_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIAnalysis]:
        """Return AI analysis history for one enquiry."""

        return self.list_by_organization(
            organization_id,
            enquiry_id=enquiry_id,
            analysis_type=analysis_type,
            offset=offset,
            limit=limit,
        )

    def get_latest_for_lead(
        self,
        organization_id: UUID,
        lead_id: UUID,
        *,
        analysis_type: str | None = None,
    ) -> AIAnalysis | None:
        """Return the latest AI analysis for a lead."""

        statement = select(AIAnalysis).where(
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.lead_id == lead_id,
        )

        if analysis_type is not None:
            normalized_type = self._normalize_enum_like(
                analysis_type
            )

            if normalized_type:
                statement = statement.where(
                    AIAnalysis.analysis_type == normalized_type
                )

        statement = (
            statement
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def get_latest_for_enquiry(
        self,
        organization_id: UUID,
        enquiry_id: UUID,
        *,
        analysis_type: str | None = None,
    ) -> AIAnalysis | None:
        """Return the latest AI analysis for an enquiry."""

        statement = select(AIAnalysis).where(
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.enquiry_id == enquiry_id,
        )

        if analysis_type is not None:
            normalized_type = self._normalize_enum_like(
                analysis_type
            )

            if normalized_type:
                statement = statement.where(
                    AIAnalysis.analysis_type == normalized_type
                )

        statement = (
            statement
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def get_by_input_hash(
        self,
        organization_id: UUID,
        analysis_type: str,
        input_hash: str,
    ) -> AIAnalysis | None:
        """Return the latest matching analysis for an input hash."""

        normalized_type = self._normalize_enum_like(
            analysis_type
        )
        normalized_hash = input_hash.strip()

        if not normalized_type or not normalized_hash:
            return None

        statement = (
            select(AIAnalysis)
            .where(
                AIAnalysis.organization_id == organization_id,
                AIAnalysis.analysis_type == normalized_type,
                AIAnalysis.input_hash == normalized_hash,
            )
            .order_by(
                AIAnalysis.created_at.desc(),
                AIAnalysis.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def count_by_status(
        self,
        organization_id: UUID,
        status: str,
    ) -> int:
        """Return analysis count for one status."""

        normalized_status = self._normalize_enum_like(
            status
        )

        if not normalized_status:
            return 0

        statement = (
            select(func.count())
            .select_from(AIAnalysis)
            .where(
                AIAnalysis.organization_id == organization_id,
                AIAnalysis.status == normalized_status,
            )
        )

        return int(self.db.scalar(statement) or 0)

    def count_by_type(
        self,
        organization_id: UUID,
        analysis_type: str,
    ) -> int:
        """Return analysis count for one analysis type."""

        normalized_type = self._normalize_enum_like(
            analysis_type
        )

        if not normalized_type:
            return 0

        statement = (
            select(func.count())
            .select_from(AIAnalysis)
            .where(
                AIAnalysis.organization_id == organization_id,
                AIAnalysis.analysis_type == normalized_type,
            )
        )

        return int(self.db.scalar(statement) or 0)

    @staticmethod
    def _normalize_enum_like(value: str) -> str:
        """Normalize flexible enum-like database strings."""

        return (
            value.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )


class AIFeedbackRepository(BaseRepository[AIFeedback]):
    """Data-access operations for human AI reviews."""

    model = AIFeedback

    def list_by_analysis(
        self,
        organization_id: UUID,
        ai_analysis_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIFeedback]:
        """Return review history for one AI analysis."""

        statement = (
            select(AIFeedback)
            .where(
                AIFeedback.organization_id == organization_id,
                AIFeedback.ai_analysis_id == ai_analysis_id,
            )
            .order_by(
                AIFeedback.reviewed_at.desc(),
                AIFeedback.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def get_latest_for_analysis(
        self,
        organization_id: UUID,
        ai_analysis_id: UUID,
    ) -> AIFeedback | None:
        """Return the latest human review for an AI analysis."""

        statement = (
            select(AIFeedback)
            .where(
                AIFeedback.organization_id == organization_id,
                AIFeedback.ai_analysis_id == ai_analysis_id,
            )
            .order_by(
                AIFeedback.reviewed_at.desc(),
                AIFeedback.id,
            )
            .limit(1)
        )

        return self.db.scalar(statement)

    def has_feedback(
        self,
        organization_id: UUID,
        ai_analysis_id: UUID,
    ) -> bool:
        """Return whether an AI analysis has human feedback."""

        statement = (
            select(AIFeedback.id)
            .where(
                AIFeedback.organization_id == organization_id,
                AIFeedback.ai_analysis_id == ai_analysis_id,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_reviewer(
        self,
        organization_id: UUID,
        reviewed_by_user_id: UUID,
        *,
        decision: AIReviewDecision | str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[AIFeedback]:
        """Return feedback submitted by one team member."""

        statement = select(AIFeedback).where(
            AIFeedback.organization_id == organization_id,
            AIFeedback.reviewed_by_user_id == reviewed_by_user_id,
        )

        if decision is not None:
            normalized_decision = (
                decision.value
                if isinstance(decision, AIReviewDecision)
                else decision.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_decision:
                statement = statement.where(
                    AIFeedback.decision == normalized_decision
                )

        statement = (
            statement
            .order_by(
                AIFeedback.reviewed_at.desc(),
                AIFeedback.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def count_by_decision(
        self,
        organization_id: UUID,
        decision: AIReviewDecision | str,
    ) -> int:
        """Return feedback count for one review decision."""

        normalized_decision = (
            decision.value
            if isinstance(decision, AIReviewDecision)
            else decision.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if not normalized_decision:
            return 0

        statement = (
            select(func.count())
            .select_from(AIFeedback)
            .where(
                AIFeedback.organization_id == organization_id,
                AIFeedback.decision == normalized_decision,
            )
        )

        return int(self.db.scalar(statement) or 0)
