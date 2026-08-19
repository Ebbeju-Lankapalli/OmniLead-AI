"""Analytics aggregation schemas for OmniLead AI."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.db.types import (
    FollowUpStatus,
    FollowUpType,
    LeadSource,
    PurchaseIntent,
)
from app.schemas.common import ORMModel


class AnalyticsDateRange(ORMModel):
    """Date range represented by an analytics response."""

    start_date: date
    end_date: date


class AnalyticsOverview(ORMModel):
    """High-level analytics KPI summary."""

    total_enquiries: int = Field(ge=0)
    total_leads: int = Field(ge=0)
    total_converted_leads: int = Field(ge=0)

    conversion_rate: float = Field(ge=0.0, le=100.0)

    average_lead_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    average_priority_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    average_followup_risk_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    total_followups: int = Field(ge=0)
    completed_followups: int = Field(ge=0)
    overdue_followups: int = Field(ge=0)

    followup_completion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )


class AnalyticsTrendPoint(ORMModel):
    """Single time-series data point."""

    period_start: datetime
    enquiries: int = Field(ge=0)
    leads: int = Field(ge=0)
    converted_leads: int = Field(ge=0)
    completed_followups: int = Field(ge=0)


class SourceAnalytics(ORMModel):
    """Performance metrics for an acquisition source."""

    source: LeadSource

    enquiries: int = Field(ge=0)
    leads: int = Field(ge=0)
    converted_leads: int = Field(ge=0)

    lead_conversion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    average_lead_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    average_priority_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )


class PurchaseIntentAnalytics(ORMModel):
    """Lead metrics grouped by purchase intent."""

    purchase_intent: PurchaseIntent
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)

    average_lead_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )


class LeadStatusAnalytics(ORMModel):
    """Lead metrics grouped by lifecycle status."""

    status_id: UUID
    status_key: str
    status_name: str

    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class ProductAnalytics(ORMModel):
    """Lead and conversion performance for a product."""

    product_id: UUID
    product_name: str

    lead_count: int = Field(ge=0)
    converted_leads: int = Field(ge=0)

    conversion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    average_lead_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )


class FollowUpTypeAnalytics(ORMModel):
    """Follow-up performance grouped by communication type."""

    followup_type: FollowUpType

    total: int = Field(ge=0)
    completed: int = Field(ge=0)
    overdue: int = Field(ge=0)

    completion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )


class FollowUpStatusAnalytics(ORMModel):
    """Follow-up count grouped by lifecycle state."""

    status: FollowUpStatus
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class TeamAnalytics(ORMModel):
    """Sales-team performance metrics."""

    user_id: UUID
    full_name: str

    assigned_leads: int = Field(ge=0)
    active_leads: int = Field(ge=0)
    converted_leads: int = Field(ge=0)

    conversion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    scheduled_followups: int = Field(ge=0)
    completed_followups: int = Field(ge=0)
    overdue_followups: int = Field(ge=0)

    followup_completion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    average_lead_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )


class AIAnalytics(ORMModel):
    """AI analysis and human-review quality metrics."""

    total_analyses: int = Field(ge=0)
    completed_analyses: int = Field(ge=0)
    failed_analyses: int = Field(ge=0)

    total_reviews: int = Field(ge=0)
    accepted_reviews: int = Field(ge=0)
    edited_reviews: int = Field(ge=0)
    rejected_reviews: int = Field(ge=0)

    acceptance_rate: float = Field(
        ge=0.0,
        le=100.0,
    )
    edit_rate: float = Field(
        ge=0.0,
        le=100.0,
    )
    rejection_rate: float = Field(
        ge=0.0,
        le=100.0,
    )


class ConversionAnalytics(ORMModel):
    """Overall lead conversion metrics."""

    total_leads: int = Field(ge=0)
    converted_leads: int = Field(ge=0)
    conversion_rate: float = Field(
        ge=0.0,
        le=100.0,
    )

    average_days_to_conversion: float | None = Field(
        default=None,
        ge=0.0,
    )


class AnalyticsResponse(ORMModel):
    """Complete analytics payload returned by the API."""

    generated_at: datetime
    date_range: AnalyticsDateRange

    overview: AnalyticsOverview
    conversion: ConversionAnalytics

    trend: list[AnalyticsTrendPoint] = Field(
        default_factory=list
    )

    source_performance: list[SourceAnalytics] = Field(
        default_factory=list
    )
    purchase_intent_breakdown: list[PurchaseIntentAnalytics] = Field(
        default_factory=list
    )
    lead_status_breakdown: list[LeadStatusAnalytics] = Field(
        default_factory=list
    )

    product_performance: list[ProductAnalytics] = Field(
        default_factory=list
    )

    followup_type_performance: list[FollowUpTypeAnalytics] = Field(
        default_factory=list
    )
    followup_status_breakdown: list[FollowUpStatusAnalytics] = Field(
        default_factory=list
    )

    team_performance: list[TeamAnalytics] = Field(
        default_factory=list
    )

    ai_metrics: AIAnalytics
