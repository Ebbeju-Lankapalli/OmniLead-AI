import pytest

from app.ai.scoring.priority_score import calculate_priority_score
from app.db.types import PurchaseIntent


@pytest.mark.unit
def test_high_intent_high_risk_urgent_lead_gets_high_priority():
    result = calculate_priority_score(
        lead_score=95,
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        followup_risk_score=90,
        urgency="HIGH",
    )

    assert result.score >= 90


@pytest.mark.unit
def test_priority_score_is_bounded():
    result = calculate_priority_score(
        lead_score=100,
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        followup_risk_score=100,
        urgency="URGENT",
    )

    assert result.score == 100


@pytest.mark.unit
def test_high_intent_priority_exceeds_general_enquiry():
    high = calculate_priority_score(
        lead_score=80,
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        followup_risk_score=50,
        urgency="MEDIUM",
    )

    general = calculate_priority_score(
        lead_score=80,
        purchase_intent=PurchaseIntent.GENERAL_ENQUIRY,
        followup_risk_score=50,
        urgency="MEDIUM",
    )

    assert high.score > general.score
