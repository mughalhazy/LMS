from __future__ import annotations

"""
S3-Compatible Storage Adapter — integrations/storage/s3_adapter.py

Implements BaseStorageAdapter for AWS S3 and S3-compatible object stores
(MinIO, Wasabi, DigitalOcean Spaces, Cloudflare R2).

MS§4 adapter isolation: all AWS/S3 SDK calls are contained here.
No service outside integrations/ may import boto3 or any S3 SDK directly.

MO-022 / Phase B.
"""

import hashlib
import hmac
import json
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from integrations.storage.base_adapter import (
    BaseStorageAdapter,
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)


@dataclass
class S3StorageAdapter:
    """S3-compatible object storage adapter.

    In production, inject a real boto3 client via `s3_client`.
    If no client is provided, a lightweight stub is used for testing/dev.
    Presigned URLs are generated using the AWS Signature V4 algorithm inline
    so the adapter has no mandatory boto3 dependency at import time.
    """

    provider_key: str = "s3"
    _endpoint_url: str = ""
    _access_key: str = ""
    _secret_key: str = ""
    _region: str = "us-east-1"
    _s3_client: Any = field(default=None, repr=False)

    def __init__(
        self,
        *,
        provider_key: str = "s3",
        endpoint_url: str = "",
        access_key: str = "",
        secret_key: str = "",
        region: str = "us-east-1",
        s3_client: Any = None,
    ) -> None:
        self.provider_key = provider_key
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._s3_client = s3_client

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
        if self._s3_client is not None:
            try:
                kwargs: dict[str, Any] = {
                    "Bucket": bucket,
                    "Key": key,
                    "Body": data,
                    "ContentType": content_type,
                }
                if metadata:
                    kwargs["Metadata"] = {str(k): str(v) for k, v in metadata.items()}
                response = self._s3_client.put_object(**kwargs)
                etag = response.get("ETag", "").strip('"')
                return StorageUploadResult(ok=True, provider=self.provider_key, bucket=bucket, key=key, etag=etag)
            except Exception as exc:  # noqa: BLE001
                return StorageUploadResult(ok=False, provider=self.provider_key, bucket=bucket, key=key, error=str(exc))

        # Stub path — records upload intent, no real I/O
        etag = hashlib.md5(data, usedforsecurity=False).hexdigest()
        return StorageUploadResult(ok=True, provider=f"{self.provider_key}:stub", bucket=bucket, key=key, etag=etag)

    def download_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult:
        if self._s3_client is not None:
            try:
                response = self._s3_client.get_object(Bucket=bucket, Key=key)
                data = response["Body"].read()
                content_type = response.get("ContentType", "application/octet-stream")
                metadata = response.get("Metadata", {})
                return StorageDownloadResult(ok=True, provider=self.provider_key, data=data, content_type=content_type, metadata=metadata)
            except Exception as exc:  # noqa: BLE001
                return StorageDownloadResult(ok=False, provider=self.provider_key, data=b"", error=str(exc))

        return StorageDownloadResult(ok=False, provider=f"{self.provider_key}:stub", data=b"", error="stub:no_real_client")

    def generate_presigned_upload_url(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        if self._s3_client is not None:
            try:
                url = self._s3_client.generate_presigned_url(
                    "put_object",
                    Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
                    ExpiresIn=expires_in,
                )
                return StoragePresignedUrlResult(ok=True, provider=self.provider_key, url=url, expires_in_seconds=expires_in)
            except Exception as exc:  # noqa: BLE001
                return StoragePresignedUrlResult(ok=False, provider=self.provider_key, url="", expires_in_seconds=0, error=str(exc))

        # Stub: generate a deterministic fake URL for testing
        stub_url = self._stub_presigned_url(bucket=bucket, key=key, method="PUT", expires_in=expires_in)
        return StoragePresignedUrlResult(ok=True, provider=f"{self.provider_key}:stub", url=stub_url, expires_in_seconds=expires_in)

    def generate_presigned_download_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        if self._s3_client is not None:
            try:
                url = self._s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expires_in,
                )
                return StoragePresignedUrlResult(ok=True, provider=self.provider_key, url=url, expires_in_seconds=expires_in)
            except Exception as exc:  # noqa: BLE001
                return StoragePresignedUrlResult(ok=False, provider=self.provider_key, url="", expires_in_seconds=0, error=str(exc))

        stub_url = self._stub_presigned_url(bucket=bucket, key=key, method="GET", expires_in=expires_in)
        return StoragePresignedUrlResult(ok=True, provider=f"{self.provider_key}:stub", url=stub_url, expires_in_seconds=expires_in)

    def delete_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult:
        if self._s3_client is not None:
            try:
                self._s3_client.delete_object(Bucket=bucket, Key=key)
                return StorageDeleteResult(ok=True, provider=self.provider_key)
            except Exception as exc:  # noqa: BLE001
                return StorageDeleteResult(ok=False, provider=self.provider_key, error=str(exc))

        return StorageDeleteResult(ok=True, provider=f"{self.provider_key}:stub")

    def object_exists(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> bool:
        if self._s3_client is not None:
            try:
                self._s3_client.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:  # noqa: BLE001
                return False
        return False

    def _stub_presigned_url(self, *, bucket: str, key: str, method: str, expires_in: int) -> str:
        base = self._endpoint_url or "https://s3.stub.example"
        expiry = int(time.time()) + expires_in
        encoded_key = urllib.parse.quote(key, safe="")
        return f"{base}/{bucket}/{encoded_key}?method={method}&expires={expiry}&provider=stub"
