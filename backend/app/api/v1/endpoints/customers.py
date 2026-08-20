"""Customer-management API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DatabaseSession
from app.schemas.customer import (
    CustomerCreate,
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def list_customers(
    current_user: CurrentUser,
    db: DatabaseSession,
    include_archived: bool = False,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 100,
) -> list[CustomerResponse]:
    """Return organization-scoped customers."""

    customers = CustomerService(
        db
    ).list_by_organization(
        current_user.organization_id,
        include_archived=include_archived,
        offset=offset,
        limit=limit,
    )

    return [
        CustomerResponse.model_validate(customer)
        for customer in customers
    ]


@router.get(
    "/search",
    response_model=list[CustomerResponse],
)
def search_customers(
    current_user: CurrentUser,
    db: DatabaseSession,
    query: Annotated[
        str,
        Query(min_length=1, max_length=255),
    ],
    include_archived: bool = False,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
) -> list[CustomerResponse]:
    """Search customers by name, company, phone, or email."""

    customers = CustomerService(
        db
    ).search(
        current_user.organization_id,
        query,
        include_archived=include_archived,
        limit=limit,
    )

    return [
        CustomerResponse.model_validate(customer)
        for customer in customers
    ]


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201,
)
def create_customer(
    payload: CustomerCreateRequest,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CustomerResponse:
    """Create a customer in the authenticated organization."""

    customer = CustomerService(
        db
    ).create(
        CustomerCreate(
            organization_id=current_user.organization_id,
            **payload.model_dump(),
        )
    )

    return CustomerResponse.model_validate(
        customer
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CustomerResponse:
    """Return one organization-scoped customer."""

    customer = CustomerService(
        db
    ).get(
        current_user.organization_id,
        customer_id,
    )

    return CustomerResponse.model_validate(
        customer
    )


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CustomerResponse:
    """Update mutable customer fields."""

    customer = CustomerService(
        db
    ).update(
        current_user.organization_id,
        customer_id,
        payload,
    )

    return CustomerResponse.model_validate(
        customer
    )


@router.post(
    "/{customer_id}/archive",
    response_model=CustomerResponse,
)
def archive_customer(
    customer_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CustomerResponse:
    """Archive a customer."""

    customer = CustomerService(
        db
    ).archive(
        current_user.organization_id,
        customer_id,
        archived_at=datetime.now().astimezone(),
    )

    return CustomerResponse.model_validate(
        customer
    )


@router.post(
    "/{customer_id}/restore",
    response_model=CustomerResponse,
)
def restore_customer(
    customer_id: UUID,
    current_user: CurrentUser,
    db: DatabaseSession,
) -> CustomerResponse:
    """Restore an archived customer."""

    customer = CustomerService(
        db
    ).restore(
        current_user.organization_id,
        customer_id,
    )

    return CustomerResponse.model_validate(
        customer
    )
