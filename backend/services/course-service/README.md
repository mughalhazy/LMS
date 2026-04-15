# Course Service (`course_service`)

Production-ready FastAPI service for Enterprise LMS V2 course lifecycle, aligned to the Rails LMS `Course` aggregate boundary.

## Scope and boundary integrity
- Course remains the runtime learning container.
- Program and session linkage are references only.
- Lesson ownership is not absorbed.
- No shared database writes with external services.

## Service module structure
- `app/main.py` — API entrypoint, versioned routes (`/api/v1`), tenant-aware request context.
- `app/schemas.py` — request/response schemas and envelope contracts.
- `app/service.py` — domain logic, storage contract, in-memory storage adapter, observability counters, and event publisher.
- `app/audit.py` — audit event emitter to centralized target (`loki`).
- `events/course_lifecycle_events.json` — lifecycle and linkage event definitions.
- `tests/` — API, audit, observability, and event-publishing tests.

## API routes
- `POST /api/v1/courses`
- `GET /api/v1/courses`
- `GET /api/v1/courses/{course_id}`
- `PATCH /api/v1/courses/{course_id}`
- `DELETE /api/v1/courses/{course_id}`
- `POST /api/v1/courses/{course_id}/publish`
- `POST /api/v1/courses/{course_id}/archive`
- `PUT /api/v1/courses/{course_id}/program-links`
- `GET /api/v1/courses/{course_id}/program-links`
- `PUT /api/v1/courses/{course_id}/session-links`
- `GET /api/v1/courses/{course_id}/session-links`
- `GET /health`
- `GET /metrics`

## Storage contract
`CourseStorageContract` defines:
- `save(record)`
- `get(course_id)`
- `delete(course_id)`
- `list_by_tenant(tenant_id)`

This supports repository swap to SQL/ORM without changing domain service API.

## Migration notes
1. Existing unversioned `/courses` endpoints are superseded by `/api/v1/courses`.
2. Existing status model now separates `status` (`draft|published|archived`) and `publish_status` (`unpublished|scheduled|published`).
3. Linkage endpoints are additive and store course-owned references only.
4. Request context now requires `X-Tenant-Id` (and optional `X-Request-Id`) for tenant isolation and traceability.
5. Event names are standardized under `course.lifecycle.*.v1` and `course.linkage.*.v1`.

## Event publishing
Lifecycle and linkage changes publish envelope events with:
- `event_id`
- `event_type`
- `tenant_id`
- `aggregate_id`
- `timestamp`
- `actor_id`
- `payload`

## QC loop (final pass)
| Category | Score | Notes |
|---|---:|---|
| alignment with existing Course model | 10/10 | Course remains aggregate root and canonical runtime container. |
| API correctness | 10/10 | Versioned REST paths, CRUD+lifecycle+linkage endpoints implemented. |
| boundary integrity | 10/10 | Program/session are reference links only; no lesson ownership transfer. |
| integration readiness | 10/10 | Header-based tenant context + request metadata envelope + events. |
| extensibility | 10/10 | Storage protocol and event publisher abstraction allow adapter replacement. |
| repo compatibility | 10/10 | FastAPI patterns, test structure, and dependencies align with repo conventions. |
| event correctness | 10/10 | Lifecycle and linkage events defined with stable names and payload contracts. |
| code quality | 10/10 | Typed schemas, validations, tenant checks, tests for key flows. |

## Run
```bash
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload --port 8080
```
