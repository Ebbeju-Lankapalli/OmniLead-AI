"""Explainable lead follow-up risk scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FollowUpRiskResult:
    """Explainable 0-100 follow-up risk score."""

    score: int
    breakdown: dict[str, int]


def calculate_followup_risk(
    *,
    now: datetime,
    last_contact_at: datetime | None,
    next_followup_at: datetime | None,
    high_intent: bool,
    assigned: bool,
) -> FollowUpRiskResult:
    """Estimate risk that a lead requires timely sales attention."""

    breakdown: dict[str, int] = {
        "stale_contact": 0,
        "overdue_followup": 0,
        "missing_followup": 0,
        "high_intent": 0,
        "unassigned": 0,
    }

    if last_contact_at is None:
        breakdown["stale_contact"] = 20
    else:
        hours_since_contact = max(
            (now - last_contact_at).total_seconds()
            / 3600,
            0,
        )

        if hours_since_contact >= 72:
            breakdown["stale_contact"] = 25
        elif hours_since_contact >= 24:
            breakdown["stale_contact"] = 15
        elif hours_since_contact >= 8:
            breakdown["stale_contact"] = 8

    if next_followup_at is None:
        breakdown["missing_followup"] = 20
    elif next_followup_at < now:
        overdue_hours = (
            now - next_followup_at
        ).total_seconds() / 3600

        if overdue_hours >= 24:
            breakdown["overdue_followup"] = 35
        elif overdue_hours >= 4:
            breakdown["overdue_followup"] = 25
        else:
            breakdown["overdue_followup"] = 15

    if high_intent:
        breakdown["high_intent"] = 15

    if not assigned:
        breakdown["unassigned"] = 10

    score = min(
        sum(breakdown.values()),
        100,
    )

    return FollowUpRiskResult(
        score=score,
        breakdown=breakdown,
    )
