# lesson-service (Enterprise LMS V2)

Production-ready lesson runtime service aligned to the Rails LMS `Lesson` model boundaries.

## Scope and bounded context

- **Owns:** lesson lifecycle, lesson metadata, lesson-to-course linkage, runtime delivery state, progression hook emission.
- **Does NOT own:** Course domain data, Progress domain state, shared database writes.

## Service module structure

- `app/main.py` – versioned REST API, tenant request context, health/metrics, middleware observability hooks.
- `app/models.py` – lesson domain model, audit model, outbox event model.
- `app/schemas.py` – request/response DTOs for lesson CRUD/lifecycle and runtime operations.
- `app/service.py` – core lifecycle and business logic.
- `app/store.py` – storage contract (`LessonStore`) and default in-memory adapter.
- `events/*.json` – event contract definitions for downstream consumers.
- `migrations/0001_create_lessons.sql` – persistence schema, audit table, outbox table.
- `tests/test_lesson_service.py` – API-level coverage and boundary tests.

## Versioned API routes

Base: `/api/v1`

- `POST /lessons`
- `GET /lessons`
- `GET /lessons/{lesson_id}`
- `PATCH /lessons/{lesson_id}`
- `DELETE /lessons/{lesson_id}`
- `POST /lessons/{lesson_id}:publish`
- `POST /lessons/{lesson_id}:unpublish`
- `POST /lessons/{lesson_id}:archive`
- `POST /lessons/{lesson_id}:delivery-state`
- `POST /lessons/{lesson_id}:progression-hooks`

Infra endpoints:

- `GET /health`
- `GET /metrics`

## Tenant-aware context

All business endpoints require:

- `X-Tenant-Id`
- optional `X-Actor-Id` (defaults to `system`)
- JWT bearer auth

## Event definitions

Core lifecycle and runtime events:

- `lesson_created` -> `lms.lesson.created.v1`
- `lesson_updated` -> `lms.lesson.updated.v1`
- `lesson_published` -> `lms.lesson.published.v1`
- `lesson_unpublished` -> `lms.lesson.unpublished.v1`
- `lesson_archived` -> `lms.lesson.archived.v1`
- `lesson_deleted` -> `lms.lesson.deleted.v1`
- `lesson_delivery_state_changed` -> `lms.lesson.delivery_state_changed.v1`
- `lesson_progression_hook_triggered` -> `lms.lesson.progression_hook.v1`

## Migration notes

1. Apply `migrations/0001_create_lessons.sql` in lesson-service database.
2. Backfill lesson rows from Rails-owned lesson export into `lessons` table without changing Rails ownership.
3. Configure outbox dispatcher to publish `lesson_outbox_events` to message bus.
4. Configure audit retention policy on `lesson_audit_log`.
5. Keep cross-service communication for Course and Progress through API/events only.
