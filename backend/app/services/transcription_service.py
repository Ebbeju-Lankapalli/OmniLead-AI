"""Call-recording transcription orchestration."""

from __future__ import annotations

import subprocess
import tempfile
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

    def _normalize_audio(
        self,
        audio_path: str | Path,
    ) -> Path:
        """Normalize audio to a Whisper-friendly 16 kHz mono WAV."""

        source = Path(
            audio_path
        ).expanduser().resolve()

        if not source.exists():
            raise TranscriptionError(
                "Audio file does not exist.",
                details={
                    "audio_path": str(source),
                },
            )

        if not source.is_file():
            raise TranscriptionError(
                "Audio path is not a file.",
                details={
                    "audio_path": str(source),
                },
            )

        temp_directory = Path(
            tempfile.mkdtemp(
                prefix="omnilead-whisper-"
            )
        )

        normalized_path = (
            temp_directory / "normalized.wav"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(normalized_path),
        ]

        try:
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            ffmpeg_error = (
                process.stderr.strip()
            )

            # FFmpeg can return a non-zero exit code for partially corrupted
            # containers/codecs even when it successfully produces a usable
            # output file. This happens with some Android-generated M4A files.
            #
            # Therefore, validate the actual output instead of treating the
            # exit code alone as proof that normalization failed.
            output_exists = (
                normalized_path.exists()
                and normalized_path.is_file()
            )

            output_size = (
                normalized_path.stat().st_size
                if output_exists
                else 0
            )

            if not output_exists:
                raise TranscriptionError(
                    "FFmpeg did not produce a normalized audio file.",
                    details={
                        "audio_path": str(source),
                        "return_code": process.returncode,
                        "ffmpeg_error": ffmpeg_error[-4000:],
                    },
                )

            if output_size == 0:
                raise TranscriptionError(
                    "FFmpeg produced an empty normalized audio file.",
                    details={
                        "audio_path": str(source),
                        "return_code": process.returncode,
                        "ffmpeg_error": ffmpeg_error[-4000:],
                    },
                )

            # A non-zero return code with a valid, non-empty output can still
            # represent a usable partial decode. Whisper can process the
            # successfully decoded portion of the recording.
            if process.returncode != 0:
                # Keep the diagnostic information available without rejecting
                # the audio when FFmpeg successfully generated usable output.
                print(
                    "Warning: FFmpeg returned a non-zero exit code "
                    f"({process.returncode}) but produced a valid "
                    f"normalized audio file: {normalized_path}"
                )

                if ffmpeg_error:
                    print(
                        "FFmpeg warning:",
                        ffmpeg_error[-2000:],
                    )

            return normalized_path

        except TranscriptionError:
            with suppress(Exception):
                normalized_path.unlink()

            with suppress(Exception):
                temp_directory.rmdir()

            raise

        except Exception as exc:
            with suppress(Exception):
                normalized_path.unlink()

            with suppress(Exception):
                temp_directory.rmdir()

            raise TranscriptionError(
                "Audio normalization failed.",
                details={
                    "audio_path": str(source),
                    "error": str(exc),
                },
            ) from exc

    def _cleanup_normalized_audio(
        self,
        normalized_path: Path,
    ) -> None:
        """Remove temporary normalized audio."""

        temp_directory = (
            normalized_path.parent
        )

        with suppress(Exception):
            normalized_path.unlink()

        with suppress(Exception):
            temp_directory.rmdir()

    def transcribe_local_recording(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        audio_path: str | Path,
        *,
        language: str | None = None,
        vad_filter: bool = False,
    ) -> TranscriptionResult:
        """Normalize local audio, transcribe it, and persist the result."""

        recording = self.calls.get(
            organization_id,
            call_recording_id,
        )

        self.calls.mark_processing(
            organization_id,
            recording.id,
        )

        normalized_path: Path | None = None

        try:
            normalized_path = (
                self._normalize_audio(
                    audio_path
                )
            )

            result = self.transcriber.transcribe(
                normalized_path,
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

            if isinstance(
                exc,
                TranscriptionError,
            ):
                raise

            raise TranscriptionError(
                "Call transcription workflow failed.",
                details={
                    "call_recording_id": str(
                        recording.id
                    ),
                    "error": str(exc),
                },
            ) from exc

        finally:
            if normalized_path is not None:
                self._cleanup_normalized_audio(
                    normalized_path
                )