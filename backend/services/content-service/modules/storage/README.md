# Content Storage Integration Module

This module implements the content-service storage integration pipeline described by:

- `docs/specs/content_service_spec.md`
- `docs/architecture/content_storage_model.md`
- `docs/architecture/file_storage_design.md`

## Capabilities

- File upload pipeline with signed upload intents and upload completion.
- Object storage integration through a provider abstraction.
- CDN access configuration for CDN-enabled content types.
- Secure content access with tenant boundary and role checks.

## Module composition

- `types.ts`: DTOs/contracts for upload, metadata, and access grants.
- `config.ts`: default bucket routing and CDN/access settings.
- `object-storage.client.ts`: object storage provider adapter (in-memory example).
- `cdn-access.service.ts`: CDN signed URL generation abstraction.
- `secure-access.service.ts`: tenant isolation and role-based access control.
- `upload-pipeline.service.ts`: orchestration for upload and access flows.
- `index.ts`: module factory and exports.
