"""Meta webhook signature validation."""

from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.core.security import verify_hmac_sha256_signature

META_SIGNATURE_HEADER = "X-Hub-Signature-256"


def validate_meta_signature(
    payload: bytes,
    signature: str | None,
    *,
    app_secret: str | None = None,
) -> None:
    """
    Validate a Meta X-Hub-Signature-256 webhook signature.

    Validation may be disabled explicitly for local development through
    WEBHOOK_SIGNATURE_VALIDATION, but production webhook traffic should
    always keep it enabled.
    """

    if not settings.WEBHOOK_SIGNATURE_VALIDATION:
        return

    secret = (
        app_secret
        if app_secret is not None
        else settings.META_APP_SECRET
    ).strip()

    if not secret:
        raise ConfigurationError(
            "META_APP_SECRET is not configured."
        )

    if not signature:
        raise AuthenticationError(
            "Meta webhook signature was not provided."
        )

    valid = verify_hmac_sha256_signature(
        payload=payload,
        signature=signature,
        secret=secret,
        prefix="sha256=",
    )

    if not valid:
        raise AuthenticationError(
            "Invalid Meta webhook signature."
        )
