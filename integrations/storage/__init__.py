"""
Storage adapter package — integrations/storage/
MS§4 adapter isolation: all object storage I/O is routed through this package.

Exports:
  BaseStorageAdapter     — Protocol contract for all adapters
  S3StorageAdapter       — AWS S3 / S3-compatible adapter (production)
  LocalStorageAdapter    — Local filesystem adapter (dev / offline LMS)
  StorageRouter          — Routes by tenant config; content_category → bucket
  TenantStorageContext   — Tenant identity context for storage operations
  StorageUploadResult    — Result type for upload operations
  StorageDownloadResult  — Result type for download operations
  StoragePresignedUrlResult — Result type for presigned URL generation
  StorageDeleteResult    — Result type for delete operations
  resolve_bucket         — Utility: content_category → canonical bucket name
  CONTENT_TYPE_BUCKET_MAP — Canonical bucket name registry

MO-022 / Phase B — storage adapter implementation (resolves MS§4 violation).
"""

from integrations.storage.base_adapter import (
    BaseStorageAdapter,
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)
from integrations.storage.local_adapter import LocalStorageAdapter
from integrations.storage.router import (
    CONTENT_TYPE_BUCKET_MAP,
    StorageRouter,
    resolve_bucket,
)
from integrations.storage.s3_adapter import S3StorageAdapter

__all__ = [
    "BaseStorageAdapter",
    "S3StorageAdapter",
    "LocalStorageAdapter",
    "StorageRouter",
    "TenantStorageContext",
    "StorageUploadResult",
    "StorageDownloadResult",
    "StoragePresignedUrlResult",
    "StorageDeleteResult",
    "resolve_bucket",
    "CONTENT_TYPE_BUCKET_MAP",
]
