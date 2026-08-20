"""Explainable lead-priority scoring."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.types import PurchaseIntent

INTENT_PRIORITY_BONUS = {
    PurchaseIntent.HIGH_INTENT: 20,
    PurchaseIntent.POTENTIAL_LEAD: 12,
    PurchaseIntent.GENERAL_ENQUIRY: 5,
    PurchaseIntent.UNCERTAIN: 3,
    PurchaseIntent.NOT_INTERESTED: 0,
}


@dataclass(frozen=True, slots=True)
class PriorityScoreResult:
    """Explainable 0-100 lead priority score."""

    score: int
    breakdown: dict[str, int]


def calculate_priority_score(
    *,
    lead_score: int,
    purchase_intent: PurchaseIntent | str | None,
    followup_risk_score: int,
    urgency: str | None = None,
) -> PriorityScoreResult:
    """Calculate sales priority from quality, urgency, and follow-up risk."""

    bounded_lead_score = min(
        max(lead_score, 0),
        100,
    )

    bounded_risk = min(
        max(followup_risk_score, 0),
        100,
    )

    if purchase_intent is None:
        normalized_intent = PurchaseIntent.UNCERTAIN
    elif isinstance(purchase_intent, PurchaseIntent):
        normalized_intent = purchase_intent
    else:
        normalized_intent = PurchaseIntent(
            purchase_intent.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

    normalized_urgency = (
        urgency.strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
        if urgency
        else ""
    )

    urgency_points = {
        "URGENT": 15,
        "HIGH": 15,
        "MEDIUM": 8,
        "NORMAL": 5,
        "LOW": 2,
    }.get(
        normalized_urgency,
        0,
    )

    breakdown = {
        "lead_quality": round(
            bounded_lead_score * 0.55
        ),
        "purchase_intent": INTENT_PRIORITY_BONUS[
            normalized_intent
        ],
        "followup_risk": round(
            bounded_risk * 0.15
        ),
        "urgency": urgency_points,
    }

    score = min(
        sum(breakdown.values()),
        100,
    )

    return PriorityScoreResult(
        score=score,
        breakdown=breakdown,
    )
