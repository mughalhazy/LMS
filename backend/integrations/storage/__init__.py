"""Storage adapter package — provider-agnostic object storage adapters.

B09-002: storage-adapter-interface-contract.md claims implementation exists at
integrations/storage/. This package fulfils that contract (MO-022 / Phase B).
"""
from .base_adapter import (
    BaseStorageAdapter,
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)
from .local_adapter import LocalStorageAdapter
from .router import StorageRouter
from .s3_adapter import S3StorageAdapter

__all__ = [
    "BaseStorageAdapter",
    "LocalStorageAdapter",
    "S3StorageAdapter",
    "StorageDeleteResult",
    "StorageDownloadResult",
    "StoragePresignedUrlResult",
    "StorageRouter",
    "StorageUploadResult",
    "TenantStorageContext",
]
