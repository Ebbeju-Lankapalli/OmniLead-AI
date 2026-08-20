"""End-to-end call transcription and AI intelligence orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.providers.base import AIProvider
from app.ai.workflows.call_intelligence import (
    CallIntelligenceWorkflow,
    CallIntelligenceWorkflowResult,
)
from app.integrations.transcription import (
    FasterWhisperTranscriber,
    TranscriptionResult,
)
from app.services.call_service import CallService
from app.services.transcription_service import TranscriptionService


@dataclass(slots=True)
class CompleteCallIntelligenceResult:
    """Combined transcription and AI-analysis result."""

    call_recording_id: UUID

    transcription: TranscriptionResult
    intelligence: CallIntelligenceWorkflowResult


class CompleteCallIntelligenceService:
    """Run speech-to-text followed by structured AI call intelligence."""

    def __init__(
        self,
        db: Session,
        provider: AIProvider,
        *,
        transcriber: FasterWhisperTranscriber | None = None,
    ) -> None:
        self.db = db

        self.calls = CallService(db)

        self.transcription = TranscriptionService(
            db,
            transcriber=transcriber,
        )

        self.intelligence = CallIntelligenceWorkflow(
            db,
            provider,
        )

    def process_local_audio(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        audio_path: str | Path,
        *,
        language: str | None = None,
        vad_filter: bool = False,
        force_ai_refresh: bool = False,
    ) -> CompleteCallIntelligenceResult:
        """Transcribe local audio and run structured call intelligence."""

        self.calls.get(
            organization_id,
            call_recording_id,
        )

        transcription = (
            self.transcription.transcribe_local_recording(
                organization_id,
                call_recording_id,
                audio_path,
                language=language,
                vad_filter=vad_filter,
            )
        )

        intelligence = self.intelligence.run(
            organization_id,
            call_recording_id,
            force_refresh=force_ai_refresh,
        )

        return CompleteCallIntelligenceResult(
            call_recording_id=call_recording_id,
            transcription=transcription,
            intelligence=intelligence,
        )
