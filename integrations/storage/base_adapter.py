from __future__ import annotations

"""
Storage Adapter Base — integrations/storage/base_adapter.py
MS§4 Adapter Isolation — all storage I/O must route through this interface.
No service may embed provider SDK calls directly.

MO-022 / Phase B — storage adapter implementation.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class StorageUploadResult:
    ok: bool
    provider: str
    bucket: str
    key: str
    etag: str = ""
    error: str | None = None


@dataclass(frozen=True)
class StorageDownloadResult:
    ok: bool
    provider: str
    data: bytes
    content_type: str = "application/octet-stream"
    metadata: dict = field(default_factory=dict)
    error: str | None = None


@dataclass(frozen=True)
class StoragePresignedUrlResult:
    ok: bool
    provider: str
    url: str
    expires_in_seconds: int
    error: str | None = None


@dataclass(frozen=True)
class StorageDeleteResult:
    ok: bool
    provider: str
    error: str | None = None


@dataclass(frozen=True)
class TenantStorageContext:
    tenant_id: str
    storage_region: str = "default"


class BaseStorageAdapter(Protocol):
    """Provider-agnostic storage adapter contract.

    All implementations must satisfy this Protocol.
    Canonical buckets are defined per content type in file_storage_design.md:
      lms-video-store, lms-document-store, lms-scorm-store, lms-image-store
    """

    provider_key: str

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
        """Upload object bytes to the specified bucket/key."""

    def download_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult:
        """Download object bytes from the specified bucket/key."""

    def generate_presigned_upload_url(
        self,
        *,
        bucket: str,
        key: str,
        content_type: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        """Generate a short-lived pre-signed URL for direct client upload."""

    def generate_presigned_download_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in: int,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        """Generate a short-lived pre-signed URL for direct client download."""

    def delete_object(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult:
        """Delete object from bucket. Non-existent key is treated as success."""

    def object_exists(
        self,
        *,
        bucket: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> bool:
        """Return True if the object exists in the bucket."""
