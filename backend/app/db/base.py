"""Shared SQLAlchemy declarative base and reusable model mixins."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Base class for every SQLAlchemy model in OmniLead AI."""

    metadata = metadata

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Generate a default snake-case table name when a model does not
        explicitly provide one.

        Core application models will still define explicit table names so the
        database contract remains obvious and stable.
        """

        name = cls.__name__

        characters: list[str] = []

        for index, character in enumerate(name):
            if character.isupper() and index > 0:
                characters.append("_")

            characters.append(character.lower())

        return "".join(characters)

    def to_dict(self) -> dict[str, Any]:
        """
        Return mapped column values as a plain dictionary.

        This helper is intended for internal debugging and audit utilities.
        API serialization remains the responsibility of Pydantic schemas.
        """

        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


class UUIDPrimaryKeyMixin:
    """Provide a PostgreSQL UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Provide timezone-aware creation and update timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
