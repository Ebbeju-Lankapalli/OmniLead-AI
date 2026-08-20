from datetime import UTC, datetime, timedelta

import pytest

from app.ai.scoring.followup_risk import calculate_followup_risk


@pytest.mark.unit
def test_unassigned_high_intent_missing_followup_has_risk():
    now = datetime.now(UTC)

    result = calculate_followup_risk(
        now=now,
        last_contact_at=None,
        next_followup_at=None,
        high_intent=True,
        assigned=False,
    )

    assert result.score >= 60
    assert result.breakdown["missing_followup"] == 20
    assert result.breakdown["high_intent"] == 15
    assert result.breakdown["unassigned"] == 10


@pytest.mark.unit
def test_overdue_followup_increases_risk():
    now = datetime.now(UTC)

    result = calculate_followup_risk(
        now=now,
        last_contact_at=now - timedelta(hours=2),
        next_followup_at=now - timedelta(hours=30),
        high_intent=False,
        assigned=True,
    )

    assert result.breakdown["overdue_followup"] == 35


@pytest.mark.unit
def test_followup_risk_is_bounded():
    now = datetime.now(UTC)

    result = calculate_followup_risk(
        now=now,
        last_contact_at=now - timedelta(days=10),
        next_followup_at=now - timedelta(days=10),
        high_intent=True,
        assigned=False,
    )

    assert 0 <= result.score <= 100
