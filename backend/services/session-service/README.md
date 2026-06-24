# Session Service

## Authentication

JWT required on all routes (B01-015, 2026-05-31). Authorization: Bearer <token>.

Production-ready `session_service` implementation for Enterprise LMS V2.

## Scope
- session lifecycle transitions
- session scheduling and rescheduling history
- session-to-course linkage
- session-to-lesson linkage (reference only)
- session-to-cohort linkage
- delivery metadata for `in_person`, `online`, and `hybrid`
- tenant-aware records and access checks
- audit logging and event publishing
- health and observability endpoints

## API versioning note

This service uses `/api/v2/sessions`. It is the only service in the platform not on `/api/v1/`. This is intentional â€” the session service was designed as a v2 API from inception, with a richer scheduling, rescheduling, and cohort-linkage model not present in the v1 baseline. All other services use `/api/v1/`.

## Module structure
- `app/main.py` â€” versioned REST API (`/api/v2/sessions`)
- `app/schemas.py` â€” request schema contracts
- `src/models.py` â€” domain models and events
- `src/repository.py` â€” storage contract + in-memory reference adapter
- `src/service.py` â€” service logic and scheduling/lifecycle policy
- `src/events.py` â€” lifecycle event definitions
- `tests/test_session_service.py` â€” service and API tests
- `docs/migration_notes.md` â€” migration guidance

## Boundary integrity
This service stores only session-owned data (schedule, metadata, lifecycle, link references).
It does **not** replace ownership of `Course`, `Lesson`, or `Enrollment`, and does not perform shared database writes.
