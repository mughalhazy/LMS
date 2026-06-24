"""S3StorageAdapter — AWS S3 / S3-compatible production storage.

B09-002: storage-adapter-interface-contract.md §Implementations.
Provider SDK (boto3) is injected at construction — not imported at module level,
preserving offline-box portability when boto3 is not installed.
"""
from __future__ import annotations

import logging
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

logger = logging.getLogger("integrations.storage.s3")


class S3StorageAdapter(BaseStorageAdapter):
    """S3-compatible object storage — production use (AWS S3, MinIO, Wasabi, Cloudflare R2)."""

    provider_key: str = "s3"

    def __init__(self, s3_client: Any | None = None, endpoint_url: str | None = None) -> None:
        self._client = s3_client  # injected boto3 client; None = stub mode
        self._endpoint = endpoint_url

    def _client_or_stub(self) -> Any:
        if self._client is None:
            raise RuntimeError("S3StorageAdapter: no boto3 client configured — running in stub mode")
        return self._client

    def upload_object(self, *, bucket: str, key: str, data: bytes, content_type: str,
                      metadata: dict[str, Any] | None = None, tenant: TenantStorageContext) -> StorageUploadResult:
        client = self._client_or_stub()
        resp = client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type,
                                  Metadata={**(metadata or {}), "tenant_id": tenant.tenant_id})
        return StorageUploadResult(bucket=bucket, key=key,
                                   etag=resp.get("ETag", "").strip('"'),
                                   size_bytes=len(data), provider_ref="s3")

    def download_object(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> StorageDownloadResult:
        client = self._client_or_stub()
        resp = client.get_object(Bucket=bucket, Key=key)
        data = resp["Body"].read()
        return StorageDownloadResult(bucket=bucket, key=key, data=data,
                                     content_type=resp.get("ContentType", "application/octet-stream"),
                                     size_bytes=len(data))

    def generate_presigned_upload_url(self, *, bucket: str, key: str, content_type: str,
                                       expires_in: int, tenant: TenantStorageContext) -> StoragePresignedUrlResult:
        client = self._client_or_stub()
        url = client.generate_presigned_url("put_object", Params={"Bucket": bucket, "Key": key,
                                                                     "ContentType": content_type}, ExpiresIn=expires_in)
        return StoragePresignedUrlResult(url=url, expires_at=datetime.now(timezone.utc).isoformat(), method="PUT")

    def generate_presigned_download_url(self, *, bucket: str, key: str,
                                         expires_in: int, tenant: TenantStorageContext) -> StoragePresignedUrlResult:
        client = self._client_or_stub()
        url = client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires_in)
        return StoragePresignedUrlResult(url=url, expires_at=datetime.now(timezone.utc).isoformat(), method="GET")

    def delete_object(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> StorageDeleteResult:
        self._client_or_stub().delete_object(Bucket=bucket, Key=key)
        return StorageDeleteResult(bucket=bucket, key=key, deleted=True)

    def object_exists(self, *, bucket: str, key: str, tenant: TenantStorageContext) -> bool:
        try:
            self._client_or_stub().head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False
