import pytest

from app.ai.guards.confidence import (
    DEFAULT_REJECT_THRESHOLD,
    DEFAULT_REVIEW_THRESHOLD,
    evaluate_confidence,
)


@pytest.mark.unit
def test_high_confidence_does_not_require_review():
    result = evaluate_confidence(0.95)

    assert result.confidence == 0.95
    assert result.requires_review is False
    assert result.should_reject is False
    assert result.reason is None


@pytest.mark.unit
def test_medium_confidence_requires_review():
    result = evaluate_confidence(0.55)

    assert result.requires_review is True
    assert result.should_reject is False
    assert result.reason is not None


@pytest.mark.unit
def test_low_confidence_requires_review_and_rejection():
    result = evaluate_confidence(0.20)

    assert result.requires_review is True
    assert result.should_reject is True


@pytest.mark.unit
def test_missing_confidence_requires_review():
    result = evaluate_confidence(None)

    assert result.requires_review is True
    assert result.should_reject is False


@pytest.mark.unit
def test_default_threshold_order():
    assert (
        0.0
        <= DEFAULT_REJECT_THRESHOLD
        <= DEFAULT_REVIEW_THRESHOLD
        <= 1.0
    )


@pytest.mark.unit
def test_invalid_confidence_raises():
    with pytest.raises(ValueError):
        evaluate_confidence(1.5)
