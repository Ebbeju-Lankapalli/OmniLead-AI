"""Safe AI fallback helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AIFallbackResult:
    """Fallback result used when AI execution is unavailable."""

    status: str
    result: dict[str, Any]
    requires_review: bool
    reason: str


def unavailable_fallback(
    *,
    analysis_type: str,
    reason: str,
) -> AIFallbackResult:
    """Return a safe human-review fallback."""

    normalized_type = (
        analysis_type.strip()
        .upper()
        .replace("-", "_")
        .replace(" ", "_")
    )

    cleaned_reason = reason.strip()

    if not cleaned_reason:
        cleaned_reason = "AI service unavailable."

    return AIFallbackResult(
        status="FALLBACK",
        result={
            "analysis_type": normalized_type,
            "fallback": True,
        },
        requires_review=True,
        reason=cleaned_reason,
    )
