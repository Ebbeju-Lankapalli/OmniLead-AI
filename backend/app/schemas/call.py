"""Call recording and transcription request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.core.constants import (
    DEFAULT_MAX_UPLOAD_SIZE_MB,
    SUPPORTED_AUDIO_EXTENSIONS,
)
from app.schemas.common import ORMModel, TimestampedSchema

TranscriptionStatus = Literal[
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
]


class CallRecordingBase(ORMModel):
    """Shared call recording fields."""

    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    file_size_bytes: int = Field(ge=1)
    duration_seconds: int | None = Field(default=None, ge=0)
    transcription_status: TranscriptionStatus = "PENDING"
    transcript: str | None = None
    transcript_language: str | None = Field(default=None, max_length=20)
    recorded_at: datetime | None = None
    recording_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("original_filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Original filename cannot be empty.")

        if "." not in cleaned:
            raise ValueError("Audio filename must include an extension.")

        extension = cleaned.rsplit(".", 1)[-1].lower()

        if extension not in SUPPORTED_AUDIO_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise ValueError(
                f"Unsupported audio extension '{extension}'. "
                f"Supported extensions: {supported}."
            )

        return cleaned

    @field_validator("mime_type")
    @classmethod
    def normalize_mime_type(cls, value: str) -> str:
        cleaned = value.strip().lower()

        if not cleaned:
            raise ValueError("MIME type cannot be empty.")

        return cleaned

    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size(cls, value: int) -> int:
        max_bytes = DEFAULT_MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if value > max_bytes:
            raise ValueError(
                f"Audio file exceeds the "
                f"{DEFAULT_MAX_UPLOAD_SIZE_MB} MB upload limit."
            )

        return value

    @field_validator("transcript")
    @classmethod
    def normalize_transcript(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("transcript_language")
    @classmethod
    def normalize_transcript_language(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().lower()
        return cleaned or None


class CallRecordingCreate(CallRecordingBase):
    """Create metadata for an uploaded call recording."""

    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    uploaded_by_user_id: UUID | None = None
    storage_path: str = Field(min_length=1)

    @field_validator("storage_path")
    @classmethod
    def normalize_storage_path(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Storage path cannot be empty.")

        return cleaned


class CallRecordingUpdate(ORMModel):
    """Update mutable call recording metadata."""

    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    transcription_status: TranscriptionStatus | None = None
    transcript: str | None = None
    transcript_language: str | None = Field(default=None, max_length=20)
    recorded_at: datetime | None = None
    recording_metadata: dict[str, Any] | None = None

    @field_validator("transcript")
    @classmethod
    def normalize_optional_transcript(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("transcript_language")
    @classmethod
    def normalize_optional_language(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().lower()
        return cleaned or None


class CallRecordingResponse(CallRecordingBase, TimestampedSchema):
    """Full call recording returned by the API."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    uploaded_by_user_id: UUID | None = None
    storage_path: str
    uploaded_at: datetime


class CallRecordingSummary(ORMModel):
    """Compact call recording representation for call history."""

    id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    original_filename: str
    duration_seconds: int | None = None
    transcription_status: TranscriptionStatus
    transcript_language: str | None = None
    recorded_at: datetime | None = None
    uploaded_at: datetime


class CallUploadRequest(ORMModel):
    """Metadata supplied alongside a call recording upload."""

    organization_id: UUID
    customer_id: UUID
    lead_id: UUID | None = None
    conversation_id: UUID | None = None
    recorded_at: datetime | None = None
    recording_metadata: dict[str, Any] = Field(default_factory=dict)


class CallTranscriptionUpdate(ORMModel):
    """Internal payload for transcription task results."""

    transcription_status: TranscriptionStatus
    transcript: str | None = None
    transcript_language: str | None = Field(default=None, max_length=20)
    duration_seconds: int | None = Field(default=None, ge=0)

    @field_validator("transcript")
    @classmethod
    def normalize_transcription_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("transcript_language")
    @classmethod
    def normalize_transcription_language(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip().lower()
        return cleaned or None


class CallTranscriptionFailure(ORMModel):
    """Internal payload for failed transcription jobs."""

    transcription_status: Literal["FAILED"] = "FAILED"
    error: str = Field(min_length=1)

    @field_validator("error")
    @classmethod
    def normalize_error(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Transcription error cannot be empty.")

        return cleaned


class CallIntelligenceResponse(ORMModel):
    """AI intelligence returned after processing a call recording."""

    analysis_id: UUID

    summary: str
    purchase_intent: str | None = None
    sentiment: str | None = None
    requirement: str | None = None

    objections: list[str] = Field(default_factory=list)
    commitments: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    customer_questions: list[str] = Field(default_factory=list)
    key_moments: list[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)
    requires_review: bool = False


class CallUploadProcessingResponse(ORMModel):
    """Response returned after upload, transcription, and AI analysis."""

    call_recording_id: UUID
    storage_path: str

    transcription_status: TranscriptionStatus
    transcript: str
    transcript_language: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)

    intelligence: CallIntelligenceResponse
