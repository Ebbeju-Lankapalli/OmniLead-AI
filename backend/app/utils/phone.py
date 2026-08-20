"""Phone-number normalization helpers."""

from __future__ import annotations

import re

_NON_DIGIT_PATTERN = re.compile(r"\D+")


def normalize_phone(
    value: str,
    *,
    default_country_code: str = "91",
) -> str:
    """
    Normalize a phone number to a stable E.164-like representation.

    Examples:
    - "+91 98765 43210" -> "+919876543210"
    - "9876543210"      -> "+919876543210"
    - "919876543210"    -> "+919876543210"

    This is intentionally lightweight for V1. A dedicated phone-number
    library can replace it later if international validation requirements
    become more complex.
    """

    cleaned = value.strip()

    if not cleaned:
        raise ValueError("Phone number cannot be empty.")

    digits = _NON_DIGIT_PATTERN.sub("", cleaned)

    if not digits:
        raise ValueError("Phone number must contain digits.")

    normalized_country_code = _NON_DIGIT_PATTERN.sub(
        "",
        default_country_code,
    )

    if not normalized_country_code:
        raise ValueError(
            "Default country code must contain digits."
        )

    if len(digits) == 10:
        digits = f"{normalized_country_code}{digits}"
    elif digits.startswith("0") and len(digits) == 11:
        digits = f"{normalized_country_code}{digits[1:]}"

    if len(digits) < 8 or len(digits) > 15:
        raise ValueError(
            "Phone number must contain between 8 and 15 digits "
            "after normalization."
        )

    return f"+{digits}"


def normalize_phone_or_none(
    value: str | None,
    *,
    default_country_code: str = "91",
) -> str | None:
    """Normalize a phone number when a value is present."""

    if value is None:
        return None

    cleaned = value.strip()

    if not cleaned:
        return None

    return normalize_phone(
        cleaned,
        default_country_code=default_country_code,
    )
