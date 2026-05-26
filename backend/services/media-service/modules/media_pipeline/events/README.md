# Media Pipeline Domain Events

This directory defines media pipeline domain event contracts for:

- `media_uploaded`
- `media_processing_started`
- `media_processing_completed`
- `media_published`

Each file contains event metadata (topic, producer, consumers, purpose) and a JSON-schema-style payload definition.

> **Naming convention note:** These events use the `media_*` prefix (snake_case). The main media-service README uses the `video.*` prefix (dot.case: `video.uploaded`, `video.transcoded`, `video.thumbnails_generated`, `video.published`). Both refer to the same pipeline lifecycle. Normalisation to a single canonical event naming convention is a pending action — the `video.*` names in the service README should be reconciled with the `media_*` contracts defined here.
