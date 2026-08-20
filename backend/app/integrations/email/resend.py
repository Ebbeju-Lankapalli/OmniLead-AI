"""Resend email delivery integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import resend

from app.core.config import settings
from app.core.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class EmailDeliveryResult:
    """Normalized result returned after sending an email."""

    provider: str
    message_id: str | None
    raw_response: dict[str, Any]


class ResendEmailClient:
    """Small Resend wrapper used by OmniLead AI background workers."""

    provider_name = "resend"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        from_address: str | None = None,
        from_name: str | None = None,
    ) -> None:
        self.api_key = (
            api_key
            if api_key is not None
            else settings.RESEND_API_KEY
        ).strip()

        self.from_address = (
            from_address
            if from_address is not None
            else settings.EMAIL_FROM_ADDRESS
        ).strip()

        self.from_name = (
            from_name
            if from_name is not None
            else settings.EMAIL_FROM_NAME
        ).strip()

        if not self.api_key:
            raise ConfigurationError(
                "RESEND_API_KEY is not configured."
            )

        if not self.from_address:
            raise ConfigurationError(
                "EMAIL_FROM_ADDRESS is not configured."
            )

    @property
    def sender(self) -> str:
        """Return the formatted From header."""

        if self.from_name:
            return (
                f"{self.from_name} "
                f"<{self.from_address}>"
            )

        return self.from_address

    def send(
        self,
        *,
        to: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> EmailDeliveryResult:
        """Send one email through Resend."""

        recipient = to.strip()
        cleaned_subject = subject.strip()
        cleaned_text = text.strip()

        if not recipient:
            raise ValueError(
                "Email recipient cannot be empty."
            )

        if not cleaned_subject:
            raise ValueError(
                "Email subject cannot be empty."
            )

        if not cleaned_text:
            raise ValueError(
                "Email text cannot be empty."
            )

        resend.api_key = self.api_key

        payload: resend.Emails.SendParams = {
            "from": self.sender,
            "to": [recipient],
            "subject": cleaned_subject,
            "text": cleaned_text,
        }

        if html is not None:
            cleaned_html = html.strip()

            if cleaned_html:
                payload["html"] = cleaned_html

        response = resend.Emails.send(
            payload
        )

        if isinstance(response, dict):
            raw_response = dict(response)
        else:
            raw_response = {
                "id": getattr(
                    response,
                    "id",
                    None,
                ),
            }

        message_id = raw_response.get(
            "id"
        )

        return EmailDeliveryResult(
            provider=self.provider_name,
            message_id=(
                str(message_id)
                if message_id is not None
                else None
            ),
            raw_response=raw_response,
        )
