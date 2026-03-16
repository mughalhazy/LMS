# AI_04_learning_analytics_service

## Engineering + Implementation Prompt (Enterprise LMS V2)

You are implementing `learning_analytics_service` for Enterprise LMS V2.

Design and specify the service so it **extends existing LMS capabilities** while remaining fully compatible with these runtime entities owned elsewhere:

- `User`
- `Course`
- `Lesson`
- `Enrollment`
- `Progress`
- `Certificate`

## Service Mission

Build a tenant-safe analytics service that:

1. Aggregates learning events into derived analytics views.
2. Produces learner analytics.
3. Produces course analytics.
4. Produces cohort analytics.
5. Produces institution-level analytics.
6. Publishes analytics summaries for downstream AI consumers.

## Hard Constraints

- Analytics data is **derived** and never source-of-truth ownership for runtime entities.
- Do **not** mutate `Course`, `Lesson`, `Enrollment`, `Progress`, or `Certificate` directly.
- No shared database writes into other services.
- Tenant isolation is mandatory in storage, access control, querying, caching, and event publishing.

## Required Integrations

The service must integrate with:

- `event_ingestion_service`
- `progress_service`
- `assessment_service`
- `certificate_service`
- `ai_tutor_service`
- `recommendation_service`
- `skill_inference_service`

## Required Implementation Scope

Your implementation/spec must include all of the following:

- Versioned REST API (`/api/v1/...`).
- Analytics query endpoints.
- Analytics aggregation pipeline (ingest → normalize → aggregate → persist derived views).
- Tenant-aware request context and authorization guards.
- Audit logging for read/query and summary publish actions.
- Observability hooks (structured logs, metrics, traces, domain counters).
- Health endpoint (`/health` + dependency checks).
- Event publishing for analytics summaries where applicable.

---

## Deliverables (Provide in this exact order)

### 1) Service Module Structure

Provide a concrete folder/module layout covering at least:

- `app/main` or service bootstrap
- `api/routes`
- `api/schemas`
- `domain/models`
- `domain/services`
- `aggregation/pipeline`
- `integrations/clients`
- `events/publishers`
- `storage/repository`
- `observability`
- `audit`
- `tests/unit`, `tests/integration`, `tests/contract`

### 2) API Routes

Define versioned endpoints with method, path, purpose, auth scope, and tenancy rules. Include at least:

- `GET /api/v1/analytics/learners/{learnerId}`
- `GET /api/v1/analytics/courses/{courseId}`
- `GET /api/v1/analytics/cohorts/{cohortId}`
- `GET /api/v1/analytics/institutions/{institutionId}`
- `POST /api/v1/analytics/query`
- `GET /health`

Each route must define:

- required headers (`X-Tenant-Id`, `X-Request-Id`, auth token)
- pagination/filtering/sort semantics
- error model (`400`, `401`, `403`, `404`, `422`, `429`, `500`)

### 3) Request/Response Schemas

Define schema contracts for:

- Learner analytics response
- Course analytics response
- Cohort analytics response
- Institution analytics response
- Generic query request/response
- Error response envelope
- Audit metadata envelope

Include field types, nullability, enums, time windows, and tenant identifiers.

### 4) Domain Models

Define models for:

- `LearningEvent` (ingested reference)
- `LearnerAnalyticsSnapshot`
- `CourseAnalyticsSnapshot`
- `CohortAnalyticsSnapshot`
- `InstitutionAnalyticsSnapshot`
- `AnalyticsComputationJob`
- `AnalyticsSummaryEvent`

Clearly separate:

- source references (foreign IDs only)
- derived metrics
- lineage metadata (event source, computed_at, window)

### 5) Service Logic

Describe application services/use-cases for:

- on-demand analytics query execution
- pre-aggregated snapshot retrieval
- scheduled/stream aggregation triggers
- stale-data handling and backfill strategy
- tenant-aware access verification

Include anti-corruption boundaries for external services.

### 6) Aggregation Flow

Provide step-by-step flow:

1. Consume learning events from `event_ingestion_service`.
2. Enrich with progress/assessment/certificate projections via read-only calls.
3. Normalize to canonical analytics event format.
4. Aggregate by learner/course/cohort/institution + time bucket.
5. Persist derived snapshots in analytics-owned storage.
6. Emit analytics summary events for AI services.
7. Expose query APIs over derived snapshots.

Include idempotency strategy, late-arriving event handling, replay support, and deduplication keys.

### 7) Storage Contract

Define analytics-owned storage only (no cross-service writes), including:

- logical tables/collections
- primary keys and tenant partition keys
- retention and TTL policy
- materialized views/pre-aggregation strategy
- index strategy for query latency
- schema versioning and migration approach

### 8) Event Definitions

Define events emitted by this service, e.g.:

- `analytics.learner.summary.v1`
- `analytics.course.summary.v1`
- `analytics.cohort.summary.v1`
- `analytics.institution.summary.v1`

For each event include:

- topic/routing key
- payload schema
- required metadata (`tenant_id`, `trace_id`, `correlation_id`, `produced_at`, `schema_version`)
- delivery semantics and retry policy

### 9) Tests

Provide test plan and representative cases for:

- unit tests for metric computation correctness
- integration tests for external-service read adapters
- contract tests for API schemas and versioning
- tenancy isolation tests (cross-tenant access denied)
- idempotency/replay tests for aggregator
- observability tests (logs/metrics/traces emitted)
- performance checks for high-volume event windows

### 10) Migration Notes

Include migration and rollout notes:

- deployment order
- backfill strategy for historical analytics
- feature flags/canary rollout
- compatibility plan for existing consumers
- rollback strategy

---

## Output Format Requirements

Your response must be implementation-ready and include:

- explicit assumptions
- sequence diagrams or numbered flows (text form is acceptable)
- table-form API and event contracts
- pseudocode for aggregator core loop
- clear separation between required MVP and extensibility points

---

## QC LOOP (Run Iteratively Until Perfect)

Evaluate your own output against each category below and score from 1–10:

1. Analytics boundary correctness
2. Alignment with repo runtime entities
3. Data derivation correctness
4. Tenant safety
5. API quality
6. Observability completeness
7. AI compatibility
8. Extensibility

### QC Rules

- If **any score < 10**, you must:
  1. Identify the exact defect(s).
  2. Correct the implementation/spec.
  3. Re-run QC scoring.
- Repeat until **all categories score 10/10**.
- End with a final QC report showing each category = `10/10` and a brief rationale.

## Definition of Done

The prompt output is complete only when:

- all deliverables (1–10) are present,
- all hard constraints are satisfied,
- all integrations are represented via explicit interfaces,
- QC loop converges with all categories at `10/10`.
