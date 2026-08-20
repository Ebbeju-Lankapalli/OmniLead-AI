"""Supabase Storage integration for OmniLead AI."""

from __future__ import annotations

from pathlib import Path

from supabase import Client, create_client

from app.core.config import settings
from app.core.exceptions import ConfigurationError


class SupabaseStorageService:
    """Upload, download, and delete files in Supabase Storage."""

    def __init__(
        self,
        *,
        bucket: str | None = None,
        client: Client | None = None,
    ) -> None:
        if not settings.SUPABASE_URL:
            raise ConfigurationError(
                "SUPABASE_URL is not configured."
            )

        if not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise ConfigurationError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured."
            )

        self.bucket = (
            bucket
            or settings.SUPABASE_CALL_RECORDINGS_BUCKET
        ).strip()

        if not self.bucket:
            raise ConfigurationError(
                "Supabase storage bucket is not configured."
            )

        self.client = (
            client
            or create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        )

    def upload_file(
        self,
        local_path: str | Path,
        storage_path: str,
        *,
        content_type: str | None = None,
        upsert: bool = False,
    ) -> str:
        """Upload a local file and return its storage path."""

        path = Path(local_path).expanduser().resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"Local file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Local path is not a file: {path}"
            )

        normalized_storage_path = storage_path.strip().lstrip("/")

        if not normalized_storage_path:
            raise ValueError(
                "Storage path cannot be empty."
            )

        options = {
            "upsert": "true" if upsert else "false",
        }

        if content_type:
            options["content-type"] = content_type

        with path.open("rb") as file_handle:
            self.client.storage.from_(
                self.bucket
            ).upload(
                path=normalized_storage_path,
                file=file_handle,
                file_options=options,
            )

        return normalized_storage_path

    def download_bytes(
        self,
        storage_path: str,
    ) -> bytes:
        """Download an object and return its raw bytes."""

        normalized_storage_path = storage_path.strip().lstrip("/")

        if not normalized_storage_path:
            raise ValueError(
                "Storage path cannot be empty."
            )

        return self.client.storage.from_(
            self.bucket
        ).download(
            normalized_storage_path
        )

    def download_file(
        self,
        storage_path: str,
        destination: str | Path,
    ) -> Path:
        """Download an object to a local file."""

        destination_path = (
            Path(destination)
            .expanduser()
            .resolve()
        )

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = self.download_bytes(
            storage_path
        )

        destination_path.write_bytes(data)

        return destination_path

    def delete_file(
        self,
        storage_path: str,
    ) -> None:
        """Delete one object from storage."""

        normalized_storage_path = storage_path.strip().lstrip("/")

        if not normalized_storage_path:
            raise ValueError(
                "Storage path cannot be empty."
            )

        self.client.storage.from_(
            self.bucket
        ).remove(
            [normalized_storage_path]
        )
