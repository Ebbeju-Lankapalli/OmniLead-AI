"""Lead lifecycle status API tests."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.services.lead_status_service import LeadStatusService


@pytest.fixture
def fake_db():
    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_a():
    return SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        full_name="Test User",
        email="test@example.com",
        role="SALES",
        is_active=True,
    )


def make_status(organization_id, key, name, display_order):
    """Build a status object compatible with the response schema."""

    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid4(),
        organization_id=organization_id,
        key=key,
        name=name,
        description=None,
        display_order=display_order,
        is_terminal=False,
        is_won=False,
        is_lost=False,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.api
def test_statuses_are_scoped_to_authenticated_organization(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    called = {}
    status = make_status(user_a.organization_id, "NEW", "New", 1)

    def fake_list(self, organization_id, *, active_only=True):
        called["organization_id"] = organization_id
        called["active_only"] = active_only
        return [status]

    monkeypatch.setattr(
        LeadStatusService,
        "list_by_organization",
        fake_list,
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get("/api/v1/leads/statuses")

    assert response.status_code == 200
    assert called == {
        "organization_id": user_a.organization_id,
        "active_only": True,
    }
    assert response.json()[0]["organization_id"] == str(
        user_a.organization_id
    )


@pytest.mark.api
def test_statuses_require_authentication(client, fake_db):
    response = client.get("/api/v1/leads/statuses")

    assert response.status_code == 401


@pytest.mark.api
def test_statuses_endpoint_preserves_lifecycle_order(
    client,
    fake_db,
    user_a,
    monkeypatch,
):
    statuses = [
        make_status(user_a.organization_id, "NEW", "New", 1),
        make_status(
            user_a.organization_id,
            "CONTACTED",
            "Contacted",
            2,
        ),
        make_status(
            user_a.organization_id,
            "QUALIFIED",
            "Qualified",
            4,
        ),
    ]
    monkeypatch.setattr(
        LeadStatusService,
        "list_by_organization",
        lambda self, organization_id, active_only=True: statuses,
    )
    app.dependency_overrides[get_current_user] = lambda: user_a

    response = client.get("/api/v1/leads/statuses")

    assert response.status_code == 200
    assert [item["key"] for item in response.json()] == [
        "NEW",
        "CONTACTED",
        "QUALIFIED",
    ]
