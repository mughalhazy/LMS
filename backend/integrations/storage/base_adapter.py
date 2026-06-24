"""BaseStorageAdapter Protocol — storage-adapter-interface-contract.md.

B09-002: provider-agnostic storage adapter contract per MS§4 adapter isolation.
All storage I/O must route through this contract — no service may embed S3 SDK
calls, filesystem calls, or any storage provider logic directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TenantStorageContext:
    tenant_id: str
    storage_region: str = "default"


@dataclass
class StorageUploadResult:
    bucket: str
    key: str
    etag: str
    size_bytes: int
    provider_ref: str = ""


@dataclass
class StorageDownloadResult:
    bucket: str
    key: str
    data: bytes
    content_type: str
    size_bytes: int


@dataclass
class StoragePresignedUrlResult:
    url: str
    expires_at: str
    method: str  # GET | PUT


@dataclass
class StorageDeleteResult:
    bucket: str
    key: str
    deleted: bool


class BaseStorageAdapter:
    """Provider-agnostic storage adapter Protocol (storage-adapter-interface-contract.md)."""

    provider_key: str = "base"

    def upload_object(
        self, *, bucket: str, key: str, data: bytes,
        content_type: str, metadata: dict[str, Any] | None = None,
        tenant: TenantStorageContext,
    ) -> StorageUploadResult:
        raise NotImplementedError

    def download_object(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult:
        raise NotImplementedError

    def generate_presigned_upload_url(
        self, *, bucket: str, key: str, content_type: str,
        expires_in: int, tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        raise NotImplementedError

    def generate_presigned_download_url(
        self, *, bucket: str, key: str,
        expires_in: int, tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        raise NotImplementedError

    def delete_object(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult:
        raise NotImplementedError

    def object_exists(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> bool:
        raise NotImplementedError
