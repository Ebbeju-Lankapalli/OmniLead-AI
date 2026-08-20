import hashlib
import hmac

import pytest

from app.core.exceptions import AuthenticationError
from app.integrations.meta.signatures import validate_meta_signature
from app.integrations.meta.webhooks import verify_webhook_subscription


@pytest.mark.webhook
def test_valid_meta_signature():
    payload = b'{"object":"whatsapp_business_account"}'
    secret = "test-secret"

    digest = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    validate_meta_signature(
        payload,
        f"sha256={digest}",
        app_secret=secret,
    )


@pytest.mark.webhook
def test_invalid_meta_signature_rejected():
    payload = b'{"object":"whatsapp_business_account"}'

    with pytest.raises(AuthenticationError):
        validate_meta_signature(
            payload,
            "sha256=invalid",
            app_secret="test-secret",
        )


@pytest.mark.webhook
def test_valid_webhook_subscription():
    result = verify_webhook_subscription(
        mode="subscribe",
        verify_token="expected-token",
        challenge="12345",
        configured_token="expected-token",
    )

    assert result == "12345"


@pytest.mark.webhook
def test_invalid_webhook_verify_token_rejected():
    with pytest.raises(AuthenticationError):
        verify_webhook_subscription(
            mode="subscribe",
            verify_token="wrong-token",
            challenge="12345",
            configured_token="expected-token",
        )
