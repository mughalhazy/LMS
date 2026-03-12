# Cohort Service

Implements tenant-scoped cohort management for LMS with:
- cohort creation
- lifecycle transitions
- membership assignment/removal with capacity-aware waitlisting
- tenant boundary enforcement
- cohort schedule planning and publication

## API Endpoints
- `POST /cohorts`
- `GET /cohorts?tenant_id={tenant_id}`
- `POST /cohorts/{cohort_id}/lifecycle`
- `POST /cohorts/{cohort_id}/members:assign`
- `POST /cohorts/{cohort_id}/members:remove`
- `POST /cohorts/{cohort_id}/schedule`

## Entities
- `Cohort`
- `CohortMembership`
- `AuditEvent`
- `CohortSchedule` / `CohortSession`

Mapped from specs:
- cohort statuses: `draft`, `scheduled`, `active`
- membership assignment conflict report and waitlisting
- tenant-scoped ownership and access checks
