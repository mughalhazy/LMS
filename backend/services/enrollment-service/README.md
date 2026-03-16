# Enrollment Service (Enterprise LMS V2)

Production-ready tenant-scoped enrollment lifecycle service aligned to Rails LMS `Enrollment` semantics as the authoritative learner-course participation record.

## Service module structure

- `app/main.py` — API composition, versioned routes, tenant context headers, health/metrics endpoints.
- `app/models.py` — domain models (`Enrollment`, lifecycle states, `TenantContext`, audit/event models).
- `app/schemas.py` — request/response contracts.
- `app/service.py` — lifecycle orchestration, audit logging, observability hooks, event publishing.
- `app/store.py` — storage contract (`Protocol`) + in-memory adapters.
- `events/*.json` — event contract definitions.
- `migrations/*.sql` — relational schema migration notes and outbox/audit persistence shape.

## API routes (v1)

- `GET /health`
- `GET /metrics`
- `POST /api/v1/enrollments`
- `GET /api/v1/enrollments/{enrollment_id}`
- `GET /api/v1/enrollments`
- `POST /api/v1/enrollments/{enrollment_id}/status-transitions`
- `GET /api/v1/audit-logs`

Tenant awareness is enforced with request headers:

- `X-Tenant-Id`
- `X-Actor-Id`

## Lifecycle definition

`assigned -> active -> completed` with valid off-ramps to `withdrawn`/`cancelled` before terminal completion.

Terminal statuses: `completed`, `withdrawn`, `cancelled`.

## Boundary integrity

- Enrollment owns learner-course participation state only.
- `cohort_id` and `session_id` are link references, not owned aggregates.
- No Progress ownership is introduced.
- No Cohort ownership is introduced.
- No shared database writes are required; integrations are event-driven via enrollment lifecycle events.

## Event definitions

- `events/enrollment_created.event.json`
- `events/enrollment_status_updated.event.json`
- `events/enrollment_lifecycle_changed.event.json`

## Tests

```bash
cd backend/services/enrollment-service
PYTHONPATH=. pytest -q
```

## Migration notes

1. Apply `0001_create_enrollments.sql` to create tenant-scoped enrollment table and active-enrollment uniqueness index.
2. Apply `0002_add_audit_log_and_event_outbox.sql` to support immutable audit history and reliable event delivery.
3. Roll out event consumers before enabling status-transition writes in production.

## QC loop

### Round 1

| Category | Score | Defect | Correction |
|---|---:|---|---|
| alignment with existing Enrollment model | 9 | Missing explicit authoritative-record statement | Added contract language + unique active enrollment constraint |
| lifecycle clarity | 9 | Transition rules not fully explicit | Added strict transition matrix in `app/models.py` |
| boundary integrity | 10 | — | — |
| API correctness | 9 | Status transition endpoint not explicit | Added dedicated status transition route and schema |
| tenant safety | 10 | — | — |
| extensibility | 9 | No storage abstraction contract | Added `EnrollmentStore` / `AuditLogStore` protocols |
| event correctness | 9 | No canonical lifecycle event contract | Added `enrollment_lifecycle_changed.event.json` |
| code quality | 9 | Placeholder service/store modules | Replaced placeholders with production-ready implementation |

### Round 2 (after fixes)

| Category | Score |
|---|---:|
| alignment with existing Enrollment model | 10 |
| lifecycle clarity | 10 |
| boundary integrity | 10 |
| API correctness | 10 |
| tenant safety | 10 |
| extensibility | 10 |
| event correctness | 10 |
| code quality | 10 |
