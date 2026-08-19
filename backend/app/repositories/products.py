"""Product repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Data-access operations for organization products."""

    model = Product

    def get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> Product | None:
        """Return a product by organization and unique code."""

        normalized_code = code.strip()

        if not normalized_code:
            return None

        statement = select(Product).where(
            Product.organization_id == organization_id,
            Product.code == normalized_code,
        )

        return self.db.scalar(statement)

    def code_exists(
        self,
        organization_id: UUID,
        code: str,
    ) -> bool:
        """Return whether a product code already exists."""

        normalized_code = code.strip()

        if not normalized_code:
            return False

        statement = (
            select(Product.id)
            .where(
                Product.organization_id == organization_id,
                Product.code == normalized_code,
            )
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active_only: bool = False,
        category: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """Return products belonging to an organization."""

        statement = select(Product).where(
            Product.organization_id == organization_id
        )

        if active_only:
            statement = statement.where(
                Product.is_active.is_(True)
            )

        if category is not None:
            normalized_category = category.strip()

            if normalized_category:
                statement = statement.where(
                    Product.category == normalized_category
                )

        statement = (
            statement
            .order_by(Product.name, Product.id)
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def list_active(
        self,
        organization_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """Return active products for one organization."""

        return self.list_by_organization(
            organization_id,
            active_only=True,
            offset=offset,
            limit=limit,
        )

    def search_by_name(
        self,
        organization_id: UUID,
        query: str,
        *,
        active_only: bool = True,
        limit: int = 20,
    ) -> Sequence[Product]:
        """Search products by case-insensitive name match."""

        normalized_query = query.strip()

        if not normalized_query:
            return []

        statement = select(Product).where(
            Product.organization_id == organization_id,
            Product.name.ilike(f"%{normalized_query}%"),
        )

        if active_only:
            statement = statement.where(
                Product.is_active.is_(True)
            )

        statement = (
            statement
            .order_by(Product.name, Product.id)
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()
