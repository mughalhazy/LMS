# Storage Adapter Interface Contract

**Type:** Architecture | **Date:** 2026-04-14 | **MS§:** §4 (Adapter Isolation)
**Source:** `adapter_inventory.md` — required this doc as part of storage adapter implementation
**Status:** IMPLEMENTED — `integrations/storage/` (MO-022 / Phase B)

---

## Purpose

Define the provider-agnostic storage adapter contract for the file/object storage domain. All storage I/O in the platform must route through this contract — no service may embed S3 SDK calls, filesystem calls, or any storage provider logic directly.

This contract follows the same MS§4 isolation pattern as:
- `docs/architecture/payment_provider_adapter_interface_contract.md`
- `docs/architecture/communication_adapter_interface_contract.md`

---

## Domain Boundary

### Storage adapter responsibilities (this interface)
- Upload objects (bytes) to a named bucket/key
- Download objects from a named bucket/key
- Generate pre-signed upload URLs for direct client upload
- Generate pre-signed download URLs for direct client download
- Delete objects
- Check object existence

### Explicitly out of scope (handled by other services)
- Content metadata (title, status, content_tier) — managed by `services/file-storage/`
- Media transcoding, image optimization, SCORM extraction — managed by `services/media-pipeline/`
- Playback authorization and session token management — managed by `services/media-security/`
- Content CDN configuration — infrastructure layer (`infrastructure/`)

---

## Canonical Buckets (per `file_storage_design.md`)

| Content Type | Canonical Bucket | Access Pattern |
|---|---|---|
| `video` | `lms-video-store` | Pre-signed URLs; CDN for streaming (production) |
| `document` | `lms-document-store` | Pre-signed GET/PUT; inline preview via secure proxy |
| `scorm` | `lms-scorm-store` | Package upload via pre-signed PUT; runtime via SCORM service |
| `image` | `lms-image-store` | Public CDN for approved assets; signed GET for gated assets |

Content category → bucket routing is handled by `StorageRouter` in `integrations/storage/router.py`.

---

## Interface Contract

```python
class BaseStorageAdapter(Protocol):
    provider_key: str

    def upload_object(
        self, *, bucket: str, key: str, data: bytes,
        content_type: str, metadata: dict | None = None,
        tenant: TenantStorageContext,
    ) -> StorageUploadResult: ...

    def download_object(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> StorageDownloadResult: ...

    def generate_presigned_upload_url(
        self, *, bucket: str, key: str, content_type: str,
        expires_in: int, tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult: ...

    def generate_presigned_download_url(
        self, *, bucket: str, key: str,
        expires_in: int, tenant: TenantStorageContext,
    ) -> StoragePresignedUrlResult: ...

    def delete_object(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> StorageDeleteResult: ...

    def object_exists(
        self, *, bucket: str, key: str,
        tenant: TenantStorageContext,
    ) -> bool: ...
```

See `integrations/storage/base_adapter.py` for full type definitions.

---

## Implementations

| Adapter | Path | Use Case |
|---|---|---|
| `S3StorageAdapter` | `integrations/storage/s3_adapter.py` | Production — AWS S3 / S3-compatible (MinIO, Wasabi, Cloudflare R2, DigitalOcean Spaces) |
| `LocalStorageAdapter` | `integrations/storage/local_adapter.py` | Development / single-server / offline LMS-in-a-box |

Both implement the `BaseStorageAdapter` Protocol structurally (no inheritance required).

---

## Router

`StorageRouter` (`integrations/storage/router.py`) selects the correct adapter per tenant and translates content category to canonical bucket name. Services interact with `StorageRouter`, not individual adapters directly.

---

## Tenant Context

All storage operations carry a `TenantStorageContext(tenant_id, storage_region)`. The router uses `tenant_id` to select per-tenant storage providers (e.g., enterprise tenants may have their own S3 bucket).

---

## BC-CONTENT-02 Integration

The file storage service (`services/file-storage/service.py`) enforces BC-CONTENT-02:
- Paid content (`content_tier = "paid"`) never receives a direct presigned download URL from the file storage service
- Callers are redirected to the media security service for session-token-gated access
- This enforcement is at the service layer, not the adapter layer — the storage adapter itself is tier-agnostic

---

## MS§4 Enforcement

Per MS-ADAPTER-01:
- `services/file-storage/` imports from `integrations/storage/` — correct
- `services/media-pipeline/` imports from `integrations/storage/` — correct
- `services/media-security/` does **not** import from `integrations/storage/` directly — it operates on tokens, not raw storage operations — correct
- No service outside `integrations/storage/` may import `boto3`, `s3fs`, or any storage SDK

---

## References

- `integrations/storage/base_adapter.py` — Protocol definition
- `integrations/storage/router.py` — adapter routing + bucket mapping
- `integrations/storage/s3_adapter.py` — S3 implementation
- `integrations/storage/local_adapter.py` — local implementation
- `services/file-storage/service.py` — primary consumer of this contract
- `services/media-pipeline/service.py` — secondary consumer (processed asset storage)
- `docs/architecture/file_storage_design.md` — bucket/content-type design
- `docs/specs/adapter_inventory.md` — adapter registry
