"""Organization repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.organization import Organization
from app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """Data-access operations for organizations."""

    model = Organization

    def get_by_slug(
        self,
        slug: str,
    ) -> Organization | None:
        """Return one organization by unique slug."""

        normalized_slug = slug.strip().lower()

        if not normalized_slug:
            return None

        statement = select(Organization).where(
            Organization.slug == normalized_slug
        )

        return self.db.scalar(statement)

    def get_active_by_slug(
        self,
        slug: str,
    ) -> Organization | None:
        """Return one active organization by slug."""

        normalized_slug = slug.strip().lower()

        if not normalized_slug:
            return None

        statement = select(Organization).where(
            Organization.slug == normalized_slug,
            Organization.is_active.is_(True),
        )

        return self.db.scalar(statement)

    def list_active(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Organization]:
        """Return active organizations ordered by name."""

        statement = (
            select(Organization)
            .where(Organization.is_active.is_(True))
            .order_by(Organization.name, Organization.id)
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def slug_exists(
        self,
        slug: str,
    ) -> bool:
        """Return whether an organization slug already exists."""

        normalized_slug = slug.strip().lower()

        if not normalized_slug:
            return False

        statement = (
            select(Organization.id)
            .where(Organization.slug == normalized_slug)
            .limit(1)
        )

        return self.db.scalar(statement) is not None
