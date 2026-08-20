"""API authentication and organization-isolation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.services.customer_service import CustomerService
from app.services.lead_service import LeadService

ORG_A_ID = uuid4()
ORG_B_ID = uuid4()

USER_A_ID = uuid4()
USER_B_ID = uuid4()

CUSTOMER_A_ID = uuid4()
CUSTOMER_B_ID = uuid4()

LEAD_A_ID = uuid4()
LEAD_B_ID = uuid4()


def make_user(
    *,
    user_id: UUID,
    organization_id: UUID,
    role: str = "SALES",
):
    """Build a lightweight authenticated-user object."""

    return SimpleNamespace(
        id=user_id,
        organization_id=organization_id,
        full_name="Test User",
        email="test@example.com",
        role=role,
        is_active=True,
    )


@pytest.fixture
def fake_db():
    """Provide a lightweight fake DB dependency."""

    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    yield db

    app.dependency_overrides.clear()


@pytest.fixture
def user_a():
    return make_user(
        user_id=USER_A_ID,
        organization_id=ORG_A_ID,
    )


@pytest.fixture
def user_b():
    return make_user(
        user_id=USER_B_ID,
        organization_id=ORG_B_ID,
    )


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.api
def test_customer_list_uses_authenticated_organization(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    """
    Customer listing must use the authenticated user's organization,
    never a client-controlled organization identifier.
    """

    called = {}

    def fake_list(
        self,
        organization_id,
        *,
        include_archived=False,
        offset=0,
        limit=100,
    ):
        called["organization_id"] = organization_id
        called["include_archived"] = include_archived
        called["offset"] = offset
        called["limit"] = limit

        return []

    monkeypatch.setattr(
        CustomerService,
        "list_by_organization",
        fake_list,
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user_a
    )

    response = client.get(
        "/api/v1/customers"
    )

    assert response.status_code == 200
    assert response.json() == []

    assert called["organization_id"] == ORG_A_ID


@pytest.mark.api
def test_customer_get_is_scoped_to_authenticated_organization(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    """Single-customer access must remain organization scoped."""

    called = {}

    customer = SimpleNamespace(
        id=CUSTOMER_A_ID,
        organization_id=ORG_A_ID,
        full_name="Organization A Customer",
        company_name=None,
        primary_phone=None,
        primary_email=None,
        city=None,
        state=None,
        country=None,
        notes=None,
        tags=[],
        archived_at=None,
        first_seen_at=datetime.now(UTC),
        last_seen_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    def fake_get(
        self,
        organization_id,
        customer_id,
    ):
        called["organization_id"] = organization_id
        called["customer_id"] = customer_id
        return customer

    monkeypatch.setattr(
        CustomerService,
        "get",
        fake_get,
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user_a
    )

    response = client.get(
        f"/api/v1/customers/{CUSTOMER_A_ID}"
    )

    assert response.status_code == 200
    assert called["organization_id"] == ORG_A_ID
    assert called["customer_id"] == CUSTOMER_A_ID


@pytest.mark.api
def test_lead_list_uses_authenticated_organization(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    """Lead listing must be scoped to the authenticated organization."""

    called = {}

    def fake_list(
        self,
        organization_id,
        **kwargs,
    ):
        called["organization_id"] = organization_id
        called["kwargs"] = kwargs
        return []

    monkeypatch.setattr(
        LeadService,
        "list_by_organization",
        fake_list,
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user_a
    )

    response = client.get(
        "/api/v1/leads"
    )

    assert response.status_code == 200
    assert response.json() == []

    assert called["organization_id"] == ORG_A_ID


@pytest.mark.api
def test_priority_queue_uses_authenticated_organization(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    """Priority queue must not allow cross-organization access."""

    called = {}

    def fake_priority(
        self,
        organization_id,
        *,
        minimum_priority_score=0,
        limit=50,
    ):
        called["organization_id"] = organization_id
        called["minimum_priority_score"] = (
            minimum_priority_score
        )
        called["limit"] = limit
        return []

    monkeypatch.setattr(
        LeadService,
        "list_priority_queue",
        fake_priority,
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user_a
    )

    response = client.get(
        "/api/v1/leads/priority-queue"
        "?minimum_priority_score=80"
    )

    assert response.status_code == 200
    assert response.json() == []

    assert called["organization_id"] == ORG_A_ID
    assert called["minimum_priority_score"] == 80


@pytest.mark.api
def test_switching_authenticated_user_switches_org_scope(
    client,
    fake_db,
    user_a,
    user_b,
    monkeypatch,
):
    """
    The same endpoint must automatically switch organization scope
    when authentication context changes.
    """

    organizations = []

    def fake_list(
        self,
        organization_id,
        **kwargs,
    ):
        organizations.append(
            organization_id
        )
        return []

    monkeypatch.setattr(
        LeadService,
        "list_by_organization",
        fake_list,
    )

    app.dependency_overrides[get_current_user] = (
        lambda: user_a
    )

    response_a = client.get(
        "/api/v1/leads"
    )

    assert response_a.status_code == 200

    app.dependency_overrides[get_current_user] = (
        lambda: user_b
    )

    response_b = client.get(
        "/api/v1/leads"
    )

    assert response_b.status_code == 200

    assert organizations == [
        ORG_A_ID,
        ORG_B_ID,
    ]


@pytest.mark.api
def test_unauthenticated_customer_request_is_rejected(
    client,
):
    """
    Protected endpoints must reject requests without authentication
    when no authentication dependency override is active.
    """

    app.dependency_overrides.clear()

    response = client.get(
        "/api/v1/customers"
    )

    assert response.status_code == 401

    body = response.json()

    assert (
        body["error"]["code"]
        == "AUTHENTICATION_ERROR"
    )


@pytest.mark.api
def test_unauthenticated_lead_request_is_rejected(
    client,
):
    """Lead endpoints must require authentication."""

    app.dependency_overrides.clear()

    response = client.get(
        "/api/v1/leads"
    )

    assert response.status_code == 401

    body = response.json()

    assert (
        body["error"]["code"]
        == "AUTHENTICATION_ERROR"
    )
