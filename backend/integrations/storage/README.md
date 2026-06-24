# Storage Adapters

Provider-agnostic storage adapter package implementing `docs/contracts/storage-adapter-interface-contract.md` (MS-ADAPTER-01 / MO-022).

Created 2026-06-01 (B09-002). Status: IMPLEMENTED.

## Purpose

All storage I/O in the platform routes through `StorageRouter` — no service may embed S3 SDK calls, filesystem calls, or any storage provider logic directly. Adapters are registered by provider key; callers interact with the router, not individual adapters.

## Adapters

| Adapter | Provider | File | Use case |
|---|---|---|---|
| `LocalStorageAdapter` | Local/in-memory | `local_adapter.py` | Development, testing, offline LMS-in-a-box |
| `S3StorageAdapter` | AWS S3 / S3-compatible (MinIO, Wasabi, Cloudflare R2, DigitalOcean Spaces) | `s3_adapter.py` | Production — boto3 client injected at construction |

## Canonical buckets

| Content type | Bucket |
|---|---|
| `video` | `lms-video-store` |
| `document` | `lms-document-store` |
| `scorm` / `scorm_package` | `lms-scorm-store` |
| `image` | `lms-image-store` |
| `assessment_asset` | `lms-document-store` |
| `audio` | `lms-document-store` |

## Interface (`base_adapter.py`)

All adapters implement `BaseStorageAdapter`:

- `upload_object(bucket, key, data, content_type, metadata, tenant)`
- `download_object(bucket, key, tenant)`
- `generate_presigned_upload_url(bucket, key, content_type, expires_in, tenant)`
- `generate_presigned_download_url(bucket, key, expires_in, tenant)`
- `delete_object(bucket, key, tenant)`
- `object_exists(bucket, key, tenant)` → `bool`

All operations carry a `TenantStorageContext(tenant_id, storage_region)` for per-tenant routing.

## Router (`router.py`)

`StorageRouter` selects the correct adapter per tenant and translates content type to canonical bucket:

```python
from backend.integrations.storage import StorageRouter, LocalStorageAdapter

router = StorageRouter()
router.set_default(LocalStorageAdapter())

result = router.upload(
    content_type="video",
    key="courses/course_001/intro.mp4",
    data=video_bytes,
    tenant=TenantStorageContext(tenant_id="tenant_abc"),
)
# → uploads to lms-video-store bucket via the registered adapter
```

Enterprise tenants may register their own per-tenant adapter override:
```python
router.register("tenant_enterprise_42", S3StorageAdapter(s3_client=boto3.client("s3"), endpoint_url="https://custom-s3.example.com"))
```

## Design reference

`docs/contracts/storage-adapter-interface-contract.md`  
`docs/designs/file-storage-design.md`
