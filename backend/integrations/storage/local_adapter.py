"""LocalStorageAdapter — in-memory/local storage for dev and offline-box.

B09-002: storage-adapter-interface-contract.md §Implementations.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .base_adapter import (
    BaseStorageAdapter,
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)


class LocalStorageAdapter(BaseStorageAdapter):
    """In-memory local storage — development / offline LMS-in-a-box use."""

    provider_key: str = "local"

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def _k(self, bucket: str, key: str) -> str:
        return f"{bucket}/{key}"

    def upload_object(
        self, *, bucket: str, key: str, data: bytes,
        content_type: str, metadata: dict[str, Any] | None = None,
        tenant: TenantStorageContext,
    ) -> StorageUploadResult:
        self._store[self._k(bucket, key)] = {
            "data": data, "content_type": content_type,
            "metadata": metadata or {}, "tenant_id": tenant.tenant_id,
        }
        etag = hashlib.md5(data).hexdigest()
        return StorageUploadResult(bucket=bucket, key=key, etag=etag, size_bytes=len(data), provider_ref="local")

    def download_object(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> StorageDownloadResult:
        obj = self._store.get(self._k(bucket, key))
        if not obj:
            raise FileNotFoundError(f"Object not found: {bucket}/{key}")
        return StorageDownloadResult(bucket=bucket, key=key, data=obj["data"],
                                     content_type=obj["content_type"], size_bytes=len(obj["data"]))

    def generate_presigned_upload_url(self, *, bucket: str, key: str, content_type: str,
                                       expires_in: int, tenant: TenantStorageContext) -> StoragePresignedUrlResult:
        return StoragePresignedUrlResult(
            url=f"local://upload/{bucket}/{key}",
            expires_at=datetime.now(timezone.utc).isoformat(),
            method="PUT",
        )

    def generate_presigned_download_url(self, *, bucket: str, key: str,
                                         expires_in: int, tenant: TenantStorageContext) -> StoragePresignedUrlResult:
        return StoragePresignedUrlResult(
            url=f"local://download/{bucket}/{key}",
            expires_at=datetime.now(timezone.utc).isoformat(),
            method="GET",
        )

    def delete_object(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> StorageDeleteResult:
        existed = self._k(bucket, key) in self._store
        self._store.pop(self._k(bucket, key), None)
        return StorageDeleteResult(bucket=bucket, key=key, deleted=existed)

    def object_exists(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> bool:
        return self._k(bucket, key) in self._store
