"""Default lead lifecycle status provisioning tests."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from app.models.lead_status import LeadStatus
from app.services.lead_status_service import LeadStatusService


def make_service(existing=None):
    """Create a service backed by an in-memory status collection."""

    stored = list(existing or [])
    db = MagicMock()
    db.add_all.side_effect = lambda statuses: stored.extend(statuses)
    service = LeadStatusService(db)
    service.leads.list_statuses = MagicMock(
        side_effect=lambda organization_id, active_only=False: list(stored)
    )
    return service, db, stored


def test_provisioning_creates_all_default_statuses():
    organization_id = uuid4()
    service, db, stored = make_service()

    service.provision_defaults(organization_id)

    assert [status.key for status in stored] == [
        "NEW",
        "CONTACTED",
        "INTERESTED",
        "QUALIFIED",
        "WON",
        "LOST",
    ]
    assert [status.display_order for status in stored] == list(range(1, 7))
    assert all(status.organization_id == organization_id for status in stored)
    assert stored[4].is_terminal is True
    assert stored[4].is_won is True
    assert stored[5].is_terminal is True
    assert stored[5].is_lost is True
    db.flush.assert_called_once_with()
    db.commit.assert_not_called()


def test_provisioning_is_idempotent():
    organization_id = uuid4()
    service, db, stored = make_service()

    service.provision_defaults(organization_id)
    service.provision_defaults(organization_id)

    assert len(stored) == 6
    db.add_all.assert_called_once()
    db.flush.assert_called_once_with()


def test_provisioning_preserves_existing_status_rows():
    organization_id = uuid4()
    existing_new = LeadStatus(
        organization_id=organization_id,
        key="NEW",
        name="Incoming",
        display_order=10,
        is_terminal=False,
        is_won=False,
        is_lost=False,
        is_active=False,
    )
    service, _, stored = make_service([existing_new])

    service.provision_defaults(organization_id)

    assert len(stored) == 6
    assert stored[0] is existing_new
    assert stored[0].name == "Incoming"
    assert stored[0].display_order == 10
    assert stored[0].is_active is False
    assert sum(status.key == "NEW" for status in stored) == 1
