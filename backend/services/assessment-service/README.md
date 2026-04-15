# Assessment Service

Production-ready assessment lifecycle service for Enterprise LMS V2.

## Responsibilities
- Assessment lifecycle and CRUD.
- Quiz/exam/assignment/mock-test definitions.
- Attempt and submission management.
- Grading result linkage (`grading_result_id` only, no grading ownership).
- Tenant-scoped request context.
- Audit logging and observability hooks.
- Domain event publishing for lifecycle changes.

## Runtime Boundaries
- Extends LMS runtime as an independent service module.
- Does **not** replace Course, Lesson, Progress, or Certificate services.
- Does **not** absorb Progress ownership.
- Uses service-local storage contract; no shared database writes.

## Module Structure
- `app/main.py`: FastAPI routes, health, metrics.
- `app/schemas.py`: request/response contracts.
- `app/models.py`: domain models and enums.
- `app/service.py`: business logic and lifecycle orchestration.
- `app/store.py`: storage contract + in-memory adapter.
- `app/events.py`: domain event contract + publisher adapter.
- `app/audit.py`: audit sink.
- `app/tenant.py`: tenant-aware request context resolver.
- `app/observability.py`: counters/metrics hooks.
- `events/*.event.json`: event definitions.
- `tests/test_assessment_service.py`: functional API tests.

## API Routes (v1)
- `POST /api/v1/assessments`
- `GET /api/v1/assessments`
- `GET /api/v1/assessments/{assessment_id}`
- `PATCH /api/v1/assessments/{assessment_id}`
- `POST /api/v1/assessments/{assessment_id}/publish`
- `POST /api/v1/assessments/{assessment_id}/activate`
- `POST /api/v1/assessments/{assessment_id}/retire`
- `DELETE /api/v1/assessments/{assessment_id}`
- `POST /api/v1/assessments/{assessment_id}/attempts`
- `GET /api/v1/assessments/{assessment_id}/attempts`
- `POST /api/v1/attempts/{attempt_id}/submissions`
- `POST /api/v1/attempts/{attempt_id}/grade`
- `GET /api/v1/attempts/{attempt_id}`
- `GET /health`
- `GET /metrics`
- `GET /api/v1/observability/hooks`

## Local test
```bash
cd backend/services/assessment-service
pytest -q
```
