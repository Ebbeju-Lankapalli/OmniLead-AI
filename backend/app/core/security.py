"""Security-related helpers for authentication and webhook validation."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def constant_time_compare(
    value_a: str | bytes,
    value_b: str | bytes,
) -> bool:
    """Compare sensitive values using a timing-attack-resistant comparison."""

    if isinstance(value_a, str):
        value_a = value_a.encode("utf-8")

    if isinstance(value_b, str):
        value_b = value_b.encode("utf-8")

    return hmac.compare_digest(value_a, value_b)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""

    if length < 16:
        raise ValueError("Secure tokens must use at least 16 bytes of entropy.")

    return secrets.token_urlsafe(length)


def sha256_hex(value: str | bytes) -> str:
    """Return a SHA-256 hexadecimal digest."""

    if isinstance(value, str):
        value = value.encode("utf-8")

    return hashlib.sha256(value).hexdigest()


def verify_hmac_sha256_signature(
    *,
    payload: bytes,
    signature: str,
    secret: str,
    prefix: str = "sha256=",
) -> bool:
    """
    Validate an HMAC SHA-256 signature.

    This helper is intentionally provider-agnostic. Meta-specific webhook
    parsing and signature semantics remain in integrations/meta/signatures.py.
    """

    if not signature or not secret:
        return False

    received_signature = (
        signature[len(prefix):]
        if prefix and signature.startswith(prefix)
        else signature
    )

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return constant_time_compare(
        received_signature,
        expected_signature,
    )