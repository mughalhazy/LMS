# File Storage Design

**Type:** Architecture Reference | **Last reviewed:** 2026-05-26

> **Canonical doc for storage adapter contract:** `docs/contracts/storage-adapter-interface-contract.md`. This file is a historical bucket access reference; the adapter contract is authoritative for integration. See `docs/contracts/content-storage-model.md` for metadata field definitions.

Storage bucket layout and access method per content type.

---

| storage_component | content_types | access_method |
|---|---|---|
| Object Storage Bucket (`lms-video-store`) + CDN | videos | Signed CDN URLs for streaming/download; upload via pre-signed PUT URLs |
| Object Storage Bucket (`lms-document-store`) | documents | Pre-signed GET/PUT URLs through Content API; optional inline preview via secure proxy |
| Object Storage Bucket (`lms-scorm-store`) + SCORM Runtime Service | SCORM packages | Package upload via pre-signed PUT; launch via tokenized runtime URL that mounts extracted package assets |
| Object Storage Bucket (`lms-image-store`) + Image Optimization Service + CDN | images | Public CDN URLs for approved assets, otherwise signed GET URLs; upload via pre-signed PUT URLs |
