"""Shared Pydantic schemas used across OmniLead AI APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    """Base schema configured for SQLAlchemy ORM objects."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class TimestampedSchema(ORMModel):
    """Common timestamps returned by persisted resources."""

    created_at: datetime
    updated_at: datetime


class IdentifiedSchema(ORMModel):
    """Common UUID identifier returned by persisted resources."""

    id: UUID


class APIMessage(ORMModel):
    """Simple API acknowledgement response."""

    message: str = Field(min_length=1)


class ErrorDetail(ORMModel):
    """Structured field-level error information."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(ORMModel):
    """Standard API error response."""

    error: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: str | None = None


class PaginationMeta(ORMModel):
    """Pagination metadata returned with list endpoints."""

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


class PaginatedResponse[T](ORMModel):
    """Generic paginated API response."""

    items: list[T]
    pagination: PaginationMeta


class IDResponse(ORMModel):
    """Response containing only a resource identifier."""

    id: UUID


class HealthResponse(ORMModel):
    """Basic application health-check response."""

    status: str
    app: str
    environment: str
    timestamp: datetime


class MetadataResponse(ORMModel):
    """Flexible metadata payload for internal/API use."""

    data: dict[str, Any] = Field(default_factory=dict)
