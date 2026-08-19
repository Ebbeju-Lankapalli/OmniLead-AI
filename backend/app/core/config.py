"""Typed application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    API_V1_PREFIX,
    APP_NAME,
    DEFAULT_CURRENCY,
    DEFAULT_MAX_UPLOAD_SIZE_MB,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
    DEFAULT_TIMEZONE,
    SUPPORTED_AUDIO_EXTENSIONS,
)


class Settings(BaseSettings):
    """Centralized and validated OmniLead AI backend configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    APP_NAME: str = APP_NAME
    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_DEBUG: bool = True

    API_V1_PREFIX: str = API_V1_PREFIX

    FRONTEND_URL: str = "http://localhost:5173"

    APP_TIMEZONE: str = DEFAULT_TIMEZONE
    DEFAULT_CURRENCY: str = DEFAULT_CURRENCY

    DEMO_MODE: bool = True

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------

    DATABASE_URL: str = ""

    DB_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=60)

    # ------------------------------------------------------------------
    # Supabase
    # ------------------------------------------------------------------

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    SUPABASE_CALL_RECORDINGS_BUCKET: str = "call-recordings"

    # ------------------------------------------------------------------
    # Gemini / AI
    # ------------------------------------------------------------------

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = ""

    AI_ENABLED: bool = True
    AI_REQUEST_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=300)

    # ------------------------------------------------------------------
    # LangSmith
    # ------------------------------------------------------------------

    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "omnilead-ai"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    EMBEDDING_PROVIDER: Literal["sentence_transformers", "gemini"] = (
        "sentence_transformers"
    )
    SENTENCE_TRANSFORMER_MODEL: str = ""

    SEMANTIC_SEARCH_ENABLED: bool = False

    # ------------------------------------------------------------------
    # Redis / Celery
    # ------------------------------------------------------------------

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CELERY_TASK_ALWAYS_EAGER: bool = False

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    RESEND_API_KEY: str = ""

    EMAIL_FROM_ADDRESS: str = ""
    EMAIL_FROM_NAME: str = APP_NAME

    EMAIL_NOTIFICATIONS_ENABLED: bool = False

    # ------------------------------------------------------------------
    # Meta / Instagram / WhatsApp
    # ------------------------------------------------------------------

    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = ""

    META_GRAPH_API_VERSION: str = ""

    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""

    META_WEBHOOK_ENABLED: bool = False

    # ------------------------------------------------------------------
    # Call intelligence
    # ------------------------------------------------------------------

    CALL_INTELLIGENCE_ENABLED: bool = False

    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    MAX_AUDIO_FILE_SIZE_MB: int = Field(
        default=DEFAULT_MAX_UPLOAD_SIZE_MB,
        ge=1,
        le=100,
    )

    ALLOWED_AUDIO_EXTENSIONS: tuple[str, ...] = tuple(SUPPORTED_AUDIO_EXTENSIONS)

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    CORS_ALLOWED_ORIGINS: tuple[str, ...] = ("http://localhost:5173",)

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = Field(
        default=DEFAULT_RATE_LIMIT_REQUESTS,
        ge=1,
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        ge=1,
    )

    WEBHOOK_SIGNATURE_VALIDATION: bool = True

    MAX_UPLOAD_SIZE_MB: int = Field(
        default=DEFAULT_MAX_UPLOAD_SIZE_MB,
        ge=1,
        le=100,
    )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # ------------------------------------------------------------------
    # WebSockets
    # ------------------------------------------------------------------

    WEBSOCKET_ENABLED: bool = True

    # ------------------------------------------------------------------
    # Demo
    # ------------------------------------------------------------------

    DEMO_ORGANIZATION_NAME: str = "OmniLead Demo Company"
    DEMO_ORGANIZATION_SLUG: str = "omnilead-demo"
    DEMO_ADMIN_EMAIL: str = "demo@omnilead.local"

    DEMO_SEED_ENABLED: bool = True

    # ------------------------------------------------------------------
    # Parsing / normalization
    # ------------------------------------------------------------------

    @field_validator(
        "CORS_ALLOWED_ORIGINS",
        "ALLOWED_AUDIO_EXTENSIONS",
        mode="before",
    )
    @classmethod
    def parse_csv_tuple(
        cls,
        value: object,
    ) -> object:
        """Convert comma-separated environment values into normalized tuples."""

        if not isinstance(value, str):
            return value

        items = tuple(
            item.strip()
            for item in value.split(",")
            if item.strip()
        )

        return items

    @field_validator("ALLOWED_AUDIO_EXTENSIONS")
    @classmethod
    def normalize_audio_extensions(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Normalize configured audio file extensions."""

        return tuple(
            sorted(
                {
                    extension.lower().lstrip(".")
                    for extension in value
                }
            )
        )

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    # ------------------------------------------------------------------
    # Startup validation
    # ------------------------------------------------------------------

    def validate_runtime_configuration(self) -> None:
        """
        Validate configuration that becomes mandatory only when a feature
        or production environment is enabled.

        Optional external services remain optional during local development,
        allowing the CRM to operate even when AI or channel integrations
        are unavailable.
        """

        missing: list[str] = []

        if self.is_production:
            required_production_values = {
                "DATABASE_URL": self.DATABASE_URL,
                "SUPABASE_URL": self.SUPABASE_URL,
                "SUPABASE_ANON_KEY": self.SUPABASE_ANON_KEY,
                "SUPABASE_SERVICE_ROLE_KEY": self.SUPABASE_SERVICE_ROLE_KEY,
            }

            missing.extend(
                name
                for name, value in required_production_values.items()
                if not value
            )

        if self.AI_ENABLED and self.is_production:
            if not self.GEMINI_API_KEY:
                missing.append("GEMINI_API_KEY")

            if not self.GEMINI_MODEL:
                missing.append("GEMINI_MODEL")

        if self.EMAIL_NOTIFICATIONS_ENABLED:
            if not self.RESEND_API_KEY:
                missing.append("RESEND_API_KEY")

            if not self.EMAIL_FROM_ADDRESS:
                missing.append("EMAIL_FROM_ADDRESS")

        if self.META_WEBHOOK_ENABLED:
            meta_required_values = {
                "META_APP_SECRET": self.META_APP_SECRET,
                "META_VERIFY_TOKEN": self.META_VERIFY_TOKEN,
            }

            missing.extend(
                name
                for name, value in meta_required_values.items()
                if not value
            )

        if missing:
            unique_missing = sorted(set(missing))

            raise RuntimeError(
                "Missing required OmniLead AI configuration: "
                + ", ".join(unique_missing)
            )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance for application-wide dependency use."""

    return Settings()


settings = get_settings()