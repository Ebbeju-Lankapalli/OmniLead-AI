"""FastAPI authentication and authorization dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
)
from app.db.session import get_db
from app.db.types import UserRole
from app.models.user import User
from app.repositories.users import UserRepository

bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_supabase_auth_client() -> Client:
    """Create a Supabase client used to validate user access tokens."""

    if not settings.SUPABASE_URL:
        raise ConfigurationError(
            "SUPABASE_URL is not configured."
        )

    if not settings.SUPABASE_ANON_KEY:
        raise ConfigurationError(
            "SUPABASE_ANON_KEY is not configured."
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> User:
    """Return the authenticated active OmniLead AI user."""

    if credentials is None:
        raise AuthenticationError(
            "Authentication credentials were not provided."
        )

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            "Bearer authentication is required."
        )

    access_token = credentials.credentials.strip()

    if not access_token:
        raise AuthenticationError(
            "Authentication token cannot be empty."
        )

    auth_client = get_supabase_auth_client()

    try:
        response = auth_client.auth.get_user(
            access_token
        )
    except Exception as exc:
        raise AuthenticationError(
            "Invalid or expired authentication token."
        ) from exc

    auth_user = getattr(
        response,
        "user",
        None,
    )

    if auth_user is None:
        raise AuthenticationError(
            "Unable to resolve authenticated Supabase user."
        )

    auth_user_id = getattr(
        auth_user,
        "id",
        None,
    )

    if auth_user_id is None:
        raise AuthenticationError(
            "Authenticated Supabase user has no ID."
        )

    repository = UserRepository(db)

    try:
        user = repository.get_by_auth_user_id(
            auth_user_id
        )
    except (TypeError, ValueError) as exc:
        raise AuthenticationError(
            "Authenticated Supabase user ID is invalid."
        ) from exc

    if user is None:
        raise AuthenticationError(
            "Authenticated user is not registered in OmniLead AI."
        )

    if not user.is_active:
        raise AuthorizationError(
            "User account is inactive."
        )

    return user


def require_admin(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """Require an authenticated OmniLead AI administrator."""

    if current_user.role != UserRole.ADMIN.value:
        raise AuthorizationError(
            "Administrator access is required."
        )

    return current_user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

AdminUser = Annotated[
    User,
    Depends(require_admin),
]

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]
