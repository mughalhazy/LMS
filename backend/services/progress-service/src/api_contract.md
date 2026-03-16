# Progress Service API Endpoints (v1)

Base path: `/api/v1/progress`

## Health and observability
- `GET /health`
- `GET /metrics`

## Upsert lesson progress
- `POST /api/v1/progress/lessons/{lesson_id}/upsert`
- Idempotent write using `idempotency_key`
- Requires tenant context in both payload and `X-Tenant-Id`
- Returns canonical Progress response with `learner_id` and `user_id` alias

## Complete lesson
- `POST /api/v1/progress/lessons/{lesson_id}/complete`
- Forces lesson progress to `completed` with `progress_percentage=100`
- Recomputes and persists course progression snapshot
- Emits lesson + progress lifecycle events

## Get learner summary
- `GET /api/v1/progress/learners/{learner_id}?tenant_id={tenant_id}`
- Returns tenant-scoped course/lesson/path projections

## Get course progress
- `GET /api/v1/progress/learners/{learner_id}/courses/{course_id}?tenant_id={tenant_id}`
- Returns course completion state and metrics

## Assign learning path context
- `POST /api/v1/progress/learning-paths/{learning_path_id}/assignments`
- Stores path assignment context for path-level progression rollups

## Error semantics
- `400 tenant_mismatch` when `X-Tenant-Id` differs from requested tenant
- `404 course_progress_not_found` when no course projection exists
- `409 enrollment_not_active` when enrollment gateway denies progress mutation
