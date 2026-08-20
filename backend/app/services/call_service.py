"""Call-recording and transcription business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.call_recording import CallRecording
from app.repositories.customers import CustomerRepository
from app.repositories.leads import LeadRepository
from app.repositories.users import UserRepository
from app.schemas.call import (
    CallRecordingCreate,
    CallRecordingUpdate,
    CallTranscriptionFailure,
    CallTranscriptionUpdate,
)


class CallService:
    """Business operations for uploaded call recordings."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.customers = CustomerRepository(db)
        self.leads = LeadRepository(db)
        self.users = UserRepository(db)

    def get(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
    ) -> CallRecording:
        """Return an organization-scoped call recording."""

        recording = self.db.get(
            CallRecording,
            call_recording_id,
        )

        if (
            recording is None
            or recording.organization_id != organization_id
        ):
            raise NotFoundError(
                "Call recording not found.",
                details={
                    "call_recording_id": str(call_recording_id),
                },
            )

        return recording

    def create(
        self,
        payload: CallRecordingCreate,
    ) -> CallRecording:
        """Create call-recording metadata."""

        customer = self.customers.get(
            payload.customer_id
        )

        if (
            customer is None
            or customer.organization_id
            != payload.organization_id
        ):
            raise NotFoundError(
                "Customer not found.",
                details={
                    "customer_id": str(payload.customer_id),
                },
            )

        if payload.lead_id is not None:
            lead = self.leads.get(
                payload.lead_id
            )

            if (
                lead is None
                or lead.organization_id
                != payload.organization_id
            ):
                raise NotFoundError(
                    "Lead not found.",
                    details={
                        "lead_id": str(payload.lead_id),
                    },
                )

            if lead.customer_id != payload.customer_id:
                raise ValidationError(
                    "Call-recording customer does not match lead customer."
                )

        if payload.uploaded_by_user_id is not None:
            user = self.users.get(
                payload.uploaded_by_user_id
            )

            if (
                user is None
                or user.organization_id
                != payload.organization_id
            ):
                raise NotFoundError(
                    "Uploading user not found.",
                    details={
                        "user_id": str(
                            payload.uploaded_by_user_id
                        ),
                    },
                )

        existing = self.db.scalar(
            select(CallRecording).where(
                CallRecording.storage_path
                == payload.storage_path
            )
        )

        if existing is not None:
            raise ConflictError(
                "Call recording storage path already exists."
            )

        recording = CallRecording(
            **payload.model_dump()
        )

        try:
            self.db.add(recording)
            self.db.commit()
            self.db.refresh(recording)

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Call recording storage path already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return recording

    def update(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        payload: CallRecordingUpdate,
    ) -> CallRecording:
        """Update mutable call-recording metadata."""

        recording = self.get(
            organization_id,
            call_recording_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return recording

        try:
            for field_name, value in values.items():
                setattr(
                    recording,
                    field_name,
                    value,
                )

            self.db.commit()
            self.db.refresh(recording)

        except Exception:
            self.db.rollback()
            raise

        return recording

    def mark_processing(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
    ) -> CallRecording:
        """Mark transcription as processing."""

        return self.update(
            organization_id,
            call_recording_id,
            CallRecordingUpdate(
                transcription_status="PROCESSING",
            ),
        )

    def complete_transcription(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        payload: CallTranscriptionUpdate,
    ) -> CallRecording:
        """Persist a completed transcription."""

        if payload.transcription_status != "COMPLETED":
            raise ValidationError(
                "Completed transcription must use COMPLETED status."
            )

        if not payload.transcript:
            raise ValidationError(
                "Completed transcription requires transcript text."
            )

        return self.update(
            organization_id,
            call_recording_id,
            CallRecordingUpdate(
                transcription_status="COMPLETED",
                transcript=payload.transcript,
                transcript_language=payload.transcript_language,
                duration_seconds=payload.duration_seconds,
            ),
        )

    def fail_transcription(
        self,
        organization_id: UUID,
        call_recording_id: UUID,
        payload: CallTranscriptionFailure,
    ) -> CallRecording:
        """Persist failed-transcription state and error metadata."""

        recording = self.get(
            organization_id,
            call_recording_id,
        )

        metadata = dict(
            recording.recording_metadata
            or {}
        )

        metadata["transcription_error"] = payload.error

        return self.update(
            organization_id,
            call_recording_id,
            CallRecordingUpdate(
                transcription_status="FAILED",
                recording_metadata=metadata,
            ),
        )

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        customer_id: UUID | None = None,
        lead_id: UUID | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[CallRecording]:
        """Return filtered call recordings."""

        statement = select(CallRecording).where(
            CallRecording.organization_id
            == organization_id
        )

        if customer_id is not None:
            statement = statement.where(
                CallRecording.customer_id
                == customer_id
            )

        if lead_id is not None:
            statement = statement.where(
                CallRecording.lead_id
                == lead_id
            )

        if status is not None:
            normalized_status = (
                status.strip()
                .upper()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if normalized_status:
                statement = statement.where(
                    CallRecording.transcription_status
                    == normalized_status
                )

        statement = (
            statement
            .order_by(
                CallRecording.uploaded_at.desc(),
                CallRecording.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()
