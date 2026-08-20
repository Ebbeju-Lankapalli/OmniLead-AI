"""Application security and request-protection middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach conservative security headers to API responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        response = await call_next(request)

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff",
        )
        response.headers.setdefault(
            "X-Frame-Options",
            "DENY",
        )
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Cross-Origin-Opener-Policy",
            "same-origin",
        )

        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Apply a lightweight per-client fixed-window-style rate limit.

    Redis-backed distributed limiting can replace this implementation later
    without changing endpoint contracts.
    """

    def __init__(self, app) -> None:
        super().__init__(app)

        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        if request.url.path in {
            "/health",
            "/ready",
        }:
            return await call_next(request)

        client_host = (
            request.client.host
            if request.client is not None
            else "unknown"
        )

        now = time.monotonic()

        window = float(
            settings.RATE_LIMIT_WINDOW_SECONDS
        )

        limit = int(
            settings.RATE_LIMIT_REQUESTS
        )

        bucket = self.requests[client_host]

        cutoff = now - window

        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": (
                            "Too many requests. "
                            "Please try again later."
                        ),
                        "details": {
                            "limit": limit,
                            "window_seconds": (
                                settings.RATE_LIMIT_WINDOW_SECONDS
                            ),
                        },
                    }
                },
                headers={
                    "Retry-After": str(
                        settings.RATE_LIMIT_WINDOW_SECONDS
                    ),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        bucket.append(now)

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(
            limit
        )
        response.headers["X-RateLimit-Remaining"] = str(
            max(limit - len(bucket), 0)
        )

        return response
