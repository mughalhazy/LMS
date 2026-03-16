# Progress Service

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

## Local test
```bash
python -m unittest discover -s backend/services/progress-service/tests -p 'test_*.py'
```
