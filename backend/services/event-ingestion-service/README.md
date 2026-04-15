# Event Ingestion Service

Production-ready ingestion boundary for Enterprise LMS V2 domain events.

## Scope

This service **only ingests and normalizes events**. It does not own source domain entities and does not write to any shared domain service database.

## Responsibilities

- Capture domain events through `/events/ingest`
- Normalize payloads into a tenant-aware canonical record
- Persist event records and immutable audit entries in service-owned storage
- Forward events to analytics and AI consumers
- Preserve tenant context and end-to-end traceability metadata
- Provide health and metrics endpoints for observability

## Event Families

- `user`
- `course`
- `lesson`
- `enrollment`
- `progress`
- `assessment`
- `certificate`
- `ai`

## API

- `POST /events/ingest`
- `GET /health`
- `GET /metrics`

## Migration notes

1. Provision a dedicated storage schema/database for this service (no shared DB writes).
2. Apply `migrations/0001_create_event_records.sql`.
3. Configure downstream forwarders (analytics + AI endpoints/queues).
4. Replace in-memory store and noop forwarders with production adapters implementing:
   - `EventStorage`
   - `AuditStorage`
   - `EventForwarder`
5. Route producer services to this API instead of direct analytics writes.
