"""Reusable SQLAlchemy repository primitives."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository[ModelT: Base]:
    """
    Generic SQLAlchemy repository.

    Repositories never commit transactions themselves. The service layer owns
    transaction boundaries and decides when to commit or roll back.
    """

    model: type[ModelT]

    def __init__(
        self,
        db: Session,
        model: type[ModelT] | None = None,
    ) -> None:
        self.db = db

        if model is not None:
            self.model = model

        if not hasattr(self, "model"):
            raise TypeError(
                "Repository model is not configured. "
                "Set `model` on the repository class or pass it to __init__()."
            )

    def get(
        self,
        object_id: UUID,
    ) -> ModelT | None:
        """Return one record by primary key."""

        return self.db.get(self.model, object_id)

    def get_or_none(
        self,
        object_id: UUID | None,
    ) -> ModelT | None:
        """Return one record by primary key when an ID is provided."""

        if object_id is None:
            return None

        return self.get(object_id)

    def exists(
        self,
        object_id: UUID,
    ) -> bool:
        """Return whether a record exists for the supplied primary key."""

        statement = (
            select(self.model.id)
            .where(self.model.id == object_id)
            .limit(1)
        )

        return self.db.scalar(statement) is not None

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelT]:
        """Return records ordered by primary key."""

        statement = (
            select(self.model)
            .order_by(self.model.id)
            .offset(max(offset, 0))
            .limit(max(limit, 0))
        )

        return self.db.scalars(statement).all()

    def count(self) -> int:
        """Return the number of records in the repository table."""

        statement = select(func.count()).select_from(self.model)

        return int(self.db.scalar(statement) or 0)

    def add(
        self,
        instance: ModelT,
        *,
        flush: bool = True,
    ) -> ModelT:
        """Add a mapped instance to the current transaction."""

        self.db.add(instance)

        if flush:
            self.db.flush()

        return instance

    def add_all(
        self,
        instances: Sequence[ModelT],
        *,
        flush: bool = True,
    ) -> Sequence[ModelT]:
        """Add multiple mapped instances to the current transaction."""

        if not instances:
            return instances

        self.db.add_all(list(instances))

        if flush:
            self.db.flush()

        return instances

    def create(
        self,
        *,
        flush: bool = True,
        **values: Any,
    ) -> ModelT:
        """Create and add a new mapped instance."""

        instance = self.model(**values)
        return self.add(instance, flush=flush)

    def update(
        self,
        instance: ModelT,
        *,
        flush: bool = True,
        **values: Any,
    ) -> ModelT:
        """Update mapped attributes on an existing instance."""

        mapper = self.model.__mapper__
        writable_attributes = {
            attribute.key
            for attribute in mapper.column_attrs
        }

        for field_name, value in values.items():
            if field_name not in writable_attributes:
                raise AttributeError(
                    f"{self.model.__name__} has no mapped column "
                    f"{field_name!r}."
                )

            setattr(instance, field_name, value)

        if flush:
            self.db.flush()

        return instance

    def delete(
        self,
        instance: ModelT,
        *,
        flush: bool = True,
    ) -> None:
        """Delete a mapped instance from the current transaction."""

        self.db.delete(instance)

        if flush:
            self.db.flush()

    def delete_by_id(
        self,
        object_id: UUID,
        *,
        flush: bool = True,
    ) -> bool:
        """Delete a record by primary key and return whether it existed."""

        instance = self.get(object_id)

        if instance is None:
            return False

        self.delete(instance, flush=flush)
        return True

    def refresh(
        self,
        instance: ModelT,
    ) -> ModelT:
        """Refresh an instance from the database."""

        self.db.refresh(instance)
        return instance

    def flush(self) -> None:
        """Flush pending repository changes without committing."""

        self.db.flush()
