"""StorageRouter — selects correct adapter per tenant and maps content type to canonical bucket.

B09-002: storage-adapter-interface-contract.md §Router.
Services interact with StorageRouter, not individual adapters directly.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_adapter import BaseStorageAdapter, TenantStorageContext
from .local_adapter import LocalStorageAdapter

logger = logging.getLogger("integrations.storage.router")

# Canonical bucket map per content-type (storage-adapter-interface-contract.md §Canonical Buckets)
_CANONICAL_BUCKETS: dict[str, str] = {
    "video": "lms-video-store",
    "document": "lms-document-store",
    "scorm": "lms-scorm-store",
    "image": "lms-image-store",
    "scorm_package": "lms-scorm-store",
    "assessment_asset": "lms-document-store",
    "audio": "lms-document-store",
}

_DEFAULT_ADAPTER = LocalStorageAdapter()


class StorageRouter:
    """Routes storage calls to the correct adapter per tenant and maps content type to bucket."""

    def __init__(self) -> None:
        self._adapters: dict[str, BaseStorageAdapter] = {}
        self._default: BaseStorageAdapter = _DEFAULT_ADAPTER

    def register(self, tenant_id: str, adapter: BaseStorageAdapter) -> None:
        """Register a per-tenant adapter override (e.g., enterprise BYOS tenants)."""
        self._adapters[tenant_id] = adapter

    def set_default(self, adapter: BaseStorageAdapter) -> None:
        self._default = adapter

    def resolve_adapter(self, tenant: TenantStorageContext) -> BaseStorageAdapter:
        return self._adapters.get(tenant.tenant_id, self._default)

    def bucket_for(self, content_type: str) -> str:
        bucket = _CANONICAL_BUCKETS.get(content_type)
        if not bucket:
            logger.warning("StorageRouter: unknown content_type %r — defaulting to lms-document-store", content_type)
            return "lms-document-store"
        return bucket

    def upload(self, *, content_type: str, key: str, data: bytes,
               metadata: dict[str, Any] | None = None, tenant: TenantStorageContext) -> Any:
        adapter = self.resolve_adapter(tenant)
        bucket = self.bucket_for(content_type)
        return adapter.upload_object(bucket=bucket, key=key, data=data,
                                      content_type=content_type, metadata=metadata, tenant=tenant)

    def presigned_download(self, *, content_type: str, key: str,
                            expires_in: int = 900, tenant: TenantStorageContext) -> Any:
        adapter = self.resolve_adapter(tenant)
        bucket = self.bucket_for(content_type)
        return adapter.generate_presigned_download_url(bucket=bucket, key=key,
                                                        expires_in=expires_in, tenant=tenant)
