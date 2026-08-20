"""Product catalog business logic."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.products import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Business operations for organization products."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)

    def get(
        self,
        organization_id: UUID,
        product_id: UUID,
    ) -> Product:
        """Return an organization-scoped product."""

        product = self.products.get(product_id)

        if (
            product is None
            or product.organization_id != organization_id
        ):
            raise NotFoundError(
                "Product not found.",
                details={
                    "product_id": str(product_id),
                },
            )

        return product

    def list_by_organization(
        self,
        organization_id: UUID,
        *,
        active_only: bool = False,
        category: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """Return products for an organization."""

        return self.products.list_by_organization(
            organization_id,
            active_only=active_only,
            category=category,
            offset=offset,
            limit=limit,
        )

    def search(
        self,
        organization_id: UUID,
        query: str,
        *,
        active_only: bool = True,
        limit: int = 20,
    ) -> Sequence[Product]:
        """Search products by name."""

        return self.products.search_by_name(
            organization_id,
            query,
            active_only=active_only,
            limit=limit,
        )

    def create(
        self,
        payload: ProductCreate,
    ) -> Product:
        """Create an organization product."""

        if (
            payload.code is not None
            and self.products.code_exists(
                payload.organization_id,
                payload.code,
            )
        ):
            raise ConflictError(
                "Product code already exists.",
                details={
                    "code": payload.code,
                },
            )

        product = Product(
            **payload.model_dump()
        )

        try:
            self.products.add(product)
            self.db.commit()
            self.db.refresh(product)

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Product code already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return product

    def update(
        self,
        organization_id: UUID,
        product_id: UUID,
        payload: ProductUpdate,
    ) -> Product:
        """Update product catalog fields."""

        product = self.get(
            organization_id,
            product_id,
        )

        values = payload.model_dump(
            exclude_unset=True,
        )

        if not values:
            return product

        if "code" in values:
            code = values["code"]

            if code is not None:
                existing = self.products.get_by_code(
                    organization_id,
                    code,
                )

                if (
                    existing is not None
                    and existing.id != product.id
                ):
                    raise ConflictError(
                        "Product code already exists.",
                        details={
                            "code": code,
                        },
                    )

        try:
            self.products.update(
                product,
                **values,
            )
            self.db.commit()
            self.db.refresh(product)

        except IntegrityError as exc:
            self.db.rollback()

            raise ConflictError(
                "Product code already exists."
            ) from exc

        except Exception:
            self.db.rollback()
            raise

        return product

    def activate(
        self,
        organization_id: UUID,
        product_id: UUID,
    ) -> Product:
        """Activate a product."""

        product = self.get(
            organization_id,
            product_id,
        )

        if product.is_active:
            return product

        return self.update(
            organization_id,
            product_id,
            ProductUpdate(
                is_active=True,
            ),
        )

    def deactivate(
        self,
        organization_id: UUID,
        product_id: UUID,
    ) -> Product:
        """Deactivate a product without deleting historical references."""

        product = self.get(
            organization_id,
            product_id,
        )

        if not product.is_active:
            return product

        return self.update(
            organization_id,
            product_id,
            ProductUpdate(
                is_active=False,
            ),
        )
