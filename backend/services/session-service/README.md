# Session Service

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

## Module structure
- `app/main.py` — versioned REST API (`/api/v2/sessions`)
- `app/schemas.py` — request schema contracts
- `src/models.py` — domain models and events
- `src/repository.py` — storage contract + in-memory reference adapter
- `src/service.py` — service logic and scheduling/lifecycle policy
- `src/events.py` — lifecycle event definitions
- `tests/test_session_service.py` — service and API tests
- `docs/migration_notes.md` — migration guidance

## Boundary integrity
This service stores only session-owned data (schedule, metadata, lifecycle, link references).
It does **not** replace ownership of `Course`, `Lesson`, or `Enrollment`, and does not perform shared database writes.
