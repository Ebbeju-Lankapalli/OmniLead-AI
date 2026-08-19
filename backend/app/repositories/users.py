"""User repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data-access operations for OmniLead AI users."""

    model = User

    def get_by_auth_user_id(
        self,
        auth_user_id: UUID,
    ) -> User | None:
        """Return a user by Supabase Auth user ID."""

        statement = select(User).where(
            User.auth_user_id == auth_user_id
        )

        return self.db.scalar(statement)

    def get_by_email(
        self,
        organization_id: UUID,
        email: str,
    ) -> User | None:
        """Return a user by organization and email."""

        normalized_email = email.strip().lower()

        if not normalized_email:
            return None

        statement = select(User).where(
            User.organization_id == organization_id,
            User.email == normalized_email,
        )

        return self.db.scalar(statement)

    def email_exists(
        self,
        organization_id: UUID,
        email: str,
    ) -> bool:
        """Return whether an email exists within an organization."""

        normalized_email = email.strip().lower()

        if not normalized_email:
            return False

        statement = (
            select(User.id)
            .where(
                User.organization_id == organization_id,
                User.email == normalized_email,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def auth_user_exists(
        self,
        auth_user_id: UUID,
    ) -> bool:
        """Return whether a Supabase Auth user is already linked."""

        statement = (
            select(User.id)
            .where(User.auth_user_id == auth_user_id)
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return users belonging to one organization."""

        statement = select(User).where(
            User.organization_id == organization_id
        )

        if active_only:
            statement = statement.where(
                User.is_active.is_(True)
            )

        statement = (
            statement
            .order_by(User.full_name, User.id)
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_active(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return active users in one organization."""

        return self.list_by_organization(
            organization_id,
            active_only=True,
            offset=offset,
            limit=limit,
        )
