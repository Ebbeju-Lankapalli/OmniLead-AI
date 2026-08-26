"""Lead lifecycle status provisioning and retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.lead_status import LeadStatus
from app.repositories.leads import LeadRepository

DEFAULT_LEAD_STATUSES: Final = (
    ("NEW", "New", 1, False, False, False),
    ("CONTACTED", "Contacted", 2, False, False, False),
    ("INTERESTED", "Interested", 3, False, False, False),
    ("QUALIFIED", "Qualified", 4, False, False, False),
    ("WON", "Won", 5, True, True, False),
    ("LOST", "Lost", 6, True, False, True),
)


class LeadStatusService:
    """Manage organization-scoped lead lifecycle statuses."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.leads = LeadRepository(db)

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active_only: bool = True,
    ) -> Sequence[LeadStatus]:
        """Return statuses belonging to one organization."""

        return self.leads.list_statuses(
            organization_id,
            active_only=active_only,
        )

    def provision_defaults(
        self,
        organization_id: UUID,
    ) -> Sequence[LeadStatus]:
        """Add missing defaults without committing the current transaction."""

        existing = list(
            self.leads.list_statuses(
                organization_id,
                active_only=False,
            )
        )
        existing_keys = {status.key for status in existing}

        missing = [
            LeadStatus(
                organization_id=organization_id,
                key=key,
                name=name,
                display_order=display_order,
                is_terminal=is_terminal,
                is_won=is_won,
                is_lost=is_lost,
                is_active=True,
            )
            for (
                key,
                name,
                display_order,
                is_terminal,
                is_won,
                is_lost,
            ) in DEFAULT_LEAD_STATUSES
            if key not in existing_keys
        ]

        if missing:
            self.db.add_all(missing)
            self.db.flush()

        return [*existing, *missing]
