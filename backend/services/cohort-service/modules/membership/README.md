# Cohort Membership Module

Implements cohort membership operations from `docs/specs/cohort_spec.md`:
- add learner to cohort
- remove learner from cohort
- bulk enrollment
- cohort membership listing

## Entities used
- `cohorts` (capacity checks and membership scope)
- `users` (learner existence validation)
- `cohort_memberships` (membership record lifecycle; introduced based on validation in `docs/data/data_model_validation.md`)

## API endpoints
- `POST /cohorts/:cohortId/memberships` - Add learner to cohort.
- `DELETE /cohorts/:cohortId/memberships/:learnerId` - Remove learner from cohort.
- `POST /cohorts/:cohortId/memberships:bulkEnroll` - Bulk membership assignment.
- `GET /cohorts/:cohortId/memberships` - List memberships with optional state and pagination.

## Notes
- Capacity overflow places learners into `waitlisted` state.
- Duplicate active assignments are skipped unless `overrideFlags.allow_duplicates` is true.
- Bulk enrollment returns assignment summary, conflict report, waitlist entries, and assigned records.
