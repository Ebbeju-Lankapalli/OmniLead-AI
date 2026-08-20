"""Base interfaces and response types for AI providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass(slots=True)
class AIProviderUsage:
    """Token-usage metadata returned by an AI provider."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(slots=True)
class AIProviderResponse[SchemaT: BaseModel]:
    """Normalized structured response returned by an AI provider."""

    parsed: SchemaT

    provider: str
    model: str

    raw_text: str | None = None

    usage: AIProviderUsage | None = None

    provider_metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    """Abstract interface implemented by supported LLM providers."""

    provider_name: str

    @abstractmethod
    def generate_structured[SchemaT: BaseModel](
        self,
        *,
        prompt: str,
        response_schema: type[SchemaT],
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AIProviderResponse[SchemaT]:
        """Generate a validated structured response."""
