"""Call-recording transcription orchestration."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import TranscriptionError
from app.integrations.transcription import (
    FasterWhisperTranscriber,
    TranscriptionResult,
)
from app.schemas.call import (
    CallTranscriptionFailure,
    CallTranscriptionUpdate,
)
from app.services.call_service import CallService


class TranscriptionService:
    """Transcribe call audio and persist transcription results."""

    def __init__(
        self,
        db: Session,
        *,
        transcriber: FasterWhisperTranscriber | None = None,
    ) -> None:
        self.db = db
        self.calls = CallService(db)
        self.transcriber = (
            transcriber
            or FasterWhisperTranscriber()
        )

    def transcribe_local_recording(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        audio_path: str | Path,
        *,
        language: str | None = None,
        vad_filter: bool = False,
    ) -> TranscriptionResult:
        """Transcribe local audio and persist the completed result."""

        recording = self.calls.get(
            organization_id,
            call_recording_id,
        )

        self.calls.mark_processing(
            organization_id,
            recording.id,
        )

        try:
            result = self.transcriber.transcribe(
                audio_path,
                language=language,
                vad_filter=vad_filter,
            )

            self.calls.complete_transcription(
                organization_id,
                recording.id,
                CallTranscriptionUpdate(
                    transcription_status="COMPLETED",
                    transcript=result.text,
                    transcript_language=result.language,
                    duration_seconds=result.duration_seconds,
                ),
            )

            return result

        except Exception as exc:
            with suppress(Exception):
                self.calls.fail_transcription(
                    organization_id,
                    recording.id,
                    CallTranscriptionFailure(
                        error=str(exc),
                    ),
                )

            if isinstance(exc, TranscriptionError):
                raise

            raise TranscriptionError(
                "Call transcription workflow failed.",
                details={
                    "call_recording_id": str(recording.id),
                    "error": str(exc),
                },
            ) from exc
