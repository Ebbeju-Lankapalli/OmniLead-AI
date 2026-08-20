"""Dashboard aggregation business logic."""

from __future__ import annotations

from datetime import datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_TIMEZONE
from app.core.exceptions import NotFoundError
from app.db.types import (
    AIReviewDecision,
    EnquiryStatus,
    FollowUpStatus,
)
from app.models.ai_analysis import AIAnalysis
from app.models.ai_feedback import AIFeedback
from app.models.enquiry import Enquiry
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.organization import Organization
from app.models.user import User
from app.repositories.followups import FollowUpRepository
from app.repositories.interactions import InteractionRepository
from app.repositories.leads import LeadRepository
from app.schemas.dashboard import (
    DashboardAIReviewMetrics,
    DashboardFollowUp,
    DashboardIntentMetric,
    DashboardMetrics,
    DashboardPriorityLead,
    DashboardRecentActivity,
    DashboardResponse,
    DashboardSourceMetric,
    DashboardStatusMetric,
    DashboardTeamMetric,
)


class DashboardService:
    """Build the operational OmniLead AI dashboard."""

    HIGH_PRIORITY_THRESHOLD = 80
    PRIORITY_QUEUE_LIMIT = 10
    FOLLOWUP_QUEUE_LIMIT = 10
    RECENT_ACTIVITY_LIMIT = 10

    def __init__(self, db: Session) -> None:
        self.db = db
        self.leads = LeadRepository(db)
        self.followups = FollowUpRepository(db)
        self.interactions = InteractionRepository(db)

    def get_dashboard(
        self,
        organization_id: UUID,
        *,
        generated_at: datetime | None = None,
    ) -> DashboardResponse:
        """Return the complete organization dashboard."""

        organization = self.db.get(
            Organization,
            organization_id,
        )

        if organization is None:
            raise NotFoundError(
                "Organization not found.",
                details={
                    "organization_id": str(organization_id),
                },
            )

        now = generated_at or datetime.now().astimezone()

        day_start, day_end = self._local_day_bounds(
            now,
            organization.timezone or DEFAULT_TIMEZONE,
        )

        metrics = self._build_metrics(
            organization_id,
            now=now,
            day_start=day_start,
            day_end=day_end,
        )

        return DashboardResponse(
            generated_at=now,
            metrics=metrics,
            source_breakdown=self._source_breakdown(
                organization_id,
                metrics.total_leads,
            ),
            status_breakdown=self._status_breakdown(
                organization_id,
                metrics.total_leads,
            ),
            purchase_intent_breakdown=self._intent_breakdown(
                organization_id,
                metrics.total_leads,
            ),
            priority_leads=self._priority_leads(
                organization_id,
            ),
            upcoming_followups=self._upcoming_followups(
                organization_id,
                now,
            ),
            recent_activity=self._recent_activity(
                organization_id,
            ),
            ai_review_metrics=self._ai_review_metrics(
                organization_id,
            ),
            team_metrics=self._team_metrics(
                organization_id,
                now,
            ),
        )

    def _build_metrics(
        self,
        organization_id: UUID,
        *,
        now: datetime,
        day_start: datetime,
        day_end: datetime,
    ) -> DashboardMetrics:
        """Build top-level operational KPIs."""

        total_leads = int(
            self.db.scalar(
                select(func.count())
                .select_from(Lead)
                .where(
                    Lead.organization_id == organization_id,
                    Lead.archived_at.is_(None),
                )
            )
            or 0
        )

        active_leads = self.leads.count_active(
            organization_id
        )

        high_priority_leads = int(
            self.db.scalar(
                select(func.count())
                .select_from(Lead)
                .where(
                    Lead.organization_id == organization_id,
                    Lead.archived_at.is_(None),
                    Lead.priority_score.is_not(None),
                    Lead.priority_score
                    >= self.HIGH_PRIORITY_THRESHOLD,
                )
            )
            or 0
        )

        new_enquiries = int(
            self.db.scalar(
                select(func.count())
                .select_from(Enquiry)
                .where(
                    Enquiry.organization_id == organization_id,
                    Enquiry.status == EnquiryStatus.NEW.value,
                )
            )
            or 0
        )

        enquiries_needing_review = int(
            self.db.scalar(
                select(func.count())
                .select_from(Enquiry)
                .where(
                    Enquiry.organization_id == organization_id,
                    Enquiry.status
                    == EnquiryStatus.NEEDS_REVIEW.value,
                )
            )
            or 0
        )

        followups_due_today = int(
            self.db.scalar(
                select(func.count())
                .select_from(FollowUp)
                .where(
                    FollowUp.organization_id == organization_id,
                    FollowUp.status
                    == FollowUpStatus.SCHEDULED.value,
                    FollowUp.scheduled_at >= day_start,
                    FollowUp.scheduled_at < day_end,
                )
            )
            or 0
        )

        overdue_followups = int(
            self.db.scalar(
                select(func.count())
                .select_from(FollowUp)
                .where(
                    FollowUp.organization_id == organization_id,
                    FollowUp.status
                    == FollowUpStatus.SCHEDULED.value,
                    FollowUp.scheduled_at < now,
                )
            )
            or 0
        )

        converted_leads = self.leads.count_converted(
            organization_id
        )

        average_lead_score = self.db.scalar(
            select(func.avg(Lead.lead_score)).where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
                Lead.lead_score.is_not(None),
            )
        )

        average_priority_score = self.db.scalar(
            select(func.avg(Lead.priority_score)).where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
                Lead.priority_score.is_not(None),
            )
        )

        return DashboardMetrics(
            total_leads=total_leads,
            active_leads=active_leads,
            high_priority_leads=high_priority_leads,
            new_enquiries=new_enquiries,
            enquiries_needing_review=enquiries_needing_review,
            followups_due_today=followups_due_today,
            overdue_followups=overdue_followups,
            converted_leads=converted_leads,
            conversion_rate=self._percentage(
                converted_leads,
                total_leads,
            ),
            average_lead_score=self._optional_float(
                average_lead_score
            ),
            average_priority_score=self._optional_float(
                average_priority_score
            ),
        )

    def _source_breakdown(
        self,
        organization_id: UUID,
        total_leads: int,
    ) -> list[DashboardSourceMetric]:
        """Build lead counts grouped by acquisition source."""

        rows = self.db.execute(
            select(
                Lead.source,
                func.count(Lead.id),
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
            )
            .group_by(Lead.source)
            .order_by(func.count(Lead.id).desc())
        ).all()

        return [
            DashboardSourceMetric(
                source=source,
                count=count,
                percentage=self._percentage(
                    count,
                    total_leads,
                ),
            )
            for source, count in rows
        ]

    def _status_breakdown(
        self,
        organization_id: UUID,
        total_leads: int,
    ) -> list[DashboardStatusMetric]:
        """Build lead counts grouped by lifecycle status."""

        rows = self.db.execute(
            select(
                LeadStatus.id,
                LeadStatus.key,
                LeadStatus.name,
                func.count(Lead.id),
            )
            .join(
                Lead,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
            )
            .group_by(
                LeadStatus.id,
                LeadStatus.key,
                LeadStatus.name,
                LeadStatus.display_order,
            )
            .order_by(
                LeadStatus.display_order,
                LeadStatus.name,
            )
        ).all()

        return [
            DashboardStatusMetric(
                status_id=status_id,
                status_key=status_key,
                status_name=status_name,
                count=count,
                percentage=self._percentage(
                    count,
                    total_leads,
                ),
            )
            for (
                status_id,
                status_key,
                status_name,
                count,
            ) in rows
        ]

    def _intent_breakdown(
        self,
        organization_id: UUID,
        total_leads: int,
    ) -> list[DashboardIntentMetric]:
        """Build lead counts grouped by purchase intent."""

        rows = self.db.execute(
            select(
                Lead.purchase_intent,
                func.count(Lead.id),
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.archived_at.is_(None),
                Lead.purchase_intent.is_not(None),
            )
            .group_by(Lead.purchase_intent)
            .order_by(func.count(Lead.id).desc())
        ).all()

        return [
            DashboardIntentMetric(
                purchase_intent=purchase_intent,
                count=count,
                percentage=self._percentage(
                    count,
                    total_leads,
                ),
            )
            for purchase_intent, count in rows
        ]

    def _priority_leads(
        self,
        organization_id: UUID,
    ) -> list[DashboardPriorityLead]:
        """Build the dashboard priority queue."""

        leads = self.leads.list_priority_queue(
            organization_id,
            minimum_priority_score=self.HIGH_PRIORITY_THRESHOLD,
            limit=self.PRIORITY_QUEUE_LIMIT,
        )

        return [
            DashboardPriorityLead(
                lead_id=lead.id,
                customer_id=lead.customer_id,
                customer_name=lead.customer.full_name,
                company_name=lead.customer.company_name,
                product_id=lead.product_id,
                product_name=(
                    lead.product.name
                    if lead.product is not None
                    else None
                ),
                assigned_to_user_id=lead.assigned_to_user_id,
                assigned_to_name=(
                    lead.assignee.full_name
                    if lead.assignee is not None
                    else None
                ),
                status_id=lead.status_id,
                status_name=lead.status.name,
                source=lead.source,
                purchase_intent=lead.purchase_intent,
                lead_score=lead.lead_score,
                priority_score=lead.priority_score,
                followup_risk_score=lead.followup_risk_score,
                next_best_action=lead.next_best_action,
                next_followup_at=lead.next_followup_at,
                last_contact_at=lead.last_contact_at,
            )
            for lead in leads
        ]

    def _upcoming_followups(
        self,
        organization_id: UUID,
        now: datetime,
    ) -> list[DashboardFollowUp]:
        """Return the nearest scheduled follow-ups."""

        rows = self.db.scalars(
            select(FollowUp)
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.status
                == FollowUpStatus.SCHEDULED.value,
                FollowUp.scheduled_at >= now,
            )
            .order_by(
                FollowUp.scheduled_at,
                FollowUp.id,
            )
            .limit(self.FOLLOWUP_QUEUE_LIMIT)
        ).all()

        return [
            DashboardFollowUp(
                followup_id=followup.id,
                lead_id=followup.lead_id,
                customer_id=followup.customer_id,
                assigned_to_user_id=followup.assigned_to_user_id,
                customer_name=followup.customer.full_name,
                assigned_to_name=followup.assigned_to.full_name,
                followup_type=followup.followup_type,
                status=followup.status,
                scheduled_at=followup.scheduled_at,
                reminder_minutes_before=(
                    followup.reminder_minutes_before
                ),
                notes=followup.notes,
            )
            for followup in rows
        ]

    def _recent_activity(
        self,
        organization_id: UUID,
    ) -> list[DashboardRecentActivity]:
        """Return recent CRM timeline activity."""

        rows = self.interactions.list_by_organization(
            organization_id,
            newest_first=True,
            limit=self.RECENT_ACTIVITY_LIMIT,
        )

        return [
            DashboardRecentActivity(
                interaction_id=interaction.id,
                customer_id=interaction.customer_id,
                lead_id=interaction.lead_id,
                conversation_id=interaction.conversation_id,
                actor_user_id=interaction.actor_user_id,
                customer_name=interaction.customer.full_name,
                actor_name=(
                    interaction.actor.full_name
                    if interaction.actor is not None
                    else None
                ),
                interaction_type=interaction.interaction_type,
                direction=interaction.direction,
                channel=interaction.channel,
                content=interaction.content,
                occurred_at=interaction.occurred_at,
            )
            for interaction in rows
        ]

    def _ai_review_metrics(
        self,
        organization_id: UUID,
    ) -> DashboardAIReviewMetrics:
        """Build AI execution and review workload metrics."""

        total_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
        )

        completed_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.status == "COMPLETED",
        )

        failed_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.status == "FAILED",
        )

        reviewed_analysis_ids = select(
            AIFeedback.ai_analysis_id
        ).where(
            AIFeedback.organization_id == organization_id
        )

        pending_reviews = int(
            self.db.scalar(
                select(func.count())
                .select_from(AIAnalysis)
                .where(
                    AIAnalysis.organization_id
                    == organization_id,
                    AIAnalysis.status == "COMPLETED",
                    AIAnalysis.id.not_in(
                        reviewed_analysis_ids
                    ),
                )
            )
            or 0
        )

        accepted_reviews = self._count(
            AIFeedback,
            AIFeedback.organization_id == organization_id,
            AIFeedback.decision
            == AIReviewDecision.ACCEPTED.value,
        )

        edited_reviews = self._count(
            AIFeedback,
            AIFeedback.organization_id == organization_id,
            AIFeedback.decision
            == AIReviewDecision.EDITED.value,
        )

        rejected_reviews = self._count(
            AIFeedback,
            AIFeedback.organization_id == organization_id,
            AIFeedback.decision
            == AIReviewDecision.REJECTED.value,
        )

        return DashboardAIReviewMetrics(
            total_analyses=total_analyses,
            completed_analyses=completed_analyses,
            failed_analyses=failed_analyses,
            pending_reviews=pending_reviews,
            accepted_reviews=accepted_reviews,
            edited_reviews=edited_reviews,
            rejected_reviews=rejected_reviews,
        )

    def _team_metrics(
        self,
        organization_id: UUID,
        now: datetime,
    ) -> list[DashboardTeamMetric]:
        """Build compact workload metrics for active team members."""

        users = self.db.scalars(
            select(User)
            .where(
                User.organization_id == organization_id,
                User.is_active.is_(True),
            )
            .order_by(
                User.full_name,
                User.id,
            )
        ).all()

        metrics: list[DashboardTeamMetric] = []

        for user in users:
            active_leads = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Lead)
                    .join(
                        LeadStatus,
                        Lead.status_id == LeadStatus.id,
                    )
                    .where(
                        Lead.organization_id
                        == organization_id,
                        Lead.assigned_to_user_id == user.id,
                        Lead.archived_at.is_(None),
                        LeadStatus.is_terminal.is_(False),
                    )
                )
                or 0
            )

            due_followups = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(FollowUp)
                    .where(
                        FollowUp.organization_id
                        == organization_id,
                        FollowUp.assigned_to_user_id
                        == user.id,
                        FollowUp.status
                        == FollowUpStatus.SCHEDULED.value,
                        FollowUp.scheduled_at <= now,
                    )
                )
                or 0
            )

            completed_followups = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(FollowUp)
                    .where(
                        FollowUp.organization_id
                        == organization_id,
                        FollowUp.assigned_to_user_id
                        == user.id,
                        FollowUp.status
                        == FollowUpStatus.COMPLETED.value,
                    )
                )
                or 0
            )

            converted_leads = int(
                self.db.scalar(
                    select(func.count())
                    .select_from(Lead)
                    .join(
                        LeadStatus,
                        Lead.status_id == LeadStatus.id,
                    )
                    .where(
                        Lead.organization_id
                        == organization_id,
                        Lead.assigned_to_user_id == user.id,
                        LeadStatus.is_won.is_(True),
                    )
                )
                or 0
            )

            metrics.append(
                DashboardTeamMetric(
                    user_id=user.id,
                    full_name=user.full_name,
                    active_leads=active_leads,
                    due_followups=due_followups,
                    completed_followups=completed_followups,
                    converted_leads=converted_leads,
                )
            )

        return metrics

    def _count(
        self,
        model,
        *conditions,
    ) -> int:
        """Return a simple filtered row count."""

        return int(
            self.db.scalar(
                select(func.count())
                .select_from(model)
                .where(*conditions)
            )
            or 0
        )

    @staticmethod
    def _percentage(
        numerator: int,
        denominator: int,
    ) -> float:
        """Return a safe percentage rounded to two decimals."""

        if denominator <= 0:
            return 0.0

        return round(
            numerator / denominator * 100,
            2,
        )

    @staticmethod
    def _optional_float(
        value,
    ) -> float | None:
        """Convert nullable SQL numeric values to rounded floats."""

        if value is None:
            return None

        return round(float(value), 2)

    @staticmethod
    def _local_day_bounds(
        moment: datetime,
        timezone_name: str,
    ) -> tuple[datetime, datetime]:
        """Return timezone-aware start/end boundaries for a local day."""

        try:
            timezone = ZoneInfo(timezone_name)
        except Exception:
            timezone = ZoneInfo(DEFAULT_TIMEZONE)

        local_moment = moment.astimezone(timezone)

        start = datetime.combine(
            local_moment.date(),
            time.min,
            tzinfo=timezone,
        )

        end = datetime.combine(
            local_moment.date().fromordinal(
                local_moment.date().toordinal() + 1
            ),
            time.min,
            tzinfo=timezone,
        )

        return start, end
