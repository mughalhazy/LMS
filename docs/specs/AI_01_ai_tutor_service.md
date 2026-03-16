# AI_01_ai_tutor_service — Engineering + Implementation Prompt (Enterprise LMS V2)

Use this prompt to generate and implement `ai_tutor_service` in the existing LMS repository.

---

## Prompt

Design and implement `ai_tutor_service` for **Enterprise LMS V2** as an assistive domain service that extends the current Rails LMS runtime model without replacing core entities.

### Core runtime entities (must remain canonical)
Do **not** replace or absorb ownership of:
- `User`
- `Course`
- `Lesson`
- `Enrollment`
- `Progress`
- `Certificate`

### Service responsibilities
`ai_tutor_service` must provide:
- learner question answering
- concept explanation
- lesson guidance
- practice generation
- context-aware tutoring

### Mandatory integrations
The service must integrate with:
- learning events
- learning analytics
- knowledge graph
- course + lesson context
- user progress context

### Implementation requirements
Include all of the following:
- versioned REST API
- tutor interaction endpoint
- context retrieval layer
- tenant-aware request context
- prompt/context assembly
- AI response logging
- audit logging
- observability hooks
- health endpoint
- event publishing for tutor interactions

### Deliverables (must be explicit)
Provide:
1. service module structure
2. API routes
3. request/response schemas
4. domain models
5. service logic
6. AI interaction flow
7. storage contract
8. event definitions
9. tests
10. migration notes

### Constraints
- do not own `Course`, `Lesson`, `Enrollment`, `Progress`, or `Certificate`
- do not replace instructor workflows
- AI remains assistive and is never source-of-truth
- no shared database writes
- all AI interactions must be auditable

### Required output format
Return a production-oriented implementation spec with concrete artifacts under a service path such as:
- `backend/services/ai-tutor-service/app/main.py`
- `backend/services/ai-tutor-service/app/routes.py`
- `backend/services/ai-tutor-service/app/schemas.py`
- `backend/services/ai-tutor-service/app/models.py`
- `backend/services/ai-tutor-service/app/context.py`
- `backend/services/ai-tutor-service/app/prompt_builder.py`
- `backend/services/ai-tutor-service/app/service.py`
- `backend/services/ai-tutor-service/app/store.py`
- `backend/services/ai-tutor-service/app/events.py`
- `backend/services/ai-tutor-service/src/audit.py`
- `backend/services/ai-tutor-service/src/observability.py`
- `backend/services/ai-tutor-service/tests/test_tutor_interaction_api.py`
- `backend/services/ai-tutor-service/tests/test_audit_and_events.py`
- `backend/services/ai-tutor-service/tests/test_context_assembly.py`
- `backend/services/ai-tutor-service/migrations/0001_ai_tutor_interactions.sql`

### API contract minimums
Use `/api/v1` namespace and define at least:
- `POST /api/v1/tutor/interactions`
- `GET /api/v1/tutor/interactions/{interaction_id}`
- `GET /api/v1/tutor/interactions` (tenant + learner-scoped query)
- `GET /health`
- `GET /metrics`

### Tutor interaction behavior
`POST /api/v1/tutor/interactions` should:
1. validate tenant/user/course/lesson/progress references through read-only adapters
2. retrieve context from:
   - lesson/course metadata
   - learner progress snapshot
   - recent learning events
   - knowledge graph concepts/prereqs
3. assemble a constrained, policy-safe prompt
4. invoke AI provider via adapter interface
5. return structured answer payload with:
   - direct answer
   - explanation depth
   - suggested next lesson activity
   - optional practice items
   - citations/reference pointers to LMS context inputs
6. persist immutable interaction log + prompt/response metadata
7. publish tutor interaction event
8. write audit trail
9. emit observability metrics/traces

### Storage and ownership rules
The service may own only tutor-assistive artifacts, for example:
- `ai_tutor_interaction`
- `ai_tutor_context_snapshot`
- `ai_tutor_feedback`
- `ai_tutor_audit_link`

It must not write to system-of-record tables for course delivery lifecycle.

### Event definitions (minimum)
Define and publish:
- `lms.ai_tutor.interaction.requested.v1`
- `lms.ai_tutor.interaction.responded.v1`
- `lms.ai_tutor.interaction.failed.v1`
- `lms.ai_tutor.feedback.recorded.v1`

Include event envelope fields:
- `event_id`, `event_type`, `occurred_at`
- `tenant_id`, `user_id`
- `interaction_id`
- `course_id`, `lesson_id` (nullable where appropriate)
- `trace_id`
- `schema_version`

### Auditability and compliance requirements
- immutable AI interaction log per request
- persisted prompt template version + context source fingerprints
- model/provider metadata (`provider`, `model`, `temperature`, token usage)
- actor metadata (`user_id`, `tenant_id`, client/app id)
- policy outcome flags (safety filters triggered, fallback used)
- correlation ids for cross-service tracing

### Tenant safety requirements
- every request scoped by `tenant_id`
- reject cross-tenant context fetches
- enforce tenant-scoped query filters in all read/write paths
- include tenant isolation tests (positive + negative)

### Testing requirements
Provide tests for:
- API happy path + validation failures
- tenant boundary enforcement
- context assembly correctness
- AI adapter timeout/failure fallback
- audit logging presence + immutability expectation
- event publishing and schema correctness
- observability hooks invocation
- health endpoint

### Migration notes requirements
Include:
- mapping back to existing Rails entities by reference ID only
- zero-downtime rollout strategy
- backfill policy for historical tutor interactions (if any)
- retention/archival policy for AI logs
- explicit statement: no shared DB writes into core LMS ownership domains

---

## QC LOOP

### QC Pass 1 (initial)
| Category | Score (1–10) | Defect identified |
|---|---:|---|
| service boundary correctness | 9 | Boundary was clear but did not explicitly list allowed owned tables for assistive data. |
| alignment with repo runtime entities | 10 | Correctly preserves User/Course/Lesson/Enrollment/Progress/Certificate ownership. |
| AI integration correctness | 9 | AI flow lacked explicit fallback behavior and provider adapter abstraction requirement. |
| auditability | 9 | Needed immutable logging and prompt/context fingerprint requirements called out explicitly. |
| tenant safety | 9 | Needed explicit negative tests and cross-tenant rejection requirements. |
| API quality | 10 | Versioned routes and endpoint set are concrete and implementable. |
| observability completeness | 9 | Needed explicit trace correlation and metrics endpoint requirement in flow. |
| extensibility | 9 | Needed clearer event envelope versioning and storage contract boundaries. |

### Corrections applied
- Added explicit owned-assistive artifact list and ownership prohibition statement.
- Added AI adapter abstraction + failure/timeout fallback testing requirements.
- Added immutable audit log requirements with prompt/context fingerprint fields.
- Added tenant negative-path requirements for context fetch and query filtering.
- Added observability correlation ID and `/metrics` obligations.
- Added event envelope versioning and trace fields.

### QC Pass 2 (after corrections)
| Category | Score (1–10) |
|---|---:|
| service boundary correctness | 10 |
| alignment with repo runtime entities | 10 |
| AI integration correctness | 10 |
| auditability | 10 |
| tenant safety | 10 |
| API quality | 10 |
| observability completeness | 10 |
| extensibility | 10 |

**QC LOOP RESULT:** all categories are **10/10**.
