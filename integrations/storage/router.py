from __future__ import annotations

"""
Storage Adapter Router — integrations/storage/router.py

Routes storage operations to the correct adapter based on tenant storage
configuration. Follows the same adapter-routing pattern as
integrations/payments/router.py and integrations/communication/base_adapter.py.

Canonical content-type to bucket mapping (per file_storage_design.md):
  video     → lms-video-store
  document  → lms-document-store
  scorm     → lms-scorm-store
  image     → lms-image-store

MS§4: Router never embeds provider logic — it selects adapters only.
MO-022 / Phase B.
"""

from integrations.storage.base_adapter import (
    BaseStorageAdapter,
    StorageDeleteResult,
    StorageDownloadResult,
    StoragePresignedUrlResult,
    StorageUploadResult,
    TenantStorageContext,
)

# Canonical bucket names per content type (file_storage_design.md)
CONTENT_TYPE_BUCKET_MAP: dict[str, str] = {
    "video": "lms-video-store",
    "document": "lms-document-store",
    "scorm": "lms-scorm-store",
    "image": "lms-image-store",
}

# Default presigned URL TTLs (seconds)
DEFAULT_UPLOAD_TTL = 900   # 15 minutes
DEFAULT_DOWNLOAD_TTL = 3600  # 1 hour
DEFAULT_VIDEO_STREAM_TTL = 14400  # 4 hours (streaming sessions)


def resolve_bucket(content_category: str) -> str:
    """Return canonical bucket name for a given content category."""
    bucket = CONTENT_TYPE_BUCKET_MAP.get(content_category.lower())
    if bucket is None:
        raise ValueError(
            f"Unknown content_category '{content_category}'. "
            f"Must be one of: {list(CONTENT_TYPE_BUCKET_MAP)}"
        )
    return bucket


class StorageRouter:
    """Adapter-driven storage router.

    Selects the registered adapter by provider_key. If a tenant has a specific
    storage provider configured, that adapter is used; otherwise, the default
    adapter is used.

    Usage:
        router = StorageRouter(default_adapter=LocalStorageAdapter())
        result = router.upload(
            content_category="video",
            key="tenant_abc/course_1/intro.mp4",
            data=video_bytes,
            content_type="video/mp4",
            tenant=TenantStorageContext(tenant_id="tenant_abc"),
        )
    """

    def __init__(
        self,
        default_adapter: BaseStorageAdapter,
        adapters: dict[str, BaseStorageAdapter] | None = None,
        tenant_provider_config: dict[str, str] | None = None,
    ) -> None:
        self._default_adapter = default_adapter
        self._adapters: dict[str, BaseStorageAdapter] = {default_adapter.provider_key: default_adapter}
        if adapters:
            self._adapters.update(adapters)
        self._tenant_provider_config: dict[str, str] = tenant_provider_config or {}

    def _resolve_adapter(self, tenant: TenantStorageContext) -> BaseStorageAdapter:
        provider_key = self._tenant_provider_config.get(tenant.tenant_id)
        if provider_key and provider_key in self._adapters:
            return self._adapters[provider_key]
        return self._default_adapter

    def upload(
        self,
        *,
        content_category: str,
        key: str,
        data: bytes,
        content_type: str,
        metadata: dict | None = None,
        tenant: TenantStorageContext,
    ) -> StorageUploadResult:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.upload_object(bucket=bucket, key=key, data=data, content_type=content_type, metadata=metadata, tenant=tenant)

    def download(
        self,
        *,
        content_category: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.download_object(bucket=bucket, key=key, tenant=tenant)

    def presigned_upload_url(
        self,
        *,
        content_category: str,
        key: str,
        content_type: str,
        expires_in: int = DEFAULT_UPLOAD_TTL,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.generate_presigned_upload_url(bucket=bucket, key=key, content_type=content_type, expires_in=expires_in, tenant=tenant)

    def presigned_download_url(
        self,
        *,
        content_category: str,
        key: str,
        expires_in: int = DEFAULT_DOWNLOAD_TTL,
        tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.generate_presigned_download_url(bucket=bucket, key=key, expires_in=expires_in, tenant=tenant)

    def delete(
        self,
        *,
        content_category: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.delete_object(bucket=bucket, key=key, tenant=tenant)

    def exists(
        self,
        *,
        content_category: str,
        key: str,
        tenant: TenantStorageContext,
    ) -> bool:
        bucket = resolve_bucket(content_category)
        adapter = self._resolve_adapter(tenant)
        return adapter.object_exists(bucket=bucket, key=key, tenant=tenant)

    def register_adapter(self, adapter: BaseStorageAdapter) -> None:
        """Register an additional adapter. Called during tenant onboarding for custom storage configs."""
        self._adapters[adapter.provider_key] = adapter

    def configure_tenant_provider(self, tenant_id: str, provider_key: str) -> None:
        """Assign a specific storage adapter to a tenant."""
        if provider_key not in self._adapters:
            raise ValueError(f"Provider '{provider_key}' is not registered")
        self._tenant_provider_config[tenant_id] = provider_key
