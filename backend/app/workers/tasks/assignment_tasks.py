"""Celery tasks for automatic lead assignment escalation."""

from __future__ import annotations

from datetime import UTC, datetime

from app.db.session import get_session_factory
from app.repositories.leads import LeadRepository
from app.repositories.organizations import OrganizationRepository
from app.services.assignment_service import AssignmentService
from app.workers.celery_app import celery_app


@celery_app.task(
    name="omnilead.assignments.escalate_due",
)
def escalate_due_leads(
    minimum_priority_score: int = 80,
    minimum_followup_risk_score: int = 70,
    unassigned_grace_hours: int = 2,
    overdue_grace_hours: int = 4,
    organization_limit: int = 100,
    lead_limit: int = 200,
) -> dict[str, object]:
    """Escalate risky high-priority leads that require admin attention."""

    session_factory = get_session_factory()
    db = session_factory()

    try:
        now = datetime.now(UTC)

        organizations = OrganizationRepository(
            db
        ).list_active(
            limit=organization_limit,
        )

        leads = LeadRepository(db)
        assignments = AssignmentService(db)

        checked = 0
        escalated = 0
        organization_count = 0
        escalated_lead_ids: list[str] = []

        for organization in organizations:
            organization_count += 1

            candidates = leads.list_priority_queue(
                organization.id,
                minimum_priority_score=(
                    minimum_priority_score
                ),
                limit=lead_limit,
            )

            for lead in candidates:
                checked += 1

                owner_before = (
                    lead.assigned_to_user_id
                )

                updated = (
                    assignments.escalate_if_needed(
                        organization.id,
                        lead.id,
                        now=now,
                        minimum_priority_score=(
                            minimum_priority_score
                        ),
                        minimum_followup_risk_score=(
                            minimum_followup_risk_score
                        ),
                        unassigned_grace_hours=(
                            unassigned_grace_hours
                        ),
                        overdue_grace_hours=(
                            overdue_grace_hours
                        ),
                    )
                )

                owner_after = (
                    updated.assigned_to_user_id
                )

                if (
                    owner_after is not None
                    and owner_after != owner_before
                ):
                    escalated += 1
                    escalated_lead_ids.append(
                        str(lead.id)
                    )

        return {
            "organizations_checked": organization_count,
            "leads_checked": checked,
            "leads_escalated": escalated,
            "escalated_lead_ids": escalated_lead_ids,
            "processed_at": now.isoformat(),
        }

    finally:
        db.close()
