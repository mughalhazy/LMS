# Progress Service Migration Notes

## Objective
Move progress ownership from Rails monolith write paths to `progress-service` while preserving existing `Progress` semantics (`progress_id`, `enrollment_id`, `user_id/learner_id`, `course_id`, optional `lesson_id`, `percent_complete`, `status`, `last_activity_at`).

## Storage compatibility
- Keep `progress_records` as authoritative store in this service boundary.
- Store enrollment and assessment references only; never copy ownership.
- Avoid shared DB writes: integrations happen through APIs/events.

## Rollout plan
1. **Dual-read phase**: consumers compare service projections with Rails Progress reads.
2. **Dual-write adapter phase**: writes call `POST /api/v1/progress/lessons/{lesson_id}/upsert` while legacy path remains fallback.
3. **Event parity gate**: validate `progress.updated` and `progress.completed` payload parity.
4. **Cutover**: disable legacy writes; service becomes sole progress writer.
5. **Cleanup**: retire legacy progress mutation code after audit signoff.

## Backward compatibility
- Response/event payloads include `learner_id` and `user_id` aliasing.
- Idempotency key support ensures safe retries from legacy workers.

## Operational checks
- Validate tenant-context match (`X-Tenant-Id`) in all mutating calls.
- Monitor `/metrics` counters:
  - `progress.write.attempt`
  - `progress.write.success`
  - `progress.write.idempotent_hit`
- Monitor `409 enrollment_not_active` rates for integration drift.
