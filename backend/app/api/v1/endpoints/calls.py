"""Call-recording API endpoints."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile

from app.ai.providers.gemini import GeminiProvider
from app.api.deps import CurrentUser, DatabaseSession
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.schemas.call import (
    CallIntelligenceResponse,
    CallUploadProcessingResponse,
    CallUploadRequest,
)
from app.services.call_service import CallService
from app.services.call_upload_service import CallUploadService

router = APIRouter(
    prefix="/calls",
    tags=["calls"],
)


@router.post(
    "/upload",
    response_model=CallUploadProcessingResponse,
    status_code=201,
)
def upload_call_recording(
    db: DatabaseSession,
    current_user: CurrentUser,
    file: Annotated[
        UploadFile,
        File(description="Call recording audio file"),
    ],
    customer_id: Annotated[
        UUID,
        Form(),
    ],
    lead_id: Annotated[
        UUID | None,
        Form(),
    ] = None,
    conversation_id: Annotated[
        UUID | None,
        Form(),
    ] = None,
    recorded_at: Annotated[
        datetime | None,
        Form(),
    ] = None,
    metadata_json: Annotated[
        str | None,
        Form(),
    ] = None,
) -> CallUploadProcessingResponse:
    """
    Upload a call recording and process it through Whisper and Gemini.

    The authenticated user's organization is always used. Clients cannot
    choose another organization ID.
    """

    if not settings.CALL_INTELLIGENCE_ENABLED:
        raise ValidationError(
            "Call intelligence is currently disabled."
        )

    filename = (
        file.filename
        or ""
    ).strip()

    if not filename:
        raise ValidationError(
            "Uploaded call recording must have a filename."
        )

    content = file.file.read()

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

    recording_metadata: dict[str, object] = {}

    if metadata_json:
        try:
            parsed_metadata = json.loads(
                metadata_json
            )
        except json.JSONDecodeError as exc:
            raise ValidationError(
                "metadata_json must contain valid JSON."
            ) from exc

        if not isinstance(parsed_metadata, dict):
            raise ValidationError(
                "metadata_json must contain a JSON object."
            )

        recording_metadata = parsed_metadata

    # Validate organization-scoped customer/lead relationships early.
    calls = CallService(db)

    customer = calls.customers.get(
        customer_id
    )

    if (
        customer is None
        or customer.organization_id
        != current_user.organization_id
    ):
        raise ValidationError(
            "Customer does not belong to the authenticated organization."
        )

    if lead_id is not None:
        lead = calls.leads.get(
            lead_id
        )

        if (
            lead is None
            or lead.organization_id
            != current_user.organization_id
        ):
            raise ValidationError(
                "Lead does not belong to the authenticated organization."
            )

        if lead.customer_id != customer_id:
            raise ValidationError(
                "Lead customer does not match uploaded call customer."
            )

    provider = GeminiProvider()

    service = CallUploadService(
        db,
        provider,
    )

    result = service.upload_and_process(
        CallUploadRequest(
            organization_id=current_user.organization_id,
            customer_id=customer_id,
            lead_id=lead_id,
            conversation_id=conversation_id,
            recorded_at=recorded_at,
            recording_metadata=recording_metadata,
        ),
        filename=filename,
        content=content,
        uploaded_by_user_id=current_user.id,
        content_type=file.content_type,
        vad_filter=False,
        force_ai_refresh=False,
    )

    recording = calls.get(
        current_user.organization_id,
        result.call_recording_id,
    )

    ai = result.intelligence.intelligence

    return CallUploadProcessingResponse(
        call_recording_id=recording.id,
        storage_path=result.storage_path,
        transcription_status=recording.transcription_status,
        transcript=recording.transcript or "",
        transcript_language=recording.transcript_language,
        duration_seconds=recording.duration_seconds,
        intelligence=CallIntelligenceResponse(
            analysis_id=ai.analysis_id,
            summary=ai.summary,
            purchase_intent=ai.purchase_intent,
            sentiment=ai.sentiment,
            requirement=ai.requirement,
            objections=ai.objections,
            commitments=ai.commitments,
            action_items=ai.action_items,
            customer_questions=ai.customer_questions,
            key_moments=ai.key_moments,
            confidence=ai.confidence,
            requires_review=ai.requires_review,
        ),
    )
