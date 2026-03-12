# Content Metadata Module

This module regenerates metadata capabilities for the content service based on:

- `docs/specs/content_service_spec.md`
- `docs/data/core_lms_schema.md`
- `docs/architecture/cloud_architecture_lms.md`

## Implemented capabilities

- **Metadata storage**: create, retrieve, update, delete lifecycle through `MetadataService` and `MetadataRepository`.
- **Metadata updates**: partial updates with immutable `createdAtIso`, incrementing `version`, and `updatedBy` auditing.
- **Content tagging**: normalization (trim, lowercase, deduplicate, max limits) plus add/remove helpers.
- **Search indexing hooks**: upsert/delete callbacks for external search index pipelines.

## Module composition

- `types.ts`: contracts for metadata, update flows, repository API, and search hook interfaces.
- `config.ts`: module-level limits and normalization behavior.
- `metadata.repository.ts`: in-memory repository with tenant-aware metadata querying.
- `tagging.service.ts`: tag normalization and merge/remove helpers.
- `search-index.hooks.ts`: in-memory hook implementation for indexing events.
- `metadata.service.ts`: orchestration for metadata CRUD, tagging, and index hooks.
- `index.ts`: exports and factory for module composition.

## Usage

```ts
import { createMetadataModule } from "./modules/metadata";

const metadataModule = createMetadataModule();

await metadataModule.service.createMetadata({
  contentId: "asset_123",
  tenantId: "tenant_acme",
  contentType: "video",
  actorUserId: "user_1",
  title: "Safety Orientation",
  tags: ["Compliance", "Safety"],
});

await metadataModule.service.addTags({
  tenantId: "tenant_acme",
  contentId: "asset_123",
  actorUserId: "user_2",
  tags: ["Onboarding"],
});

const results = await metadataModule.service.search({
  tenantId: "tenant_acme",
  tagsAny: ["safety"],
});

console.log(results.total);
console.log(metadataModule.searchHook.events);
```
