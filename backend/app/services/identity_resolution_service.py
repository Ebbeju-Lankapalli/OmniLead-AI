"""Deterministic omnichannel customer identity resolution."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.repositories.customers import CustomerRepository
from app.utils.phone import normalize_phone


class IdentityResolutionService:
    """
    Resolve external identities to unified OmniLead AI customers.

    Deterministic identity matching is preferred over AI-based matching for
    stable identifiers such as phone, email, WhatsApp ID, and Instagram ID.
    """

    SUPPORTED_IDENTITY_TYPES = frozenset(
        {
            "PHONE",
            "EMAIL",
            "WHATSAPP",
            "INSTAGRAM",
        }
    )

    def __init__(self, db: Session) -> None:
        self.db = db
        self.customers = CustomerRepository(db)

    @classmethod
    def normalize_identity_type(
        cls,
        identity_type: str,
    ) -> str:
        """Normalize and validate an identity type."""

        normalized = (
            identity_type.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )

        if normalized not in cls.SUPPORTED_IDENTITY_TYPES:
            raise ValidationError(
                "Unsupported customer identity type.",
                details={
                    "identity_type": normalized,
                    "supported_types": sorted(
                        cls.SUPPORTED_IDENTITY_TYPES
                    ),
                },
            )

        return normalized

    @classmethod
    def normalize_identity_value(
        cls,
        identity_type: str,
        value: str,
    ) -> str:
        """Return the canonical normalized identity value."""

        normalized_type = cls.normalize_identity_type(
            identity_type
        )

        cleaned = value.strip()

        if not cleaned:
            raise ValidationError(
                "Customer identity value cannot be empty."
            )

        try:
            if normalized_type in {"PHONE", "WHATSAPP"}:
                return normalize_phone(cleaned)

            if normalized_type == "EMAIL":
                return cleaned.lower()

            if normalized_type == "INSTAGRAM":
                return cleaned.lstrip("@").lower()
        except ValueError as exc:
            raise ValidationError(
                str(exc),
                details={
                    "identity_type": normalized_type,
                },
            ) from exc

        raise ValidationError(
            "Unsupported customer identity type."
        )

    def resolve(
        self,
        organization_id: UUID,
        identity_type: str,
        identity_value: str,
    ) -> Customer | None:
        """Resolve one normalized identity to a unified customer."""

        normalized_type = self.normalize_identity_type(
            identity_type
        )
        normalized_value = self.normalize_identity_value(
            normalized_type,
            identity_value,
        )

        return self.customers.get_by_identity(
            organization_id,
            normalized_type,
            normalized_value,
        )

    def get_identity(
        self,
        organization_id: UUID,
        identity_type: str,
        identity_value: str,
    ) -> CustomerIdentity | None:
        """Return the persisted identity record itself."""

        normalized_type = self.normalize_identity_type(
            identity_type
        )
        normalized_value = self.normalize_identity_value(
            normalized_type,
            identity_value,
        )

        statement = select(CustomerIdentity).where(
            CustomerIdentity.organization_id == organization_id,
            CustomerIdentity.identity_type == normalized_type,
            CustomerIdentity.normalized_value == normalized_value,
        )

        return self.db.scalar(statement)

    def add_identity(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        identity_type: str,
        identity_value: str,
        display_value: str | None = None,
        is_primary: bool = False,
        is_verified: bool = False,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> CustomerIdentity:
        """Attach a deterministic identity to a customer."""

        customer = self.customers.get(customer_id)

        if (
            customer is None
            or customer.organization_id != organization_id
        ):
            raise NotFoundError(
                "Customer not found.",
                details={
                    "customer_id": str(customer_id),
                },
            )

        normalized_type = self.normalize_identity_type(
            identity_type
        )
        normalized_value = self.normalize_identity_value(
            normalized_type,
            identity_value,
        )

        existing = self.get_identity(
            organization_id,
            normalized_type,
            normalized_value,
        )

        if existing is not None:
            if existing.customer_id == customer_id:
                return existing

            raise ConflictError(
                "Customer identity already belongs to another customer.",
                details={
                    "identity_type": normalized_type,
                    "normalized_value": normalized_value,
                    "existing_customer_id": str(
                        existing.customer_id
                    ),
                },
            )

        identity = CustomerIdentity(
            organization_id=organization_id,
            customer_id=customer_id,
            identity_type=normalized_type,
            identity_value=identity_value.strip(),
            normalized_value=normalized_value,
            display_value=(
                display_value.strip()
                if display_value
                else identity_value.strip()
            ),
            is_primary=is_primary,
            is_verified=is_verified,
            source=(
                source.strip().upper()
                if source and source.strip()
                else None
            ),
            identity_metadata=metadata or {},
        )

        try:
            self.db.add(identity)
            self.db.flush()

            if commit:
                self.db.commit()
                self.db.refresh(identity)
        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Customer identity already exists.",
                details={
                    "identity_type": normalized_type,
                    "normalized_value": normalized_value,
                },
            ) from exc
        except Exception:
            self.db.rollback()
            raise

        return identity

    def list_identities(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> list[CustomerIdentity]:
        """Return identities belonging to a customer."""

        statement = (
            select(CustomerIdentity)
            .where(
                CustomerIdentity.organization_id == organization_id,
                CustomerIdentity.customer_id == customer_id,
            )
            .order_by(
                CustomerIdentity.is_primary.desc(),
                CustomerIdentity.identity_type,
                CustomerIdentity.id,
            )
        )

        return list(self.db.scalars(statement).all())
