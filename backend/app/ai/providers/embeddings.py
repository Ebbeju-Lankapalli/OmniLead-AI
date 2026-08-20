"""Local sentence-transformer embedding provider."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.models.interaction import EMBEDDING_DIMENSION

DEFAULT_SENTENCE_TRANSFORMER_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


class SentenceTransformerEmbeddingProvider:
    """Generate normalized local embeddings for semantic retrieval."""

    provider_name = "sentence_transformers"

    def __init__(
        self,
        *,
        model_name: str | None = None,
    ) -> None:
        resolved_model = (
            model_name
            if model_name is not None
            else settings.SENTENCE_TRANSFORMER_MODEL
        ).strip()

        self.model_name = (
            resolved_model
            or DEFAULT_SENTENCE_TRANSFORMER_MODEL
        )

        self.model = self._load_model(
            self.model_name
        )

        dimension = (
            self.model.get_embedding_dimension()
        )

        if dimension != EMBEDDING_DIMENSION:
            raise ConfigurationError(
                "Sentence-transformer embedding dimension "
                "does not match the database vector dimension.",
                details={
                    "model": self.model_name,
                    "model_dimension": dimension,
                    "database_dimension": (
                        EMBEDDING_DIMENSION
                    ),
                },
            )

    @staticmethod
    @lru_cache(maxsize=2)
    def _load_model(
        model_name: str,
    ) -> SentenceTransformer:
        """Load and cache a sentence-transformer model."""

        return SentenceTransformer(
            model_name
        )

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        """Generate one normalized embedding."""

        cleaned = text.strip()

        if not cleaned:
            raise ValueError(
                "Embedding text cannot be empty."
            )

        embedding = self.model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        vector = [
            float(value)
            for value in embedding.tolist()
        ]

        if len(vector) != EMBEDDING_DIMENSION:
            raise RuntimeError(
                "Generated embedding has unexpected "
                "dimension."
            )

        return vector

    def embed_texts(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Generate normalized embeddings for multiple texts."""

        cleaned = [
            text.strip()
            for text in texts
            if text.strip()
        ]

        if not cleaned:
            return []

        embeddings = self.model.encode(
            cleaned,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        vectors = [
            [
                float(value)
                for value in row.tolist()
            ]
            for row in embeddings
        ]

        for vector in vectors:
            if len(vector) != EMBEDDING_DIMENSION:
                raise RuntimeError(
                    "Generated embedding has unexpected "
                    "dimension."
                )

        return vectors
