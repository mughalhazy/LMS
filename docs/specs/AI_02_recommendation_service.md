# AI_02_recommendation_service

## Engineering + Implementation Prompt (Enterprise LMS V2)

Design and implement `recommendation_service` as an additive bounded-context service in the LMS runtime. The service must **extend** runtime capabilities and must **not replace** or absorb ownership of existing entities:

- `User`
- `Course`
- `Lesson`
- `Enrollment`
- `Progress`
- `Certificate`

`recommendation_service` is a decisioning and projection service that consumes learning signals, generates ranked recommendations, and serves traceable recommendation outputs.

---

## 1) Service Boundary and Responsibilities

### In scope
- Recommend next course.
- Recommend next lesson.
- Recommend practice activity.
- Recommend learning-path adjustments.
- Recommend remediation based on progress and assessments.

### Out of scope (hard constraints)
- Do not own `Course`, `Lesson`, `Enrollment`, `Progress`, or `Assessment` source-of-truth records.
- Do not mutate source-of-truth entities directly.
- Do not perform shared database writes into other services.
- Recommendations must remain explainable, traceable, and auditable.

### Integrations (must consume)
- Learning events.
- Learning analytics.
- User progress.
- Assessment outcomes.
- Knowledge graph.

---

## 2) Service Module Structure

Create the module as:

- `backend/services/recommendation-service/app/main.py`
- `backend/services/recommendation-service/app/routes.py`
- `backend/services/recommendation-service/app/schemas.py`
- `backend/services/recommendation-service/app/models.py`
- `backend/services/recommendation-service/app/service.py`
- `backend/services/recommendation-service/app/engine.py`
- `backend/services/recommendation-service/app/store.py`
- `backend/services/recommendation-service/app/clients.py`
- `backend/services/recommendation-service/app/events.py`
- `backend/services/recommendation-service/app/observability.py`
- `backend/services/recommendation-service/app/audit.py`
- `backend/services/recommendation-service/tests/test_routes.py`
- `backend/services/recommendation-service/tests/test_service.py`
- `backend/services/recommendation-service/tests/test_audit_and_events.py`
- `backend/services/recommendation-service/migrations/0001_create_recommendation_tables.sql`

Design for dependency inversion:
- Route layer -> service layer -> engine + store + integration clients.
- External dependencies (analytics/progress/assessment/knowledge-graph/event bus) behind interfaces.

---

## 3) Versioned API Routes

Base namespace: `/api/v1/recommendations`

- `POST /api/v1/recommendations/generate`
  - Generate recommendation set for a learner context.
- `GET /api/v1/recommendations/{recommendation_set_id}`
  - Retrieve a previously generated recommendation set.
- `GET /api/v1/recommendations/users/{user_id}/latest`
  - Retrieve latest active recommendation set.
- `POST /api/v1/recommendations/{recommendation_set_id}/feedback`
  - Record feedback (accepted, dismissed, completed).
- `GET /health`
  - Liveness/readiness.
- `GET /metrics`
  - Observability/telemetry endpoint.

All endpoints must require tenant-aware context:
- `X-Tenant-Id` (required)
- `X-Request-Id` (required)
- `X-Actor-Id` (optional)

---

## 4) Request/Response Schemas

Define schemas in `app/schemas.py`.

### Request Schemas
- `GenerateRecommendationRequest`
  - `user_id: str`
  - `target_scope: Literal["course", "lesson", "practice", "learning_path", "remediation", "all"]`
  - `context: dict[str, Any]` (optional)
  - `max_results: int` (default 10)
  - `force_refresh: bool` (default false)
- `RecommendationFeedbackRequest`
  - `recommendation_id: str`
  - `feedback_type: Literal["accepted", "dismissed", "completed", "not_relevant"]`
  - `reason: str | None`

### Response Schemas
- `RecommendationItemResponse`
  - `recommendation_id: str`
  - `recommendation_type: Literal["next_course", "next_lesson", "practice_activity", "learning_path_adjustment", "remediation"]`
  - `resource_ref: {resource_type: str, resource_id: str}`
  - `score: float`
  - `rank: int`
  - `rationale: list[str]`
  - `evidence_refs: list[str]`
  - `generated_at: datetime`
