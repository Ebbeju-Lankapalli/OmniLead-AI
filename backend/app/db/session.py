"""SQLAlchemy engine and session lifecycle management."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.exceptions import ConfigurationError


def _database_url() -> str:
    """Return the configured database URL or raise a clear configuration error."""

    database_url = settings.DATABASE_URL.strip()

    if not database_url:
        raise ConfigurationError(
            "DATABASE_URL is not configured.",
            details={
                "hint": (
                    "Create backend/.env from backend/.env.example and provide "
                    "the PostgreSQL connection string before using database features."
                )
            },
        )

    return database_url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy engine.

    The engine is created lazily so importing OmniLead AI does not require a
    live database connection.
    """

    return create_engine(
        _database_url(),
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Return the application-wide SQLAlchemy session factory."""

    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides one SQLAlchemy session per request.

    Transactions are committed explicitly by the service layer rather than
    automatically at the dependency boundary.
    """

    session_factory = get_session_factory()
    db = session_factory()

    try:
        yield db
    finally:
        db.close()


def close_database() -> None:
    """
    Dispose of pooled database connections.

    Called during application shutdown and useful in tests.
    """

    if get_engine.cache_info().currsize:
        engine = get_engine()
        engine.dispose()

    get_session_factory.cache_clear()
    get_engine.cache_clear()
