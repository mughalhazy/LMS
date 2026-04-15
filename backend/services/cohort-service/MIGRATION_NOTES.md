# Cohort Service Migration Notes

## Scope
This service introduces a dedicated bounded context for cohort-like learner groupings:
- formal education cohorts
- academy batches
- tutor groups

## Data ownership boundaries
- Enrollment ownership remains in `enrollment-service`.
- Progress ownership remains in progress/analytics services.
- Cohort service writes only to its own `cohorts` and `cohort_memberships` tables.

## Suggested rollout steps
1. Create schema from `schema.sql` in the cohort-service datastore.
2. Backfill cohort structures from legacy LMS systems into `cohorts` and `cohort_memberships`.
3. Start dual publishing lifecycle events (`cohort.lifecycle.changed`, `cohort.program.linked`) for downstream consumers.
4. Switch read APIs in orchestrators/BFF to `/api/v1/cohorts` and `/api/v1/batches`.
5. Decommission legacy write paths after event lag and data parity checks.

## Compatibility notes
- `kind=academy_batch` enables academy-mode semantics while sharing storage and API shape.
- Tutor groups use `kind=tutor_group` with flexible role metadata in memberships.
- Program linkage is intentionally lightweight (`program_id`) and does not create enrollment records.
