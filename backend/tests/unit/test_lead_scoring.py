import pytest

from app.ai.scoring.lead_score import calculate_lead_score
from app.db.types import PurchaseIntent


@pytest.mark.unit
def test_high_intent_lead_scores_high():
    result = calculate_lead_score(
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        qualification_score=95,
        confidence=0.95,
        has_requirement=True,
        has_budget_signal=True,
        has_timeline_signal=True,
    )

    assert result.score >= 90
    assert result.breakdown["purchase_intent"] == 40


@pytest.mark.unit
def test_not_interested_scores_lower_than_high_intent():
    high = calculate_lead_score(
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        qualification_score=80,
        confidence=0.9,
        has_requirement=True,
        has_budget_signal=True,
        has_timeline_signal=True,
    )

    low = calculate_lead_score(
        purchase_intent=PurchaseIntent.NOT_INTERESTED,
        qualification_score=80,
        confidence=0.9,
        has_requirement=True,
        has_budget_signal=True,
        has_timeline_signal=True,
    )

    assert high.score > low.score


@pytest.mark.unit
def test_lead_score_is_bounded():
    result = calculate_lead_score(
        purchase_intent=PurchaseIntent.HIGH_INTENT,
        qualification_score=100,
        confidence=1.0,
        has_requirement=True,
        has_budget_signal=True,
        has_timeline_signal=True,
    )

    assert 0 <= result.score <= 100
