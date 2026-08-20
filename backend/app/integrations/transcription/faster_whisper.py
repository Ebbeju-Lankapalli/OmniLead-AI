"""Faster-Whisper transcription integration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.exceptions import ConfigurationError, TranscriptionError


@dataclass(slots=True)
class TranscriptionSegment:
    """One timestamped transcription segment."""

    start: float
    end: float
    text: str


@dataclass(slots=True)
class TranscriptionResult:
    """Structured transcription result."""

    text: str
    language: str | None
    language_probability: float | None
    duration_seconds: int | None
    segments: list[TranscriptionSegment]


class FasterWhisperTranscriber:
    """Local Faster-Whisper speech-to-text provider."""

    def __init__(
        self,
        *,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        self.model_size = (
            model_size
            or settings.WHISPER_MODEL_SIZE
        ).strip()

        self.device = (
            device
            or settings.WHISPER_DEVICE
        ).strip()

        self.compute_type = (
            compute_type
            or settings.WHISPER_COMPUTE_TYPE
        ).strip()

        if not self.model_size:
            raise ConfigurationError(
                "Whisper model size is not configured."
            )

        if not self.device:
            raise ConfigurationError(
                "Whisper device is not configured."
            )

        if not self.compute_type:
            raise ConfigurationError(
                "Whisper compute type is not configured."
            )

        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as exc:
            raise TranscriptionError(
                "Failed to initialize Faster-Whisper.",
                details={
                    "model_size": self.model_size,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "error": str(exc),
                },
            ) from exc

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        language: str | None = None,
        beam_size: int = 5,
        vad_filter: bool = False,
    ) -> TranscriptionResult:
        """Transcribe a local audio file."""

        path = Path(audio_path).expanduser().resolve()

        if not path.exists():
            raise TranscriptionError(
                "Audio file does not exist.",
                details={
                    "audio_path": str(path),
                },
            )

        if not path.is_file():
            raise TranscriptionError(
                "Audio path is not a file.",
                details={
                    "audio_path": str(path),
                },
            )

        extension = (
            path.suffix
            .lower()
            .lstrip(".")
        )

        if (
            extension
            and extension
            not in settings.ALLOWED_AUDIO_EXTENSIONS
        ):
            raise TranscriptionError(
                "Unsupported audio file extension.",
                details={
                    "extension": extension,
                },
            )

        max_bytes = (
            settings.MAX_AUDIO_FILE_SIZE_MB
            * 1024
            * 1024
        )

        file_size = path.stat().st_size

        if file_size > max_bytes:
            raise TranscriptionError(
                "Audio file exceeds configured upload limit.",
                details={
                    "file_size_bytes": file_size,
                    "maximum_bytes": max_bytes,
                },
            )

        try:
            raw_segments, info = self.model.transcribe(
                str(path),
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )

            segments: list[TranscriptionSegment] = []
            text_parts: list[str] = []

            for raw_segment in raw_segments:
                cleaned = raw_segment.text.strip()

                if not cleaned:
                    continue

                text_parts.append(cleaned)

                segments.append(
                    TranscriptionSegment(
                        start=float(raw_segment.start),
                        end=float(raw_segment.end),
                        text=cleaned,
                    )
                )

            transcript = " ".join(
                text_parts
            ).strip()

            if not transcript:
                raise TranscriptionError(
                    "Whisper returned an empty transcript."
                )

            duration = getattr(
                info,
                "duration",
                None,
            )

            detected_language = getattr(
                info,
                "language",
                None,
            )

            language_probability = getattr(
                info,
                "language_probability",
                None,
            )

            return TranscriptionResult(
                text=transcript,
                language=detected_language,
                language_probability=(
                    float(language_probability)
                    if language_probability is not None
                    else None
                ),
                duration_seconds=(
                    round(float(duration))
                    if duration is not None
                    else None
                ),
                segments=segments,
            )

        except TranscriptionError:
            raise

        except Exception as exc:
            raise TranscriptionError(
                "Faster-Whisper transcription failed.",
                details={
                    "audio_path": str(path),
                    "error": str(exc),
                },
            ) from exc
