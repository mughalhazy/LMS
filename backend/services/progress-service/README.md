# Progress Service

## Authentication

JWT required on all routes (B01-006, 2026-05-31). Authorization: Bearer <token>.

Production-oriented progress tracking service aligned to Rails LMS `Progress` semantics.

## Scope and boundaries
- Owns progress tracking records and completion-state projections.
- Does **not** own Enrollment lifecycle.
- Does **not** own Assessment attempts/results.
- Does **not** require shared database writes with those services.

## Module structure
- `app/main.py`: FastAPI v1 routes, tenant-aware context checks, health/metrics endpoints.
- `app/schemas.py`: request/response schema contracts.
- `app/models.py`: domain entities for progress records, snapshots, metrics, audit, and events.
- `app/service.py`: progress state management, completion logic, audit logging, observability hooks, event publishing.
- `app/store.py`: storage contracts plus in-memory reference adapter.
- `events/*.json`: lifecycle event contract definitions.
- `src/api_contract.md`: API reference summary.
- `migration_notes.md`: rollout and migration guidance.

## Events produced
- `progress.updated`
- `progress.completed`
- `LessonCompletionTracked`
- `CourseCompletionTracked`
- `LearningPathProgressUpdated`

> **Naming convention note:** `progress.updated` and `progress.completed` use dot.case (internal state notifications). `LessonCompletionTracked`, `CourseCompletionTracked`, and `LearningPathProgressUpdated` use PascalCase (domain events published to the event bus). These are two separate namespaces â€” dot.case for internal service signals, PascalCase for cross-service domain events. Reconciliation to a single canonical naming convention is a pending normalisation action.

## Local test
```bash
python -m unittest discover -s backend/services/progress-service/tests -p 'test_*.py'
```
