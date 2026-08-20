"""User request and response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.db.types import UserRole
from app.schemas.common import ORMModel, TimestampedSchema


class UserBase(ORMModel):
    """Shared user fields."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    role: UserRole = UserRole.SALES
    avatar_url: str | None = Field(default=None, max_length=2048)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool = True

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters."
            )

        return cleaned

    @field_validator("avatar_url")
    @classmethod
    def normalize_avatar_url(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None

    @field_validator("phone")
    @classmethod
    def normalize_phone(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class UserCreate(UserBase):
    """Create an application user linked to Supabase Auth."""

    organization_id: UUID
    auth_user_id: UUID


class UserUpdate(ORMModel):
    """Update mutable user profile and access fields."""

    email: EmailStr | None = None
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    role: UserRole | None = None
    avatar_url: str | None = Field(
        default=None,
        max_length=2048,
    )
    phone: str | None = Field(
        default=None,
        max_length=30,
    )
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_optional_full_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters."
            )

        return cleaned

    @field_validator("avatar_url", "phone")
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class UserResponse(UserBase, TimestampedSchema):
    """Full application user returned by the API."""

    id: UUID
    organization_id: UUID
    auth_user_id: UUID
    last_active_at: datetime | None = None


class UserSummary(ORMModel):
    """Compact user representation for assignments and lists."""

    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    avatar_url: str | None = None
    is_active: bool


class UserActivityUpdate(ORMModel):
    """Internal payload for updating user activity state."""

    last_active_at: datetime


class TeamMemberUpdate(ORMModel):
    """Admin-safe team member access update."""

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_team_member_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError(
                "Full name must contain at least 2 characters."
            )

        return cleaned
