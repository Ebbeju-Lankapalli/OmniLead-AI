"""Dashboard aggregation schemas for OmniLead AI."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.db.types import (
    ConversationChannel,
    FollowUpStatus,
    FollowUpType,
    InteractionDirection,
    InteractionType,
    LeadSource,
    PurchaseIntent,
)
from app.schemas.common import ORMModel


class DashboardMetrics(ORMModel):
    """Top-level dashboard KPI counters."""

    total_leads: int = Field(ge=0)
    active_leads: int = Field(ge=0)
    high_priority_leads: int = Field(ge=0)

    new_enquiries: int = Field(ge=0)
    enquiries_needing_review: int = Field(ge=0)

    followups_due_today: int = Field(ge=0)
    overdue_followups: int = Field(ge=0)

    converted_leads: int = Field(ge=0)

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


class DashboardSourceMetric(ORMModel):
    """Lead/enquiry count grouped by acquisition source."""

    source: LeadSource
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class DashboardStatusMetric(ORMModel):
    """Lead count grouped by lifecycle status."""

    status_id: UUID
    status_key: str
    status_name: str
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class DashboardIntentMetric(ORMModel):
    """Lead count grouped by purchase intent."""

    purchase_intent: PurchaseIntent
    count: int = Field(ge=0)
    percentage: float = Field(ge=0.0, le=100.0)


class DashboardPriorityLead(ORMModel):
    """High-priority lead displayed in the dashboard queue."""

    lead_id: UUID
    customer_id: UUID

    customer_name: str | None = None
    company_name: str | None = None

    product_id: UUID | None = None
    product_name: str | None = None

    assigned_to_user_id: UUID | None = None
    assigned_to_name: str | None = None

    status_id: UUID
    status_name: str

    source: LeadSource
    purchase_intent: PurchaseIntent | None = None

    lead_score: int | None = Field(default=None, ge=0, le=100)
    priority_score: int | None = Field(default=None, ge=0, le=100)
    followup_risk_score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    next_best_action: str | None = None
    next_followup_at: datetime | None = None
    last_contact_at: datetime | None = None


class DashboardFollowUp(ORMModel):
    """Upcoming or overdue follow-up displayed on the dashboard."""

    followup_id: UUID
    lead_id: UUID
    customer_id: UUID
    assigned_to_user_id: UUID

    customer_name: str | None = None
    assigned_to_name: str | None = None

    followup_type: FollowUpType
    status: FollowUpStatus
    scheduled_at: datetime

    reminder_minutes_before: int = Field(ge=0)
    notes: str | None = None


class DashboardRecentActivity(ORMModel):
    """Recent customer or internal CRM activity."""

    interaction_id: UUID
    customer_id: UUID

    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    actor_user_id: UUID | None = None

    customer_name: str | None = None
    actor_name: str | None = None

    interaction_type: InteractionType
    direction: InteractionDirection | None = None
    channel: ConversationChannel

    content: str | None = None
    occurred_at: datetime


class DashboardAIReviewMetrics(ORMModel):
    """AI-analysis and human-review workload counters."""

    total_analyses: int = Field(ge=0)
    completed_analyses: int = Field(ge=0)
    failed_analyses: int = Field(ge=0)
    pending_reviews: int = Field(ge=0)
    accepted_reviews: int = Field(ge=0)
    edited_reviews: int = Field(ge=0)
    rejected_reviews: int = Field(ge=0)


class DashboardTeamMetric(ORMModel):
    """Compact team workload/performance metric."""

    user_id: UUID
    full_name: str
    active_leads: int = Field(ge=0)
    due_followups: int = Field(ge=0)
    completed_followups: int = Field(ge=0)
    converted_leads: int = Field(ge=0)


class DashboardResponse(ORMModel):
    """Complete dashboard payload returned by the API."""

    generated_at: datetime

    metrics: DashboardMetrics

    source_breakdown: list[DashboardSourceMetric] = Field(
        default_factory=list
    )
    status_breakdown: list[DashboardStatusMetric] = Field(
        default_factory=list
    )
    purchase_intent_breakdown: list[DashboardIntentMetric] = Field(
        default_factory=list
    )

    priority_leads: list[DashboardPriorityLead] = Field(
        default_factory=list
    )
    upcoming_followups: list[DashboardFollowUp] = Field(
        default_factory=list
    )
    recent_activity: list[DashboardRecentActivity] = Field(
        default_factory=list
    )

    ai_review_metrics: DashboardAIReviewMetrics
    team_metrics: list[DashboardTeamMetric] = Field(
        default_factory=list
    )
