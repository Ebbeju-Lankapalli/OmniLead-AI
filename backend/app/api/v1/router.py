"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analytics,
    auth,
    calls,
    conversations,
    customers,
    dashboard,
    enquiries,
    followups,
    interactions,
    leads,
    notifications,
    organizations,
    products,
    search,
    users,
    webhooks,
)

router = APIRouter()

router.include_router(
    auth.router,
)

router.include_router(
    customers.router,
)

router.include_router(
    enquiries.router,
)

router.include_router(
    leads.router,
)

router.include_router(
    conversations.router,
)

router.include_router(
    interactions.router,
)

router.include_router(
    followups.router,
)

router.include_router(
    notifications.router,
)

router.include_router(
    dashboard.router,
)

router.include_router(
    analytics.router,
)

router.include_router(
    ai.router,
)

router.include_router(
    organizations.router,
)

router.include_router(
    products.router,
)

router.include_router(
    search.router,
)

router.include_router(
    users.router,
)

router.include_router(
    webhooks.router,
)

router.include_router(
    calls.router,
)
