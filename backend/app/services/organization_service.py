"""Organization business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.organization import Organization
from app.repositories.organizations import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


class OrganizationService:
    """Business operations for OmniLead AI organizations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.organizations = OrganizationRepository(db)

    def get(
        self,
        organization_id: UUID,
    ) -> Organization:
        """Return an organization or raise when it does not exist."""

        organization = self.organizations.get(organization_id)

        if organization is None:
            raise NotFoundError(
                "Organization not found.",
                details={
                    "organization_id": str(organization_id),
                },
            )

        return organization

    def get_by_slug(
        self,
        slug: str,
        *,
        active_only: bool = False,
    ) -> Organization:
        """Return an organization by slug."""

        if active_only:
            organization = self.organizations.get_active_by_slug(
                slug
            )
        else:
            organization = self.organizations.get_by_slug(
                slug
            )

        if organization is None:
            raise NotFoundError(
                "Organization not found.",
                details={
                    "slug": slug.strip().lower(),
                },
            )

        return organization

    def list_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Organization]:
        """Return active organizations."""

        return self.organizations.list_active(
            offset=offset,
            limit=limit,
        )

    def create(
        self,
        payload: OrganizationCreate,
    ) -> Organization:
        """Create a new organization."""

        if self.organizations.slug_exists(payload.slug):
            raise ConflictError(
                "Organization slug is already in use.",
                details={
                    "slug": payload.slug,
                },
            )

        organization = Organization(
            **payload.model_dump()
        )

        try:
            self.organizations.add(organization)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Organization could not be created because "
                "one of its unique values already exists.",
                details={
                    "slug": payload.slug,
                },
            ) from exc
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(organization)

        return organization

    def update(
        self,
        organization_id: UUID,
        payload: OrganizationUpdate,
    ) -> Organization:
        """Update mutable organization settings."""

        organization = self.get(organization_id)

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return organization

        try:
            self.organizations.update(
                organization,
                **values,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(organization)

        return organization

    def activate(
        self,
        organization_id: UUID,
    ) -> Organization:
        """Activate an organization."""

        organization = self.get(organization_id)

        if organization.is_active:
            return organization

        try:
            self.organizations.update(
                organization,
                is_active=True,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(organization)

        return organization

    def deactivate(
        self,
        organization_id: UUID,
    ) -> Organization:
        """Deactivate an organization without deleting its data."""

        organization = self.get(organization_id)

        if not organization.is_active:
            return organization

        try:
            self.organizations.update(
                organization,
                is_active=False,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        self.db.refresh(organization)

        return organization
