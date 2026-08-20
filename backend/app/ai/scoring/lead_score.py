"""Explainable deterministic lead scoring."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.types import PurchaseIntent

INTENT_POINTS = {
    PurchaseIntent.HIGH_INTENT: 40,
    PurchaseIntent.POTENTIAL_LEAD: 28,
    PurchaseIntent.GENERAL_ENQUIRY: 15,
    PurchaseIntent.UNCERTAIN: 10,
    PurchaseIntent.NOT_INTERESTED: 0,
}


@dataclass(frozen=True, slots=True)
class LeadScoreResult:
    """Explainable 0-100 lead score."""

    score: int
    breakdown: dict[str, int]


def calculate_lead_score(
    *,
    purchase_intent: PurchaseIntent | str | None,
    qualification_score: int | None,
    confidence: float | None,
    has_requirement: bool,
    has_budget_signal: bool,
    has_timeline_signal: bool,
) -> LeadScoreResult:
    """Calculate deterministic lead quality from AI evidence."""

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

    bounded_qualification = min(
        max(qualification_score or 0, 0),
        100,
    )

    bounded_confidence = min(
        max(confidence or 0.0, 0.0),
        1.0,
    )

    breakdown = {
        "purchase_intent": INTENT_POINTS[
            normalized_intent
        ],
        "qualification": round(
            bounded_qualification * 0.35
        ),
        "confidence": round(
            bounded_confidence * 10
        ),
        "requirement": 7 if has_requirement else 0,
        "budget_signal": 4 if has_budget_signal else 0,
        "timeline_signal": 4 if has_timeline_signal else 0,
    }

    score = min(
        sum(breakdown.values()),
        100,
    )

    return LeadScoreResult(
        score=score,
        breakdown=breakdown,
    )
