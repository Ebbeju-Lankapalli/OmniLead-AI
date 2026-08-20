"""Validation helpers for structured AI results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions import AIServiceError


def validate_structured_result[SchemaT: BaseModel](
    value: SchemaT | dict[str, Any],
    schema: type[SchemaT],
) -> SchemaT:
    """Validate arbitrary provider output against a Pydantic schema."""

    if isinstance(value, schema):
        return value

    try:
        return schema.model_validate(value)
    except PydanticValidationError as exc:
        raise AIServiceError(
            "AI structured output failed validation.",
            details={
                "schema": schema.__name__,
                "validation_errors": exc.errors(
                    include_url=False,
                ),
            },
        ) from exc


def require_non_empty_text(
    value: str | None,
    *,
    field_name: str,
) -> str:
    """Require non-empty text from workflow input."""

    if value is None:
        raise AIServiceError(
            f"{field_name} is required for AI analysis."
        )

    cleaned = value.strip()

    if not cleaned:
        raise AIServiceError(
            f"{field_name} cannot be empty for AI analysis."
        )

    return cleaned
