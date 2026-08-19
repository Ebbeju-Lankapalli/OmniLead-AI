"""Customer repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select

from app.models.customer import Customer
from app.models.customer_identity import CustomerIdentity
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Data-access operations for unified customers."""

    model = Customer

    def get_by_phone(
        self,
        organization_id: UUID,
        phone: str,
    ) -> Customer | None:
        """Return a customer by primary phone."""

        normalized_phone = phone.strip()

        if not normalized_phone:
            return None

        statement = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.primary_phone == normalized_phone,
        )

        return self.db.scalar(statement)

    def get_by_email(
        self,
        organization_id: UUID,
        email: str,
    ) -> Customer | None:
        """Return a customer by primary email."""

        normalized_email = email.strip().lower()

        if not normalized_email:
            return None

        statement = select(Customer).where(
            Customer.organization_id == organization_id,
            Customer.primary_email == normalized_email,
        )

        return self.db.scalar(statement)

    def get_by_identity(
        self,
        organization_id: UUID,
        identity_type: str,
        normalized_value: str,
    ) -> Customer | None:
        """Resolve a customer through a normalized channel identity."""

        normalized_type = (
            identity_type.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )
        normalized_identity = normalized_value.strip()

        if not normalized_type or not normalized_identity:
            return None

        statement = (
            select(Customer)
            .join(
                CustomerIdentity,
                CustomerIdentity.customer_id == Customer.id,
            )
            .where(
                Customer.organization_id == organization_id,
                CustomerIdentity.organization_id == organization_id,
                CustomerIdentity.identity_type == normalized_type,
                CustomerIdentity.normalized_value == normalized_identity,
            )
        )

        return self.db.scalar(statement)

    def identity_exists(
        self,
        organization_id: UUID,
        identity_type: str,
        normalized_value: str,
    ) -> bool:
        """Return whether a normalized customer identity exists."""

        normalized_type = (
            identity_type.strip()
            .upper()
            .replace("-", "_")
            .replace(" ", "_")
        )
        normalized_identity = normalized_value.strip()

        if not normalized_type or not normalized_identity:
            return False

        statement = (
            select(CustomerIdentity.id)
            .where(
                CustomerIdentity.organization_id == organization_id,
                CustomerIdentity.identity_type == normalized_type,
                CustomerIdentity.normalized_value == normalized_identity,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Customer]:
        """Return customers belonging to one organization."""

        statement = select(Customer).where(
            Customer.organization_id == organization_id
        )

        if not include_archived:
            statement = statement.where(
                Customer.archived_at.is_(None)
            )

        statement = (
            statement
            .order_by(
                Customer.last_seen_at.desc(),
                Customer.id,
            )
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def search(
        self,
        organization_id: UUID,
        query: str,
        *,
        include_archived: bool = False,
        limit: int = 20,
    ) -> Sequence[Customer]:
        """Search customers by name, company, phone, or email."""

        normalized_query = query.strip()

        if not normalized_query:
            return []

        pattern = f"%{normalized_query}%"

        statement = select(Customer).where(
            Customer.organization_id == organization_id,
            or_(
                Customer.full_name.ilike(pattern),
                Customer.company_name.ilike(pattern),
                Customer.primary_phone.ilike(pattern),
                Customer.primary_email.ilike(pattern),
            ),
        )

        if not include_archived:
            statement = statement.where(
                Customer.archived_at.is_(None)
            )

        statement = (
            statement
            .order_by(
                Customer.last_seen_at.desc(),
                Customer.id,
            )
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()
