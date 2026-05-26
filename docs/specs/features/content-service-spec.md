# Content Service Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-26

Core operations for the content service. Each row defines an operation, the supported content types, and the operation result.

---

| operation | content_type | result |
upload_content | video, audio, document, scorm_package, assessment_asset | Stores the uploaded content, validates format/security constraints, and returns a unique content_id with version metadata.
manage_content_metadata | all_supported_content_types | Creates/updates metadata (title, description, tags, language, duration, licensing, accessibility fields) and returns normalized metadata with audit timestamps.
retrieve_content | video, audio, document, scorm_package, assessment_asset | Fetches content by content_id (or metadata filters), enforces access permissions, and returns secure delivery URL/stream plus metadata.


---

## See also
- `backend/services/content-service/README.md` � content service implementation
- `docs/specs/features/content-versioning-spec.md` � content versioning spec
