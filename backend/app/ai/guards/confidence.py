"""Confidence-based human-review decisions."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_REVIEW_THRESHOLD = 0.70
DEFAULT_REJECT_THRESHOLD = 0.40


@dataclass(frozen=True, slots=True)
class ConfidenceDecision:
    """Normalized confidence evaluation."""

    confidence: float | None
    requires_review: bool
    should_reject: bool
    reason: str | None = None


def evaluate_confidence(
    confidence: float | None,
    *,
    review_threshold: float = DEFAULT_REVIEW_THRESHOLD,
    reject_threshold: float = DEFAULT_REJECT_THRESHOLD,
) -> ConfidenceDecision:
    """Determine whether an AI result should require human review."""

    if not 0.0 <= reject_threshold <= review_threshold <= 1.0:
        raise ValueError(
            "Confidence thresholds must satisfy "
            "0 <= reject <= review <= 1."
        )

    if confidence is None:
        return ConfidenceDecision(
            confidence=None,
            requires_review=True,
            should_reject=False,
            reason="AI result did not provide confidence.",
        )

    bounded = float(confidence)

    if not 0.0 <= bounded <= 1.0:
        raise ValueError(
            "Confidence must be between 0 and 1."
        )

    if bounded < reject_threshold:
        return ConfidenceDecision(
            confidence=bounded,
            requires_review=True,
            should_reject=True,
            reason="AI confidence is below the rejection threshold.",
        )

    if bounded < review_threshold:
        return ConfidenceDecision(
            confidence=bounded,
            requires_review=True,
            should_reject=False,
            reason="AI confidence is below the review threshold.",
        )

    return ConfidenceDecision(
        confidence=bounded,
        requires_review=False,
        should_reject=False,
        reason=None,
    )
