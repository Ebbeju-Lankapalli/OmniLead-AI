"""Domain and infrastructure exceptions for OmniLead AI."""

from __future__ import annotations

from typing import Any


class OmniLeadError(Exception):
    """Base class for expected OmniLead AI application errors."""

    status_code = 500
    error_code = "OMNILEAD_ERROR"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(OmniLeadError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class AuthenticationError(OmniLeadError):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(OmniLeadError):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(OmniLeadError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(OmniLeadError):
    status_code = 409
    error_code = "CONFLICT"


class RateLimitError(OmniLeadError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class ExternalServiceError(OmniLeadError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


class AIServiceError(ExternalServiceError):
    error_code = "AI_SERVICE_ERROR"


class IntegrationError(ExternalServiceError):
    error_code = "INTEGRATION_ERROR"


class StorageError(ExternalServiceError):
    error_code = "STORAGE_ERROR"


class TranscriptionError(ExternalServiceError):
    error_code = "TRANSCRIPTION_ERROR"


class ConfigurationError(OmniLeadError):
    status_code = 500
    error_code = "CONFIGURATION_ERROR"