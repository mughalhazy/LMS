"""Object storage integration for media pipeline assets."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from .models import StorageObject


class ObjectStorageClient(Protocol):
    """Storage adapter protocol allowing provider swapping (S3, GCS, Azure Blob)."""

    def put_bytes(self, bucket: str, key: str, data: bytes) -> StorageObject:
        """Persist bytes and return canonical object metadata."""

    def create_presigned_get_url(self, bucket: str, key: str, ttl_seconds: int = 900) -> str:
        """Create a short-lived URL to fetch media objects directly."""


@dataclass(slots=True)
class InMemoryObjectStorageClient:
    """A lightweight in-memory object store useful for local integration tests."""

    _store: dict[str, bytes]

    def __init__(self) -> None:
        self._store = {}

    def put_bytes(self, bucket: str, key: str, data: bytes) -> StorageObject:
        storage_key = f"{bucket}/{key}"
        self._store[storage_key] = data
        checksum = sha256(data).hexdigest()
        return StorageObject(bucket=bucket, key=key, checksum_sha256=checksum, size_bytes=len(data))

    def create_presigned_get_url(self, bucket: str, key: str, ttl_seconds: int = 900) -> str:
        return f"https://storage.local/{bucket}/{key}?ttl={ttl_seconds}"


class LocalFileObjectStorageClient(InMemoryObjectStorageClient):
    """Writes objects to a local directory while still exposing an S3-like interface."""

    def __init__(self, root: str | Path) -> None:
        super().__init__()
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, bucket: str, key: str, data: bytes) -> StorageObject:
        obj = super().put_bytes(bucket=bucket, key=key, data=data)
        path = self._root / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return obj
