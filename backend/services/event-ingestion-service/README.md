# Event Ingestion Service

Production-ready ingestion boundary for Enterprise LMS V2 domain events. Spec: `docs/specs/event-ingestion-spec.md`.

## Scope

This service **only ingests, validates, normalizes, and replays events**. It does not own source domain entities.

## Responsibilities

- Capture domain events through `/v1/events/ingest` (single) and `/v1/events/ingest/batch` (batch — B15-038)
- Validate event envelopes against canonical contract without persisting (`/v1/events/validate` — B15-036)
- Replay stored events through forwarding pipeline by tenant/time/type/tags (`/v1/events/replay` — B15-035)
- Normalize payloads into tenant-aware canonical records
- Forward events to analytics, AI, workflow, and operations consumers
- Provide health and metrics endpoints

## Event Families

`user` | `course` | `lesson` | `enrollment` | `progress` | `assessment` | `certificate` | `ai` | `fee` | `attendance` | `operations`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/v1/events/ingest` | Ingest single event (B15-037: canonical v1 path) |
| POST | `/v1/events/ingest/batch` | Ingest multiple events per call (B15-038) |
| POST | `/v1/events/replay` | Replay stored events by tenant/time/type/tags (B15-035) |
| POST | `/v1/events/validate` | Validate envelope against canonical contract without persisting (B15-036) |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## B15 fixes (2026-06-02)

- Path corrected from `/events/ingest` to `/v1/events/ingest` (old path aliased for compatibility)
- Batch ingest added: accepts `{"events": [...]}` with per-event tenant validation
- Replay now queries the event store and re-publishes through the ForwardingPipeline
- Validate now checks all required fields, valid EventFamily enum, and non-empty event_type

## Migration notes

1. Provision a dedicated storage schema/database for this service (no shared DB writes).
2. Apply `migrations/0001_create_event_records.sql`.
3. Configure downstream forwarders (analytics + AI endpoints/queues).
4. Replace in-memory store and noop forwarders with production adapters implementing `EventStorage`, `AuditStorage`, `EventForwarder`.
5. Route producer services to `/v1/events/ingest` instead of old `/events/ingest`.