- `RecommendationSetResponse`
  - `recommendation_set_id: str`
  - `tenant_id: str`
  - `user_id: str`
  - `model_version: str`
  - `items: list[RecommendationItemResponse]`
  - `expires_at: datetime | None`
- `ErrorResponse`
  - `code: str`
  - `message: str`
  - `request_id: str`

---

## 5) Domain Models

Define in `app/models.py`:

- `RecommendationSet`
  - Identity and request context for one generation run.
- `RecommendationItem`
  - Ranked recommendation candidate with rationale + provenance.
- `RecommendationSignalSnapshot`
  - Frozen input signal references used for generation.
- `RecommendationFeedback`
  - Learner or system feedback on recommendation usefulness.
- `RecommendationAuditLog`
  - Immutable audit record for generation/retrieval/feedback actions.

Model rules:
- Every record keyed by `(tenant_id, id)`.
- Immutable generation inputs persisted per set (`signal_snapshot_hash`, `input_refs`).
- Soft expiry support for stale sets.

---

## 6) Service Logic

Implement orchestration in `app/service.py` and ranking in `app/engine.py`.

### Generation flow
1. Validate tenant and request shape.
2. Pull integration data (events, analytics, progress, assessments, knowledge graph).
3. Build normalized learner state vector.
4. Create candidate pools by recommendation type.
5. Score and rank candidates (pluggable strategies).
6. Attach rationale and evidence references.
7. Persist recommendation set + items + signal snapshot.
8. Write audit record.
9. Publish generation event.
10. Return response envelope.

### Retrieval flow
1. Validate tenant and access scope.
2. Fetch recommendation set by id or latest by user.
3. Ensure not cross-tenant and not expired (unless requested with debug role).
4. Emit retrieval audit log and telemetry.
5. Return set.

### Feedback flow
1. Validate recommendation set ownership and tenant.
2. Persist feedback without mutating source entities.
3. Publish feedback event.
4. Record audit + metrics.

---

## 7) Recommendation Flow (End-to-End)

Input signals:
- Learning event recency/frequency.
- Progress velocity and blockage points.
- Assessment outcomes (scores, objective-level misses).
- Knowledge graph dependencies/prerequisites.
- Tenant policy constraints (available catalog, compliance tracks).

Decision branches:
- If prerequisite gaps are detected -> prioritize remediation + practice.
- If course completed and progression path exists -> recommend next course/lesson.
- If repeated failures on same concept -> recommend targeted practice activity.
- If path drift detected -> recommend learning-path adjustment.

Output quality controls:
- De-duplicate equivalent recommendations.
- Enforce catalog visibility and entitlement filters.
- Include minimum one explanation string per item.
- Include evidence references for every recommendation.

---

## 8) Storage Contract

Implement protocol in `app/store.py`.

### Required methods
- `save_recommendation_set(set: RecommendationSet, items: list[RecommendationItem], snapshot: RecommendationSignalSnapshot) -> None`
- `get_recommendation_set(tenant_id: str, recommendation_set_id: str) -> RecommendationSet | None`
- `get_latest_recommendation_set(tenant_id: str, user_id: str) -> RecommendationSet | None`
- `save_feedback(feedback: RecommendationFeedback) -> None`
- `append_audit_log(entry: RecommendationAuditLog) -> None`
- `list_recommendation_items(tenant_id: str, recommendation_set_id: str) -> list[RecommendationItem]`

### Data ownership
- recommendation-service owns only recommendation tables/collections.
- No writes to course/progress/assessment/enrollment databases.
- External entities referenced via foreign IDs only.

---

## 9) Event Definitions

Define in `app/events.py` and publish via event bus client.

### Produced events
- `lms.ai.recommendation.generated.v1`
  - payload: tenant_id, user_id, recommendation_set_id, target_scope, model_version, item_count, generated_at.
- `lms.ai.recommendation.feedback_recorded.v1`
  - payload: tenant_id, user_id, recommendation_set_id, recommendation_id, feedback_type, occurred_at.
- `lms.ai.recommendation.failed.v1`
  - payload: tenant_id, user_id, failure_code, request_id, occurred_at.

