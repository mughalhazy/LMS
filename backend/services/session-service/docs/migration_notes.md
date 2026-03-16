# Session Service Migration Notes

## Goal
Introduce `session_service` as the delivery-instance owner around existing course and lesson runtime objects.

## Data migration strategy
1. Backfill session records from legacy scheduling payloads into `Session` aggregate rows.
2. Persist only foreign references for `course_id`, `lesson_id`, and `cohort_ids`.
3. Do **not** copy course/lesson content trees or enrollment contracts.
4. Initialize `status` as `scheduled` only when a valid schedule exists; otherwise `draft`.
5. Seed optimistic concurrency `version = 1` and write `session.created.v1` for imported rows.

## API rollout
1. Launch `/api/v2/sessions` in parallel with legacy schedule endpoints.
2. Mirror schedule writes into session events (`session.scheduled.v1`, `session.rescheduled.v1`).
3. Migrate consumers (notifications, analytics, academy calendar) to lifecycle events.
4. Deprecate legacy endpoints after consumers confirm parity.

## Operational checks
- Verify tenant isolation by querying session IDs across tenant boundaries.
- Confirm event throughput and dead-letter policy for all session lifecycle event types.
- Ensure observability dashboards include request latency, transition counts, and schedule failures.
