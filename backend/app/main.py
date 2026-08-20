"""OmniLead AI FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import OmniLeadError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.db.session import close_database, get_session_factory

configure_logging()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage application startup and shutdown lifecycle."""

    settings.validate_runtime_configuration()

    logger.info(
        "application_starting",
        environment=settings.APP_ENV,
        debug=settings.APP_DEBUG,
    )

    try:
        yield
    finally:
        close_database()

        logger.info(
            "application_stopped",
        )


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.APP_DEBUG,
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    SecurityHeadersMiddleware,
)

app.add_middleware(
    RateLimitMiddleware,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(settings.TRUSTED_HOSTS),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OmniLeadError)
async def handle_omnilead_error(
    _request,
    exc: OmniLeadError,
) -> JSONResponse:
    """Convert expected application errors into consistent API responses."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


@app.get(
    "/health",
    tags=["health"],
)
def health_check() -> dict[str, str]:
    """Return lightweight application liveness status."""

    return {
        "status": "ok",
        "service": settings.APP_NAME,
    }


@app.get(
    "/ready",
    tags=["health"],
)
def readiness_check() -> dict[str, str]:
    """Return readiness status after verifying database connectivity."""

    session_factory = get_session_factory()
    db = session_factory()

    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "service": settings.APP_NAME,
            "database": "ok",
        }

    finally:
        db.close()


app.include_router(
    api_router,
)
