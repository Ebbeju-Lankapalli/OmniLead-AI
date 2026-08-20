"""Customer business logic."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.repositories.customers import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.identity_resolution_service import IdentityResolutionService
from app.utils.phone import normalize_phone_or_none


class CustomerService:
    """Business operations for unified OmniLead AI customers."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.customers = CustomerRepository(db)
        self.identity_resolution = IdentityResolutionService(db)

    def get(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> Customer:
        """Return a customer within an organization."""

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

        return customer

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Customer]:
        """Return customers for one organization."""

        return self.customers.list_by_organization(
            organization_id,
            include_archived=include_archived,
            offset=offset,
            limit=limit,
        )

    def search(
        self,
        organization_id: UUID,
        query: str,
        *,
        include_archived: bool = False,
        limit: int = 20,
    ) -> Sequence[Customer]:
        """Search customers by contact and profile fields."""

        return self.customers.search(
            organization_id,
            query,
            include_archived=include_archived,
            limit=limit,
        )

    def create(
        self,
        payload: CustomerCreate,
        *,
        create_primary_identities: bool = True,
    ) -> Customer:
        """Create a unified customer and deterministic primary identities."""

        values = payload.model_dump()

        phone = normalize_phone_or_none(
            values.get("primary_phone")
        )

        email_value = values.get("primary_email")
        email = (
            str(email_value).strip().lower()
            if email_value is not None
            else None
        )

        values["primary_phone"] = phone
        values["primary_email"] = email

        if phone is not None:
            existing_phone_customer = (
                self.identity_resolution.resolve(
                    payload.organization_id,
                    "PHONE",
                    phone,
                )
            )

            if existing_phone_customer is not None:
                raise ConflictError(
                    "A customer with this phone identity already exists.",
                    details={
                        "customer_id": str(
                            existing_phone_customer.id
                        ),
                        "phone": phone,
                    },
                )

        if email is not None:
            existing_email_customer = (
                self.identity_resolution.resolve(
                    payload.organization_id,
                    "EMAIL",
                    email,
                )
            )

            if existing_email_customer is not None:
                raise ConflictError(
                    "A customer with this email identity already exists.",
                    details={
                        "customer_id": str(
                            existing_email_customer.id
                        ),
                        "email": email,
                    },
                )

        customer = Customer(**values)

        try:
            self.customers.add(customer)

            if create_primary_identities:
                if phone is not None:
                    self.identity_resolution.add_identity(
                        payload.organization_id,
                        customer.id,
                        identity_type="PHONE",
                        identity_value=phone,
                        is_primary=True,
                        is_verified=False,
                        source="MANUAL",
                        commit=False,
                    )

                if email is not None:
                    self.identity_resolution.add_identity(
                        payload.organization_id,
                        customer.id,
                        identity_type="EMAIL",
                        identity_value=email,
                        is_primary=True,
                        is_verified=False,
                        source="MANUAL",
                        commit=False,
                    )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Customer could not be created because "
                "a unique identity already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)

        return customer

    def update(
        self,
        organization_id: UUID,
        customer_id: UUID,
        payload: CustomerUpdate,
    ) -> Customer:
        """Update mutable customer fields."""

        customer = self.get(
            organization_id,
            customer_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return customer

        if "primary_phone" in values:
            phone = normalize_phone_or_none(
                values["primary_phone"]
            )
            values["primary_phone"] = phone

            if phone is not None:
                existing = self.identity_resolution.resolve(
                    organization_id,
                    "PHONE",
                    phone,
                )

                if (
                    existing is not None
                    and existing.id != customer.id
                ):
                    raise ConflictError(
                        "Phone identity belongs to another customer.",
                        details={
                            "customer_id": str(existing.id),
                            "phone": phone,
                        },
                    )

        if "primary_email" in values:
            email_value = values["primary_email"]
            email = (
                str(email_value).strip().lower()
                if email_value is not None
                else None
            )

            values["primary_email"] = email

            if email is not None:
                existing = self.identity_resolution.resolve(
                    organization_id,
                    "EMAIL",
                    email,
                )

                if (
                    existing is not None
                    and existing.id != customer.id
                ):
                    raise ConflictError(
                        "Email identity belongs to another customer.",
                        details={
                            "customer_id": str(existing.id),
                            "email": email,
                        },
                    )

        try:
            self.customers.update(
                customer,
                **values,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)

        return customer

    def touch(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        seen_at: datetime,
    ) -> Customer:
        """Update the customer's latest-seen timestamp."""

        customer = self.get(
            organization_id,
            customer_id,
        )

        try:
            self.customers.update(
                customer,
                last_seen_at=seen_at,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)

        return customer

    def archive(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        archived_at: datetime,
    ) -> Customer:
        """Archive a customer without deleting historical data."""

        customer = self.get(
            organization_id,
            customer_id,
        )

        if customer.archived_at is not None:
            return customer

        try:
            self.customers.update(
                customer,
                archived_at=archived_at,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)

        return customer

    def restore(
        self,
        organization_id: UUID,
        customer_id: UUID,
    ) -> Customer:
        """Restore an archived customer."""

        customer = self.get(
            organization_id,
            customer_id,
        )

        if customer.archived_at is None:
            return customer

        try:
            self.customers.update(
                customer,
                archived_at=None,
            )
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(customer)

        return customer

    def resolve_identity(
        self,
        organization_id: UUID,
        *,
        identity_type: str,
        identity_value: str,
    ) -> Customer:
        """Resolve a deterministic identity to a customer."""

        customer = self.identity_resolution.resolve(
            organization_id,
            identity_type,
            identity_value,
        )

        if customer is None:
            raise NotFoundError(
                "No customer matches the supplied identity.",
                details={
                    "identity_type": identity_type,
                },
            )

        return customer

    def add_identity(
        self,
        organization_id: UUID,
        customer_id: UUID,
        *,
        identity_type: str,
        identity_value: str,
        is_primary: bool = False,
        is_verified: bool = False,
        source: str | None = None,
    ) -> None:
        """Attach another deterministic identity to a customer."""

        self.get(
            organization_id,
            customer_id,
        )

        if not identity_value.strip():
            raise ValidationError(
                "Customer identity value cannot be empty."
            )

        self.identity_resolution.add_identity(
            organization_id,
            customer_id,
            identity_type=identity_type,
            identity_value=identity_value,
            is_primary=is_primary,
            is_verified=is_verified,
            source=source,
            commit=True,
        )
