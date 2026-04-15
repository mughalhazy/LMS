from __future__ import annotations

"""
Local Filesystem Storage Adapter — integrations/storage/local_adapter.py

Implements BaseStorageAdapter backed by the local filesystem.
Intended for: development, single-server deployments, offline-first LMS-in-a-box scenarios.

Bucket names map to subdirectories under `base_path`.
Pre-signed URLs are stub URLs that encode the path — they are not functional
for remote access without a local file-serving proxy.

MS§4 adapter isolation: local I/O is contained here.
MO-022 / Phase B.
"""

import hashlib
import json
import os
import time
import urllib.parse
from pathlib import Path

from integrations.storage.base_adapter import (
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)


class LocalStorageAdapter:
    """Local filesystem object storage adapter."""

    provider_key: str = "local"

    def __init__(self, *, base_path: str = "/tmp/lms-storage", serve_base_url: str = "http://localhost:8090/files") -> None:
        self.provider_key = "local"
        self._base_path = Path(base_path)
        self._serve_base_url = serve_base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _object_path(self, *, bucket: str, key: str) -> Path:
        safe_key = key.lstrip("/")
        return self._base_path / bucket / safe_key

    def _ensure_parent(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def _metadata_path(self, *, bucket: str, key: str) -> Path:
        return self._object_path(bucket=bucket, key=key).with_suffix(".meta.json")

    # ------------------------------------------------------------------
    # Protocol implementation
    # ------------------------------------------------------------------

    def upload_object(
        self,
        *,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict | None = None,
        tenant: TenantStorageContext,
    ) -> StorageUploadResult:
        try:
            path = self._object_path(bucket=bucket, key=key)
            self._ensure_parent(path)
            path.write_bytes(data)
            meta = {"content_type": content_type, "tenant_id": tenant.tenant_id}
            if metadata:
                meta.update(metadata)
            self._metadata_path(bucket=bucket, key=key).write_text(json.dumps(meta))
            etag = hashlib.md5(data, usedforsecurity=False).hexdigest()
            return StorageUploadResult(ok=True, provider=self.provider_key, bucket=bucket, key=key, etag=etag)
        except Exception as exc:  # noqa: BLE001
            return StorageUploadResult(ok=False, provider=self.provider_key, bucket=bucket, key=key, error=str(exc))

    def download_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult:
        try:
            path = self._object_path(bucket=bucket, key=key)
            if not path.exists():
                return StorageDownloadResult(ok=False, provider=self.provider_key, data=b"", error="object_not_found")
            data = path.read_bytes()
            meta_path = self._metadata_path(bucket=bucket, key=key)
            meta: dict = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            content_type = meta.pop("content_type", "application/octet-stream")
            return StorageDownloadResult(ok=True, provider=self.provider_key, data=data, content_type=content_type, metadata=meta)
        except Exception as exc:  # noqa: BLE001
            return StorageDownloadResult(ok=False, provider=self.provider_key, data=b"", error=str(exc))

    def generate_presigned_upload_url(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        expiry = int(time.time()) + expires_in
        encoded_key = urllib.parse.quote(key, safe="")
        url = f"{self._serve_base_url}/upload/{bucket}/{encoded_key}?expires={expiry}&content_type={urllib.parse.quote(content_type)}"
        return StoragePresignedUrlResult(ok=True, provider=self.provider_key, url=url, expires_in_seconds=expires_in)

    def generate_presigned_download_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        expiry = int(time.time()) + expires_in
        encoded_key = urllib.parse.quote(key, safe="")
        url = f"{self._serve_base_url}/{bucket}/{encoded_key}?expires={expiry}"
        return StoragePresignedUrlResult(ok=True, provider=self.provider_key, url=url, expires_in_seconds=expires_in)

    def delete_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult:
        try:
            path = self._object_path(bucket=bucket, key=key)
            if path.exists():
                path.unlink()
            meta = self._metadata_path(bucket=bucket, key=key)
            if meta.exists():
                meta.unlink()
            return StorageDeleteResult(ok=True, provider=self.provider_key)
        except Exception as exc:  # noqa: BLE001
            return StorageDeleteResult(ok=False, provider=self.provider_key, error=str(exc))

    def object_exists(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> bool:
        return self._object_path(bucket=bucket, key=key).exists()
