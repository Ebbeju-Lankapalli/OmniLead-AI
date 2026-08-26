"""Supabase-backed authentication business logic."""

from __future__ import annotations

from contextlib import suppress
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConflictError,
)
from app.db.types import UserRole
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository
from app.schemas.auth import (
    AuthenticatedUser,
    AuthSessionResponse,
    AuthTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.services.lead_status_service import LeadStatusService


class AuthService:
    """Authentication operations backed by Supabase Auth."""

    def __init__(
        self,
        db: Session,
        *,
        public_client: Client | None = None,
        admin_client: Client | None = None,
    ) -> None:
        self.db = db

        if not settings.SUPABASE_URL:
            raise ConfigurationError(
                "SUPABASE_URL is not configured."
            )

        if not settings.SUPABASE_ANON_KEY:
            raise ConfigurationError(
                "SUPABASE_ANON_KEY is not configured."
            )

        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured."
            )

        self.public_client = (
            public_client
            or create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
            )
        )

        self.admin_client = (
            admin_client
            or create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        )

        self.users = UserRepository(db)
        self.organizations = OrganizationRepository(db)

    def register(
        self,
        payload: RegisterRequest,
    ) -> AuthSessionResponse:
        """Create a Supabase identity, organization, and admin user."""

        email = str(payload.email).strip().lower()
        slug = payload.organization_slug

        if self.organizations.slug_exists(slug):
            raise ConflictError(
                "Organization slug is already in use.",
                details={
                    "slug": slug,
                },
            )

        auth_user_id: UUID | None = None

        try:
            created = self.admin_client.auth.admin.create_user(
                {
                    "email": email,
                    "password": payload.password,
                    "email_confirm": True,
                }
            )

            auth_user = getattr(
                created,
                "user",
                None,
            )

            if auth_user is None:
                raise AuthenticationError(
                    "Supabase user registration failed."
                )

            auth_user_id = UUID(
                str(auth_user.id)
            )

            organization = Organization(
                name=payload.organization_name,
                slug=slug,
                timezone=settings.APP_TIMEZONE,
                default_currency=settings.DEFAULT_CURRENCY,
                demo_mode=settings.DEMO_MODE,
                is_active=True,
                settings={},
            )

            self.db.add(organization)
            self.db.flush()

            LeadStatusService(self.db).provision_defaults(
                organization.id
            )

            user = User(
                organization_id=organization.id,
                auth_user_id=auth_user_id,
                email=email,
                full_name=payload.full_name,
                role=UserRole.ADMIN.value,
                is_active=True,
            )

            self.db.add(user)
            self.db.commit()

            self.db.refresh(organization)
            self.db.refresh(user)

        except IntegrityError as exc:
            self.db.rollback()

            if auth_user_id is not None:
                with suppress(Exception):
                    self.admin_client.auth.admin.delete_user(
                        str(auth_user_id)
                    )

            raise ConflictError(
                "Registration conflicts with an existing account "
                "or organization."
            ) from exc

        except Exception:
            self.db.rollback()

            if auth_user_id is not None:
                with suppress(Exception):
                    self.admin_client.auth.admin.delete_user(
                        str(auth_user_id)
                    )

            raise

        return self._login_credentials(
            email=email,
            password=payload.password,
        )

    def login(
        self,
        payload: LoginRequest,
    ) -> AuthSessionResponse:
        """Authenticate an OmniLead AI user."""

        return self._login_credentials(
            email=str(payload.email).strip().lower(),
            password=payload.password,
        )

    def refresh(
        self,
        payload: RefreshTokenRequest,
    ) -> AuthTokenResponse:
        """Exchange a refresh token for a new Supabase session."""

        try:
            response = self.public_client.auth.refresh_session(
                payload.refresh_token
            )
        except Exception as exc:
            raise AuthenticationError(
                "Invalid or expired refresh token."
            ) from exc

        session = getattr(
            response,
            "session",
            None,
        )

        if session is None:
            raise AuthenticationError(
                "Unable to refresh authentication session."
            )

        return self._token_response(
            session
        )

    def get_session_for_user(
        self,
        user: User,
    ) -> AuthSessionResponse:
        """Return the authenticated application user without issuing tokens."""

        return AuthSessionResponse(
            user=self._authenticated_user(
                user
            ),
        )

    def _login_credentials(
        self,
        *,
        email: str,
        password: str,
    ) -> AuthSessionResponse:
        """Authenticate credentials and resolve the application user."""

        try:
            response = self.public_client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
        except Exception as exc:
            raise AuthenticationError(
                "Invalid email or password."
            ) from exc

        session = getattr(
            response,
            "session",
            None,
        )

        auth_user = getattr(
            response,
            "user",
            None,
        )

        if session is None or auth_user is None:
            raise AuthenticationError(
                "Supabase authentication did not return a session."
            )

        auth_user_id = UUID(
            str(auth_user.id)
        )

        user = self.users.get_by_auth_user_id(
            auth_user_id
        )

        if user is None:
            raise AuthenticationError(
                "Authenticated user is not registered in OmniLead AI."
            )

        if not user.is_active:
            raise AuthenticationError(
                "User account is inactive."
            )

        token = self._token_response(
            session
        )

        return AuthSessionResponse(
            user=self._authenticated_user(
                user
            ),
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            token_type=token.token_type,
            expires_in=token.expires_in,
        )

    @staticmethod
    def _authenticated_user(
        user: User,
    ) -> AuthenticatedUser:
        """Convert a database user to the authenticated-user schema."""

        return AuthenticatedUser(
            id=user.id,
            auth_user_id=user.auth_user_id,
            organization_id=user.organization_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )

    @staticmethod
    def _token_response(
        session,
    ) -> AuthTokenResponse:
        """Convert a Supabase session into the API token schema."""

        access_token = getattr(
            session,
            "access_token",
            None,
        )

        if not access_token:
            raise AuthenticationError(
                "Authentication session contains no access token."
            )

        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=getattr(
                session,
                "expires_in",
                None,
            ),
            refresh_token=getattr(
                session,
                "refresh_token",
                None,
            ),
        )
