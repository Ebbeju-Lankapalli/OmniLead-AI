"""Gemini structured-output provider implementation."""

from __future__ import annotations

import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.ai.providers.base import (
    AIProvider,
    AIProviderResponse,
    AIProviderUsage,
)
from app.core.config import settings
from app.core.exceptions import AIServiceError, ConfigurationError


class GeminiProvider(AIProvider):
    """Google Gemini provider using Pydantic structured outputs."""

    provider_name = "google"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_api_key = (
            api_key
            if api_key is not None
            else settings.GEMINI_API_KEY
        ).strip()

        resolved_model = (
            model
            if model is not None
            else settings.GEMINI_MODEL
        ).strip()

        if not resolved_api_key:
            raise ConfigurationError(
                "GEMINI_API_KEY is not configured."
            )

        if not resolved_model:
            raise ConfigurationError(
                "GEMINI_MODEL is not configured."
            )

        self.model = resolved_model

        self.client = genai.Client(
            api_key=resolved_api_key,
        )

    def generate_structured[SchemaT: BaseModel](
        self,
        *,
        prompt: str,
        response_schema: type[SchemaT],
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AIProviderResponse[SchemaT]:
        """Generate one structured Gemini response."""

        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "Gemini prompt cannot be empty."
            )

        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
            system_instruction=system_instruction,
        )

        response = None
        last_error: Exception | None = None

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=cleaned_prompt,
                    config=config,
                )
                break

            except Exception as exc:
                last_error = exc

                error_text = str(exc).upper()

                transient = any(
                    marker in error_text
                    for marker in (
                        "429",
                        "500",
                        "502",
                        "503",
                        "504",
                        "RESOURCE_EXHAUSTED",
                        "UNAVAILABLE",
                        "HIGH DEMAND",
                    )
                )

                if not transient or attempt == 2:
                    raise AIServiceError(
                        "Gemini request failed.",
                        details={
                            "provider": self.provider_name,
                            "model": self.model,
                            "attempts": attempt + 1,
                            "error": str(exc),
                        },
                    ) from exc

                time.sleep(2 ** attempt)

        if response is None:
            raise AIServiceError(
                "Gemini request failed.",
                details={
                    "provider": self.provider_name,
                    "model": self.model,
                    "error": str(last_error),
                },
            )

        parsed = self._parse_response(
            response,
            response_schema,
        )

        usage = self._extract_usage(response)

        return AIProviderResponse(
            parsed=parsed,
            provider=self.provider_name,
            model=self.model,
            raw_text=getattr(response, "text", None),
            usage=usage,
            provider_metadata=self._metadata(response),
        )

    @staticmethod
    def _parse_response[SchemaT: BaseModel](
        response: Any,
        response_schema: type[SchemaT],
    ) -> SchemaT:
        """Validate Gemini structured output against the requested schema."""

        parsed = getattr(
            response,
            "parsed",
            None,
        )

        if isinstance(parsed, response_schema):
            return parsed

        if isinstance(parsed, dict):
            return response_schema.model_validate(
                parsed
            )

        text = getattr(
            response,
            "text",
            None,
        )

        if text:
            try:
                return response_schema.model_validate_json(
                    text
                )
            except Exception as exc:
                raise AIServiceError(
                    "Gemini returned an invalid structured response."
                ) from exc

        raise AIServiceError(
            "Gemini returned no structured response."
        )

    @staticmethod
    def _extract_usage(
        response: Any,
    ) -> AIProviderUsage | None:
        """Normalize Gemini token-usage metadata."""

        metadata = getattr(
            response,
            "usage_metadata",
            None,
        )

        if metadata is None:
            return None

        input_tokens = getattr(
            metadata,
            "prompt_token_count",
            None,
        )

        output_tokens = getattr(
            metadata,
            "candidates_token_count",
            None,
        )

        total_tokens = getattr(
            metadata,
            "total_token_count",
            None,
        )

        return AIProviderUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _metadata(
        response: Any,
    ) -> dict[str, Any]:
        """Extract lightweight provider metadata for observability."""

        metadata: dict[str, Any] = {}

        model_version = getattr(
            response,
            "model_version",
            None,
        )

        if model_version is not None:
            metadata["model_version"] = model_version

        response_id = getattr(
            response,
            "response_id",
            None,
        )

        if response_id is not None:
            metadata["response_id"] = response_id

        return metadata
