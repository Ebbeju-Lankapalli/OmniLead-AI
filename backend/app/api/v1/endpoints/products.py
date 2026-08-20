"""Product catalog API endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import AdminUser, CurrentUser, DatabaseSession
from app.schemas.product import (
    ProductCreate,
    ProductCreateRequest,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreateRequest,
    current_user: AdminUser,
    db: DatabaseSession,
) -> ProductResponse:
    """Create a product as an organization admin."""

    product = ProductService(
        db
    ).create(
        ProductCreate(
            organization_id=current_user.organization_id,
            **payload.model_dump(),
        )
    )

    return ProductResponse.model_validate(
        product
    )


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    current_user: CurrentUser,
    db: DatabaseSession,
    active_only: bool = False,
    category: str | None = None,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[ProductResponse]:
    """Return products in the authenticated organization."""

    products = ProductService(
        db
    ).list_by_organization(
        current_user.organization_id,
        active_only=active_only,
        category=category,
        offset=offset,
        limit=limit,
    )

    return [
        ProductResponse.model_validate(product)
        for product in products
    ]


@router.get(
    "/search",
    response_model=list[ProductResponse],
)
def search_products(
    current_user: CurrentUser,
    db: DatabaseSession,
    q: Annotated[
        str,
        Query(min_length=1),
    ],
    active_only: bool = True,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
) -> list[ProductResponse]:
    """Search products by name."""

    products = ProductService(
        db
    ).search(
        current_user.organization_id,
        q,
        active_only=active_only,
        limit=limit,
    )

    return [
        ProductResponse.model_validate(product)
        for product in products
    ]


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
def get_product(
    product_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> ProductResponse:
    """Return one organization-scoped product."""

    product = ProductService(
        db
    ).get(
        current_user.organization_id,
        product_id,
    )

    return ProductResponse.model_validate(
        product
    )


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    current_user: AdminUser,
    db: DatabaseSession,
) -> ProductResponse:
    """Update a product as an admin."""

    product = ProductService(
        db
    ).update(
        current_user.organization_id,
        product_id,
        payload,
    )

    return ProductResponse.model_validate(
        product
    )


@router.post(
    "/{product_id}/activate",
    response_model=ProductResponse,
)
def activate_product(
    product_id: UUID,
    current_user: AdminUser,
    db: DatabaseSession,
) -> ProductResponse:
    """Activate a product."""

    product = ProductService(
        db
    ).activate(
        current_user.organization_id,
        product_id,
    )

    return ProductResponse.model_validate(
        product
    )


@router.post(
    "/{product_id}/deactivate",
    response_model=ProductResponse,
)
def deactivate_product(
    product_id: UUID,
    current_user: AdminUser,
    db: DatabaseSession,
) -> ProductResponse:
    """Deactivate a product."""

    product = ProductService(
        db
    ).deactivate(
        current_user.organization_id,
        product_id,
    )

    return ProductResponse.model_validate(
        product
    )
