"""Call-recording upload and processing orchestration."""

from __future__ import annotations

import mimetypes
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.ai.providers.base import AIProvider
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.integrations.storage import SupabaseStorageService
from app.integrations.transcription import FasterWhisperTranscriber
from app.schemas.call import CallRecordingCreate, CallUploadRequest
from app.services.call_intelligence_service import (
    CompleteCallIntelligenceResult,
    CompleteCallIntelligenceService,
)
from app.services.call_service import CallService


@dataclass(slots=True)
class CallUploadProcessingResult:
    """Result of upload + transcription + AI processing."""

    call_recording_id: UUID
    storage_path: str
    intelligence: CompleteCallIntelligenceResult


class CallUploadService:
    """Upload call audio to Supabase and process it end to end."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
        *,
        storage: SupabaseStorageService | None = None,
        transcriber: FasterWhisperTranscriber | None = None,
    ) -> None:
        self.db = db
        self.calls = CallService(db)

        self.storage = (
            storage
            or SupabaseStorageService()
        )

        self.processing = CompleteCallIntelligenceService(
            db,
            provider,
            transcriber=transcriber,
        )

    def upload_and_process(
        self,
        payload: CallUploadRequest,
        *,
        filename: str,
        content: bytes,
        uploaded_by_user_id: UUID | None = None,
        content_type: str | None = None,
        vad_filter: bool = False,
        force_ai_refresh: bool = False,
    ) -> CallUploadProcessingResult:
        """Upload audio and process it through Whisper and Gemini."""

        cleaned_filename = Path(filename).name.strip()

        if not cleaned_filename:
            raise ValidationError(
                "Uploaded audio filename cannot be empty."
            )

        extension = (
            Path(cleaned_filename)
            .suffix.lower()
            .lstrip(".")
        )

        if extension not in settings.ALLOWED_AUDIO_EXTENSIONS:
            raise ValidationError(
                "Unsupported call-recording extension.",
                details={
                    "extension": extension,
                },
            )

        if not content:
            raise ValidationError(
                "Uploaded call recording is empty."
            )

        maximum_bytes = (
            settings.MAX_AUDIO_FILE_SIZE_MB
            * 1024
            * 1024
        )

        if len(content) > maximum_bytes:
            raise ValidationError(
                "Uploaded call recording exceeds maximum size.",
                details={
                    "file_size_bytes": len(content),
                    "maximum_bytes": maximum_bytes,
                },
            )

        mime_type = (
            content_type
            or mimetypes.guess_type(cleaned_filename)[0]
            or "application/octet-stream"
        )

        storage_path = (
            f"{payload.organization_id}/"
            f"{payload.customer_id}/"
            f"{uuid4()}/"
            f"{cleaned_filename}"
        )

        suffix = f".{extension}"

        with tempfile.TemporaryDirectory(
            prefix="omnilead-call-"
        ) as temp_directory:
            local_upload_path = (
                Path(temp_directory)
                / f"upload{suffix}"
            )

            local_upload_path.write_bytes(
                content
            )

            self.storage.upload_file(
                local_upload_path,
                storage_path,
                content_type=mime_type,
                upsert=False,
            )

            recording = None

            try:
                recording = self.calls.create(
                    CallRecordingCreate(
                        organization_id=payload.organization_id,
                        customer_id=payload.customer_id,
                        lead_id=payload.lead_id,
                        conversation_id=payload.conversation_id,
                        uploaded_by_user_id=uploaded_by_user_id,
                        storage_path=storage_path,
                        original_filename=cleaned_filename,
                        mime_type=mime_type,
                        file_size_bytes=len(content),
                        transcription_status="PENDING",
                        recorded_at=payload.recorded_at,
                        recording_metadata=payload.recording_metadata,
                    )
                )

                downloaded_path = (
                    Path(temp_directory)
                    / f"downloaded{suffix}"
                )

                self.storage.download_file(
                    storage_path,
                    downloaded_path,
                )

                intelligence = self.processing.process_local_audio(
                    payload.organization_id,
                    recording.id,
                    downloaded_path,
                    vad_filter=vad_filter,
                    force_ai_refresh=force_ai_refresh,
                )

                return CallUploadProcessingResult(
                    call_recording_id=recording.id,
                    storage_path=storage_path,
                    intelligence=intelligence,
                )

            except Exception:
                if recording is None:
                    self.storage.delete_file(
                        storage_path
                    )

                raise
