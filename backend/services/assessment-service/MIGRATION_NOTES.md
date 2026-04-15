# Migration Notes - Assessment Service

## Objective
Introduce assessment lifecycle and attempt/submission domain without changing ownership of Course, Lesson, Progress, or Certificate domains.

## Steps
1. Deploy `assessment-service` as an independent microservice.
2. Register routes in API gateway under `/api/v1/assessments` and `/api/v1/attempts`.
3. Configure tenant context propagation header `X-Tenant-Id` in gateway/client middleware.
4. Wire event bus topics for:
   - `assessment.lifecycle_changed`
   - `assessment.attempt_started`
   - `assessment.submitted`
   - `assessment.graded`
5. Integrate grading pipeline to return `grading_result_id` and call `/api/v1/attempts/{attempt_id}/grade`.
6. Keep progress computation in Progress service; consume assessment events asynchronously for read-only progress updates.

## Data / Storage
- Current adapter is in-memory for local/runtime contract validation.
- Replace `InMemoryAssessmentStore` with a service-owned persistent store implementation.
- Do not write to other service databases.

## Compatibility
- No breaking change to existing services.
- New endpoints are additive and versioned under `/api/v1`.
