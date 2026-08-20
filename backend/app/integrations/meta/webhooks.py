"""Meta webhook verification helpers."""

from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.core.security import constant_time_compare

META_SUBSCRIBE_MODE = "subscribe"


def verify_webhook_subscription(
    *,
    mode: str | None,
    verify_token: str | None,
    challenge: str | None,
    configured_token: str | None = None,
) -> str:
    """
    Validate Meta's webhook subscription challenge.

    Returns the challenge string when verification succeeds.
    """

    expected_token = (
        configured_token
        if configured_token is not None
        else settings.META_VERIFY_TOKEN
    ).strip()

    if not expected_token:
        raise ConfigurationError(
            "META_VERIFY_TOKEN is not configured."
        )

    if mode != META_SUBSCRIBE_MODE:
        raise AuthenticationError(
            "Invalid Meta webhook verification mode."
        )

    if not verify_token:
        raise AuthenticationError(
            "Meta webhook verify token was not provided."
        )

    if not constant_time_compare(
        verify_token,
        expected_token,
    ):
        raise AuthenticationError(
            "Invalid Meta webhook verify token."
        )

    if challenge is None:
        raise AuthenticationError(
            "Meta webhook challenge was not provided."
        )

    return challenge
