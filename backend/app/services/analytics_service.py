"""Historical analytics aggregation business logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_TIMEZONE
from app.core.exceptions import NotFoundError, ValidationError
from app.db.types import AIReviewDecision, FollowUpStatus
from app.models.ai_analysis import AIAnalysis
from app.models.ai_feedback import AIFeedback
from app.models.enquiry import Enquiry
from app.models.followup import FollowUp
from app.models.lead import Lead
from app.models.lead_status import LeadStatus
from app.models.organization import Organization
from app.models.product import Product
from app.models.user import User
from app.schemas.analytics import (
    AIAnalytics,
    AnalyticsDateRange,
    AnalyticsOverview,
    AnalyticsResponse,
    AnalyticsTrendPoint,
    ConversionAnalytics,
    FollowUpStatusAnalytics,
    FollowUpTypeAnalytics,
    LeadStatusAnalytics,
    ProductAnalytics,
    PurchaseIntentAnalytics,
    SourceAnalytics,
    TeamAnalytics,
)


class AnalyticsService:
    """Build historical CRM and AI analytics for an organization."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_analytics(
        self,
        organization_id: UUID,
        *,
        start_date: date,
        end_date: date,
        generated_at: datetime | None = None,
    ) -> AnalyticsResponse:
        """Return analytics for an inclusive organization-local date range."""

        if end_date < start_date:
            raise ValidationError(
                "Analytics end date cannot be before start date.",
                details={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            )

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

        range_start, range_end = self._date_range_bounds(
            start_date,
            end_date,
            organization.timezone or DEFAULT_TIMEZONE,
        )

        overview = self._overview(
            organization_id,
            range_start,
            range_end,
            now,
        )

        return AnalyticsResponse(
            generated_at=now,
            date_range=AnalyticsDateRange(
                start_date=start_date,
                end_date=end_date,
            ),
            overview=overview,
            conversion=self._conversion(
                organization_id,
                range_start,
                range_end,
            ),
            trend=self._trend(
                organization_id,
                start_date,
                end_date,
                range_start,
                range_end,
                organization.timezone or DEFAULT_TIMEZONE,
            ),
            source_performance=self._source_performance(
                organization_id,
                range_start,
                range_end,
            ),
            purchase_intent_breakdown=self._purchase_intents(
                organization_id,
                range_start,
                range_end,
                overview.total_leads,
            ),
            lead_status_breakdown=self._lead_statuses(
                organization_id,
                range_start,
                range_end,
                overview.total_leads,
            ),
            product_performance=self._products(
                organization_id,
                range_start,
                range_end,
            ),
            followup_type_performance=self._followup_types(
                organization_id,
                range_start,
                range_end,
                now,
            ),
            followup_status_breakdown=self._followup_statuses(
                organization_id,
                range_start,
                range_end,
                overview.total_followups,
            ),
            team_performance=self._team_performance(
                organization_id,
                range_start,
                range_end,
                now,
            ),
            ai_metrics=self._ai_metrics(
                organization_id,
                range_start,
                range_end,
            ),
        )

    def _overview(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        now: datetime,
    ) -> AnalyticsOverview:
        """Build high-level analytics KPIs."""

        total_enquiries = self._count(
            Enquiry,
            Enquiry.organization_id == organization_id,
            Enquiry.received_at >= start,
            Enquiry.received_at < end,
        )

        lead_conditions = (
            Lead.organization_id == organization_id,
            Lead.created_at >= start,
            Lead.created_at < end,
        )

        total_leads = self._count(
            Lead,
            *lead_conditions,
        )

        total_converted = self._count_converted(
            organization_id,
            start,
            end,
        )

        average_lead_score = self.db.scalar(
            select(func.avg(Lead.lead_score)).where(
                *lead_conditions,
                Lead.lead_score.is_not(None),
            )
        )

        average_priority_score = self.db.scalar(
            select(func.avg(Lead.priority_score)).where(
                *lead_conditions,
                Lead.priority_score.is_not(None),
            )
        )

        average_followup_risk = self.db.scalar(
            select(func.avg(Lead.followup_risk_score)).where(
                *lead_conditions,
                Lead.followup_risk_score.is_not(None),
            )
        )

        followup_conditions = (
            FollowUp.organization_id == organization_id,
            FollowUp.scheduled_at >= start,
            FollowUp.scheduled_at < end,
        )

        total_followups = self._count(
            FollowUp,
            *followup_conditions,
        )

        completed_followups = self._count(
            FollowUp,
            *followup_conditions,
            FollowUp.status == FollowUpStatus.COMPLETED.value,
        )

        overdue_followups = self._count(
            FollowUp,
            *followup_conditions,
            FollowUp.status == FollowUpStatus.SCHEDULED.value,
            FollowUp.scheduled_at < now,
        )

        return AnalyticsOverview(
            total_enquiries=total_enquiries,
            total_leads=total_leads,
            total_converted_leads=total_converted,
            conversion_rate=self._percentage(
                total_converted,
                total_leads,
            ),
            average_lead_score=self._optional_float(
                average_lead_score
            ),
            average_priority_score=self._optional_float(
                average_priority_score
            ),
            average_followup_risk_score=self._optional_float(
                average_followup_risk
            ),
            total_followups=total_followups,
            completed_followups=completed_followups,
            overdue_followups=overdue_followups,
            followup_completion_rate=self._percentage(
                completed_followups,
                total_followups,
            ),
        )

    def _conversion(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
    ) -> ConversionAnalytics:
        """Build overall conversion metrics."""

        total_leads = self._count(
            Lead,
            Lead.organization_id == organization_id,
            Lead.created_at >= start,
            Lead.created_at < end,
        )

        converted_rows = self.db.execute(
            select(
                Lead.created_at,
                Lead.closed_at,
            )
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
                LeadStatus.is_won.is_(True),
                Lead.closed_at.is_not(None),
            )
        ).all()

        converted_leads = len(converted_rows)

        days_to_conversion = [
            max(
                (closed_at - created_at).total_seconds()
                / 86400,
                0.0,
            )
            for created_at, closed_at in converted_rows
        ]

        average_days = (
            round(
                sum(days_to_conversion)
                / len(days_to_conversion),
                2,
            )
            if days_to_conversion
            else None
        )

        return ConversionAnalytics(
            total_leads=total_leads,
            converted_leads=converted_leads,
            conversion_rate=self._percentage(
                converted_leads,
                total_leads,
            ),
            average_days_to_conversion=average_days,
        )

    def _trend(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        start: datetime,
        end: datetime,
        timezone_name: str,
    ) -> list[AnalyticsTrendPoint]:
        """Build daily enquiry, lead, conversion, and follow-up trends."""

        timezone = self._timezone(timezone_name)

        buckets: dict[date, dict[str, int]] = defaultdict(
            lambda: {
                "enquiries": 0,
                "leads": 0,
                "converted_leads": 0,
                "completed_followups": 0,
            }
        )

        enquiry_times = self.db.scalars(
            select(Enquiry.received_at).where(
                Enquiry.organization_id == organization_id,
                Enquiry.received_at >= start,
                Enquiry.received_at < end,
            )
        ).all()

        for occurred_at in enquiry_times:
            buckets[
                occurred_at.astimezone(timezone).date()
            ]["enquiries"] += 1

        lead_rows = self.db.execute(
            select(
                Lead.created_at,
                Lead.closed_at,
                LeadStatus.is_won,
            )
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
            )
        ).all()

        for created_at, closed_at, is_won in lead_rows:
            created_day = created_at.astimezone(
                timezone
            ).date()

            buckets[created_day]["leads"] += 1

            if is_won and closed_at is not None:
                closed_day = closed_at.astimezone(
                    timezone
                ).date()

                if start_date <= closed_day <= end_date:
                    buckets[closed_day][
                        "converted_leads"
                    ] += 1

        completed_times = self.db.scalars(
            select(FollowUp.completed_at).where(
                FollowUp.organization_id == organization_id,
                FollowUp.status
                == FollowUpStatus.COMPLETED.value,
                FollowUp.completed_at.is_not(None),
                FollowUp.completed_at >= start,
                FollowUp.completed_at < end,
            )
        ).all()

        for completed_at in completed_times:
            buckets[
                completed_at.astimezone(timezone).date()
            ]["completed_followups"] += 1

        points: list[AnalyticsTrendPoint] = []

        current = start_date

        while current <= end_date:
            values = buckets[current]

            points.append(
                AnalyticsTrendPoint(
                    period_start=datetime.combine(
                        current,
                        time.min,
                        tzinfo=timezone,
                    ),
                    enquiries=values["enquiries"],
                    leads=values["leads"],
                    converted_leads=values[
                        "converted_leads"
                    ],
                    completed_followups=values[
                        "completed_followups"
                    ],
                )
            )

            current += timedelta(days=1)

        return points

    def _source_performance(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[SourceAnalytics]:
        """Build enquiry and lead performance by acquisition source."""

        enquiry_rows = self.db.execute(
            select(
                Enquiry.source,
                func.count(Enquiry.id),
            )
            .where(
                Enquiry.organization_id == organization_id,
                Enquiry.received_at >= start,
                Enquiry.received_at < end,
            )
            .group_by(Enquiry.source)
        ).all()

        enquiry_counts = dict(enquiry_rows)

        lead_rows = self.db.execute(
            select(
                Lead.source,
                func.count(Lead.id),
                func.avg(Lead.lead_score),
                func.avg(Lead.priority_score),
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
            )
            .group_by(Lead.source)
        ).all()

        lead_data = {
            source: (
                count,
                average_lead_score,
                average_priority_score,
            )
            for (
                source,
                count,
                average_lead_score,
                average_priority_score,
            ) in lead_rows
        }

        converted_rows = self.db.execute(
            select(
                Lead.source,
                func.count(Lead.id),
            )
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
                LeadStatus.is_won.is_(True),
            )
            .group_by(Lead.source)
        ).all()

        converted_counts = dict(converted_rows)

        sources = sorted(
            set(enquiry_counts)
            | set(lead_data)
            | set(converted_counts)
        )

        result: list[SourceAnalytics] = []

        for source in sources:
            (
                lead_count,
                average_lead_score,
                average_priority_score,
            ) = lead_data.get(
                source,
                (0, None, None),
            )

            converted = converted_counts.get(
                source,
                0,
            )

            result.append(
                SourceAnalytics(
                    source=source,
                    enquiries=enquiry_counts.get(
                        source,
                        0,
                    ),
                    leads=lead_count,
                    converted_leads=converted,
                    lead_conversion_rate=self._percentage(
                        converted,
                        lead_count,
                    ),
                    average_lead_score=self._optional_float(
                        average_lead_score
                    ),
                    average_priority_score=self._optional_float(
                        average_priority_score
                    ),
                )
            )

        result.sort(
            key=lambda item: (
                -item.leads,
                item.source.value,
            )
        )

        return result

    def _purchase_intents(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        total_leads: int,
    ) -> list[PurchaseIntentAnalytics]:
        """Build purchase-intent distribution."""

        rows = self.db.execute(
            select(
                Lead.purchase_intent,
                func.count(Lead.id),
                func.avg(Lead.lead_score),
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
                Lead.purchase_intent.is_not(None),
            )
            .group_by(Lead.purchase_intent)
            .order_by(func.count(Lead.id).desc())
        ).all()

        return [
            PurchaseIntentAnalytics(
                purchase_intent=purchase_intent,
                count=count,
                percentage=self._percentage(
                    count,
                    total_leads,
                ),
                average_lead_score=self._optional_float(
                    average_lead_score
                ),
            )
            for (
                purchase_intent,
                count,
                average_lead_score,
            ) in rows
        ]

    def _lead_statuses(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        total_leads: int,
    ) -> list[LeadStatusAnalytics]:
        """Build lead distribution by lifecycle status."""

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
                Lead.created_at >= start,
                Lead.created_at < end,
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
            LeadStatusAnalytics(
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

    def _products(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
    ) -> list[ProductAnalytics]:
        """Build lead and conversion performance by product."""

        rows = self.db.execute(
            select(
                Product.id,
                Product.name,
                func.count(Lead.id),
                func.avg(Lead.lead_score),
            )
            .join(
                Lead,
                Lead.product_id == Product.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
            )
            .group_by(
                Product.id,
                Product.name,
            )
        ).all()

        converted_rows = self.db.execute(
            select(
                Lead.product_id,
                func.count(Lead.id),
            )
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.created_at >= start,
                Lead.created_at < end,
                Lead.product_id.is_not(None),
                LeadStatus.is_won.is_(True),
            )
            .group_by(Lead.product_id)
        ).all()

        converted = dict(converted_rows)

        result = [
            ProductAnalytics(
                product_id=product_id,
                product_name=product_name,
                lead_count=lead_count,
                converted_leads=converted.get(
                    product_id,
                    0,
                ),
                conversion_rate=self._percentage(
                    converted.get(product_id, 0),
                    lead_count,
                ),
                average_lead_score=self._optional_float(
                    average_lead_score
                ),
            )
            for (
                product_id,
                product_name,
                lead_count,
                average_lead_score,
            ) in rows
        ]

        result.sort(
            key=lambda item: (
                -item.lead_count,
                item.product_name,
            )
        )

        return result

    def _followup_types(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        now: datetime,
    ) -> list[FollowUpTypeAnalytics]:
        """Build follow-up performance by communication type."""

        rows = self.db.execute(
            select(
                FollowUp.followup_type,
                func.count(FollowUp.id),
            )
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.scheduled_at >= start,
                FollowUp.scheduled_at < end,
            )
            .group_by(FollowUp.followup_type)
        ).all()

        completed_rows = self.db.execute(
            select(
                FollowUp.followup_type,
                func.count(FollowUp.id),
            )
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.scheduled_at >= start,
                FollowUp.scheduled_at < end,
                FollowUp.status
                == FollowUpStatus.COMPLETED.value,
            )
            .group_by(FollowUp.followup_type)
        ).all()

        overdue_rows = self.db.execute(
            select(
                FollowUp.followup_type,
                func.count(FollowUp.id),
            )
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.scheduled_at >= start,
                FollowUp.scheduled_at < end,
                FollowUp.status
                == FollowUpStatus.SCHEDULED.value,
                FollowUp.scheduled_at < now,
            )
            .group_by(FollowUp.followup_type)
        ).all()

        completed = dict(completed_rows)
        overdue = dict(overdue_rows)

        return [
            FollowUpTypeAnalytics(
                followup_type=followup_type,
                total=total,
                completed=completed.get(
                    followup_type,
                    0,
                ),
                overdue=overdue.get(
                    followup_type,
                    0,
                ),
                completion_rate=self._percentage(
                    completed.get(
                        followup_type,
                        0,
                    ),
                    total,
                ),
            )
            for followup_type, total in rows
        ]

    def _followup_statuses(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        total_followups: int,
    ) -> list[FollowUpStatusAnalytics]:
        """Build follow-up lifecycle distribution."""

        rows = self.db.execute(
            select(
                FollowUp.status,
                func.count(FollowUp.id),
            )
            .where(
                FollowUp.organization_id == organization_id,
                FollowUp.scheduled_at >= start,
                FollowUp.scheduled_at < end,
            )
            .group_by(FollowUp.status)
            .order_by(func.count(FollowUp.id).desc())
        ).all()

        return [
            FollowUpStatusAnalytics(
                status=status,
                count=count,
                percentage=self._percentage(
                    count,
                    total_followups,
                ),
            )
            for status, count in rows
        ]

    def _team_performance(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
        now: datetime,
    ) -> list[TeamAnalytics]:
        """Build sales-team performance metrics."""

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

        result: list[TeamAnalytics] = []

        for user in users:
            lead_conditions = (
                Lead.organization_id == organization_id,
                Lead.assigned_to_user_id == user.id,
                Lead.created_at >= start,
                Lead.created_at < end,
            )

            assigned_leads = self._count(
                Lead,
                *lead_conditions,
            )

            active_leads = self._count_joined_status(
                organization_id,
                user.id,
                start,
                end,
                terminal=False,
            )

            converted_leads = self._count_joined_status(
                organization_id,
                user.id,
                start,
                end,
                won=True,
            )

            followup_conditions = (
                FollowUp.organization_id == organization_id,
                FollowUp.assigned_to_user_id == user.id,
                FollowUp.scheduled_at >= start,
                FollowUp.scheduled_at < end,
            )

            scheduled_followups = self._count(
                FollowUp,
                *followup_conditions,
            )

            completed_followups = self._count(
                FollowUp,
                *followup_conditions,
                FollowUp.status
                == FollowUpStatus.COMPLETED.value,
            )

            overdue_followups = self._count(
                FollowUp,
                *followup_conditions,
                FollowUp.status
                == FollowUpStatus.SCHEDULED.value,
                FollowUp.scheduled_at < now,
            )

            average_lead_score = self.db.scalar(
                select(func.avg(Lead.lead_score)).where(
                    *lead_conditions,
                    Lead.lead_score.is_not(None),
                )
            )

            result.append(
                TeamAnalytics(
                    user_id=user.id,
                    full_name=user.full_name,
                    assigned_leads=assigned_leads,
                    active_leads=active_leads,
                    converted_leads=converted_leads,
                    conversion_rate=self._percentage(
                        converted_leads,
                        assigned_leads,
                    ),
                    scheduled_followups=scheduled_followups,
                    completed_followups=completed_followups,
                    overdue_followups=overdue_followups,
                    followup_completion_rate=self._percentage(
                        completed_followups,
                        scheduled_followups,
                    ),
                    average_lead_score=self._optional_float(
                        average_lead_score
                    ),
                )
            )

        return result

    def _ai_metrics(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
    ) -> AIAnalytics:
        """Build AI execution and human-review quality metrics."""

        total_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.created_at >= start,
            AIAnalysis.created_at < end,
        )

        completed_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.created_at >= start,
            AIAnalysis.created_at < end,
            AIAnalysis.status == "COMPLETED",
        )

        failed_analyses = self._count(
            AIAnalysis,
            AIAnalysis.organization_id == organization_id,
            AIAnalysis.created_at >= start,
            AIAnalysis.created_at < end,
            AIAnalysis.status == "FAILED",
        )

        feedback_conditions = (
            AIFeedback.organization_id == organization_id,
            AIFeedback.reviewed_at >= start,
            AIFeedback.reviewed_at < end,
        )

        total_reviews = self._count(
            AIFeedback,
            *feedback_conditions,
        )

        accepted_reviews = self._count(
            AIFeedback,
            *feedback_conditions,
            AIFeedback.decision
            == AIReviewDecision.ACCEPTED.value,
        )

        edited_reviews = self._count(
            AIFeedback,
            *feedback_conditions,
            AIFeedback.decision
            == AIReviewDecision.EDITED.value,
        )

        rejected_reviews = self._count(
            AIFeedback,
            *feedback_conditions,
            AIFeedback.decision
            == AIReviewDecision.REJECTED.value,
        )

        return AIAnalytics(
            total_analyses=total_analyses,
            completed_analyses=completed_analyses,
            failed_analyses=failed_analyses,
            total_reviews=total_reviews,
            accepted_reviews=accepted_reviews,
            edited_reviews=edited_reviews,
            rejected_reviews=rejected_reviews,
            acceptance_rate=self._percentage(
                accepted_reviews,
                total_reviews,
            ),
            edit_rate=self._percentage(
                edited_reviews,
                total_reviews,
            ),
            rejection_rate=self._percentage(
                rejected_reviews,
                total_reviews,
            ),
        )

    def _count_converted(
        self,
        organization_id: UUID,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count leads created in-range that are currently won."""

        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Lead)
                .join(
                    LeadStatus,
                    Lead.status_id == LeadStatus.id,
                )
                .where(
                    Lead.organization_id == organization_id,
                    Lead.created_at >= start,
                    Lead.created_at < end,
                    LeadStatus.is_won.is_(True),
                )
            )
            or 0
        )

    def _count_joined_status(
        self,
        organization_id: UUID,
        user_id: UUID,
        start: datetime,
        end: datetime,
        *,
        terminal: bool | None = None,
        won: bool | None = None,
    ) -> int:
        """Count assigned leads using lifecycle-status properties."""

        statement = (
            select(func.count())
            .select_from(Lead)
            .join(
                LeadStatus,
                Lead.status_id == LeadStatus.id,
            )
            .where(
                Lead.organization_id == organization_id,
                Lead.assigned_to_user_id == user_id,
                Lead.created_at >= start,
                Lead.created_at < end,
            )
        )

        if terminal is not None:
            statement = statement.where(
                LeadStatus.is_terminal.is_(terminal)
            )

        if won is not None:
            statement = statement.where(
                LeadStatus.is_won.is_(won)
            )

        return int(
            self.db.scalar(statement)
            or 0
        )

    def _count(
        self,
        model,
        *conditions,
    ) -> int:
        """Return a filtered row count."""

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
        """Convert nullable SQL numerics to rounded floats."""

        if value is None:
            return None

        return round(float(value), 2)

    @classmethod
    def _date_range_bounds(
        cls,
        start_date: date,
        end_date: date,
        timezone_name: str,
    ) -> tuple[datetime, datetime]:
        """Return inclusive local-date range as [start, exclusive end)."""

        timezone = cls._timezone(
            timezone_name
        )

        start = datetime.combine(
            start_date,
            time.min,
            tzinfo=timezone,
        )

        end = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            tzinfo=timezone,
        )

        return start, end

    @staticmethod
    def _timezone(
        timezone_name: str,
    ) -> ZoneInfo:
        """Resolve an organization timezone with application fallback."""

        try:
            return ZoneInfo(timezone_name)
        except Exception:
            return ZoneInfo(DEFAULT_TIMEZONE)
