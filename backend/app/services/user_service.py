"""Team-member business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AuthorizationError,
    NotFoundError,
)
from app.db.types import UserRole
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import TeamMemberUpdate


class UserService:
    """Business operations for organization team members."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def get(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> User:
        """Return an organization-scoped team member."""

        user = self.users.get(user_id)

        if (
            user is None
            or user.organization_id != organization_id
        ):
            raise NotFoundError(
                "Team member not found.",
                details={
                    "user_id": str(user_id),
                },
            )

        return user

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Return organization team members."""

        return self.users.list_by_organization(
            organization_id,
            active_only=active_only,
            offset=offset,
            limit=limit,
        )

    def update_team_member(
        self,
        organization_id: UUID,
        user_id: UUID,
        payload: TeamMemberUpdate,
        *,
        acting_user_id: UUID,
    ) -> User:
        """Update role/access fields with admin lockout protection."""

        user = self.get(
            organization_id,
            user_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return user

        if user.id == acting_user_id:
            if (
                values.get("is_active") is False
            ):
                raise AuthorizationError(
                    "You cannot deactivate your own account."
                )

            role = values.get("role")

            if (
                role is not None
                and role != UserRole.ADMIN
            ):
                raise AuthorizationError(
                    "You cannot remove your own admin role."
                )

        try:
            self.users.update(
                user,
                **values,
            )
            self.db.commit()
            self.db.refresh(user)

        except Exception:
            self.db.rollback()
            raise

        return user
