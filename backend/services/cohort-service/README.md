# Cohort Service (Enterprise LMS V2)

Production-ready service supporting:
- formal cohorts
- academy-style batches
- tutor groups

## Responsibilities
- cohort lifecycle
- batch lifecycle
- program linkage
- cohort membership support
- cohort status and scheduling context

## Module structure
- `app/main.py` - versioned REST endpoints and health/metrics
- `app/schemas.py` - request/response contracts
- `app/models.py` - domain models
- `app/service.py` - business logic
- `app/store.py` - storage contract + in-memory adapter
- `app/audit.py` - audit logging abstraction
- `app/events.py` - event publishing abstraction
- `events/*.event.json` - lifecycle/program-link event definitions
- `schema.sql` - service-owned schema
- `MIGRATION_NOTES.md` - migration rollout

## API routes
- `POST /api/v1/cohorts`
- `POST /api/v1/batches`
- `GET /api/v1/cohorts`
- `GET /api/v1/cohorts/{cohort_id}`
- `PATCH /api/v1/cohorts/{cohort_id}`
- `POST /api/v1/cohorts/{cohort_id}/program-link`
- `POST /api/v1/cohorts/{cohort_id}/memberships`
- `DELETE /api/v1/cohorts/{cohort_id}/memberships/{membership_id}`
- `DELETE /api/v1/cohorts/{cohort_id}`
- `GET /health`
- `GET /metrics`

## Bounded-context guarantees
- No writes to enrollment/progress domains.
- Tenant-scoped access with mandatory `X-Tenant-ID` header.
- Event-driven integrations for lifecycle changes.
