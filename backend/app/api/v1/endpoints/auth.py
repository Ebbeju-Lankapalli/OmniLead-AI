"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.auth import (
    AuthSessionResponse,
    AuthTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    status_code=201,
)
def register(
    payload: RegisterRequest,
    db: DatabaseSession,
) -> AuthSessionResponse:
    """Register a new organization and its first administrator."""

    return AuthService(db).register(
        payload
    )


@router.post(
    "/login",
    response_model=AuthSessionResponse,
)
def login(
    payload: LoginRequest,
    db: DatabaseSession,
) -> AuthSessionResponse:
    """Authenticate an OmniLead AI user."""

    return AuthService(db).login(
        payload
    )


@router.get(
    "/me",
    response_model=AuthSessionResponse,
)
def get_me(
    current_user: CurrentUser,
    db: DatabaseSession,
) -> AuthSessionResponse:
    """Return the currently authenticated OmniLead AI user."""

    return AuthService(
        db
    ).get_session_for_user(
        current_user
    )


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
)
def refresh_session(
    payload: RefreshTokenRequest,
    db: DatabaseSession,
) -> AuthTokenResponse:
    """Exchange a refresh token for a new Supabase session."""

    return AuthService(db).refresh(
        payload
    )