### Consumed events (examples)
- `lms.progress.lesson_completed.v1`
- `lms.progress.course_progress_updated.v1`
- `lms.assessment.submitted.v1`
- `lms.analytics.snapshot_updated.v1`
- `lms.learning.event_recorded.v1`

---

## 10) Observability + Auditability

### Observability hooks
- Traces:
  - `recommendation.generate`
  - `recommendation.retrieve`
  - `recommendation.feedback`
- Metrics:
  - generation latency histogram
  - recommendations generated counter
  - retrieval hit/miss counter
  - feedback acceptance/dismissal counters
  - upstream integration error counters
- Structured logs:
  - include tenant_id, request_id, user_id, recommendation_set_id.

### Audit logging
For every generate/retrieve/feedback action, persist immutable audit entries with:
- actor identity (if present)
- tenant_id
- action name
- timestamp
- request_id
- target recommendation ids
- before/after metadata (where applicable)

Audit logs must be queryable by tenant and date range.

---

## 11) Tests

Create test coverage for:

- API contract tests for versioned routes and schema validation.
- Tenant isolation tests (cross-tenant access forbidden).
- Recommendation generation quality gates:
  - prerequisite gap -> remediation recommendation exists.
  - completion progression -> next course/lesson prioritized.
- Feedback persistence and event emission tests.
- Audit log completeness tests.
- Observability hook invocation tests.
- Failure-path tests for upstream integration timeout/degraded response.

Minimum expectation:
- unit tests for service/engine/store boundaries.
- integration-style tests for route + service + fake store.

---

## 12) Migration Notes

- Introduce recommendation-service as a new bounded context without changing ownership of existing LMS entities.
- Map source-of-truth dependencies via read-only clients/adapters.
- Backfill strategy:
  - optional background generation for active learners.
  - no backfill writes to progress/enrollment/course services.
- Rollout strategy:
  - dark launch generation + logging first.
  - then expose retrieval API.
  - then enable feedback ingestion and adaptive ranking updates.
- Ensure compatibility with existing event taxonomy and API versioning conventions.

---

## 13) Implementation Guardrails

- Keep recommendation engine strategy-based (`RuleBasedStrategy`, `HybridStrategy`, future `MLStrategy`).
- Isolate feature extraction from ranking to allow experimentation.
- Persist model/strategy version per recommendation set.
- Enforce idempotency on generation requests with `(tenant_id, user_id, target_scope, request_hash)`.
- Never leak data across tenants.

---

## 14) QC LOOP (Iterate Until 10/10)

### QC Pass 1
| Category | Score | Defect |
|---|---:|---|
| service boundary correctness | 9 | Initial draft lacked explicit prohibition on source-of-truth mutation and shared writes. |
| alignment with repo runtime entities | 9 | Needed explicit statement of extension-only behavior for User/Course/Lesson/Enrollment/Progress/Certificate entities. |
| recommendation quality architecture | 9 | Needed stronger decision-branch criteria and evidence-backed rationale requirements. |
| auditability | 9 | Audit schema needed immutable action log requirements for retrieval and feedback, not only generation. |
| tenant safety | 9 | Needed mandatory tenant headers and `(tenant_id, id)` keying rule. |
| API quality | 9 | Needed fully versioned routes for generate/retrieve/feedback + error envelope. |
| observability completeness | 9 | Needed specific traces/metrics/log dimensions. |
| future extensibility | 9 | Needed strategy-based engine with model_version persistence and idempotency keying. |

### Corrections Applied
- Added hard constraints on entity ownership, no shared writes, and no direct source mutation.
- Added explicit extension compatibility with existing runtime entities.
- Added decision-branch logic and rationale/evidence requirements.
- Added immutable, queryable audit logging for generate/retrieve/feedback.
- Added strict tenant-aware request context and keying conventions.
- Added complete versioned API surface with health and metrics endpoints.
- Added trace/metric/log hook requirements.
- Added pluggable strategy architecture, model version persistence, and idempotency contract.

### QC Pass 2
| Category | Score |
|---|---:|
| service boundary correctness | 10 |
| alignment with repo runtime entities | 10 |
| recommendation quality architecture | 10 |
| auditability | 10 |
| tenant safety | 10 |
| API quality | 10 |
| observability completeness | 10 |
| future extensibility | 10 |

**QC target achieved: all categories are 10/10.**
