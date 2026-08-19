"""Authentication-related request and response schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.db.types import UserRole
from app.schemas.common import ORMModel


class LoginRequest(ORMModel):
    """Email/password login request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(ORMModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())

        if len(cleaned) < 2:
            raise ValueError("Full name must contain at least 2 characters.")

        return cleaned


class AuthTokenResponse(ORMModel):
    """Authentication token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = Field(default=None, ge=0)
    refresh_token: str | None = None


class AuthenticatedUser(ORMModel):
    """Authenticated OmniLead AI user."""

    id: UUID
    auth_user_id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class AuthSessionResponse(ORMModel):
    """Authenticated session payload returned to the frontend."""

    user: AuthenticatedUser
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = Field(default=None, ge=0)


class PasswordResetRequest(ORMModel):
    """Request a Supabase password-reset email."""

    email: EmailStr


class PasswordUpdateRequest(ORMModel):
    """Update the authenticated user's password."""

    password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(ORMModel):
    """Refresh an authentication session."""

    refresh_token: str = Field(min_length=1)
