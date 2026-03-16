# AI_03_skill_inference_service — Engineering + Implementation Prompt (Enterprise LMS V2)

Use the following prompt verbatim when generating the `skill_inference_service` implementation package.

---

You are a senior principal engineer implementing `skill_inference_service` for **Enterprise LMS V2**.

## Objective
Build an AI-compatible **skill inference layer** that augments the LMS with derived learner skill intelligence **without replacing or mutating runtime ownership** of:
- `User`
- `Course`
- `Lesson`
- `Enrollment`
- `Progress`
- `Certificate`

## Core responsibilities
The service must:
1. infer learner skills
2. infer skill progression over time
3. map assessment outcomes to skills
4. map lesson completion to skill signals
5. produce learner skill profiles

## Required integrations
The service must integrate with:
- learning events
- assessment results
- progress records
- knowledge graph
- recommendation service

## Hard constraints (must enforce)
1. **Do not own assessment results** (read/subscribe only).
2. **Do not own progress records** (read/subscribe only).
3. Inferred skills are **derived data**, never source-of-truth completion status.
4. **No shared database writes** into other service-owned datastores.
5. All inference outputs must be **explainable** and **auditable**.
6. Must be **tenant-safe** in all API, storage, logs, metrics, traces, and events.

## Implementation requirements
Produce a complete service slice with:
- versioned REST API
- skill inference endpoint
- skill profile retrieval endpoint
- tenant-aware request context
- audit logging
- observability hooks (logs/metrics/traces)
- health endpoint
- event publishing for inference outputs

## Deliverables (must be explicit)
1. service module structure
2. API routes
3. request/response schemas
4. domain models
5. service logic
6. inference flow
7. storage contract
8. event definitions
9. tests
10. migration notes

## Engineering standards
- Python + FastAPI-style service patterns consistent with repo services.
- Explicit separation of layers (`app/main.py`, `schemas`, `models`, `service`, `store`, `tests`, `migrations`).
- Typed schemas and deterministic error envelopes.
- Idempotent inference behavior for repeated input/event replay.
- Explainability payload must include evidence references, rule/model version, and confidence details.
- Audit logs must include: tenant_id, actor/source, input references, inference version, output summary, and trace/correlation IDs.
- Observability must include:
  - request latency + error metrics by endpoint and tenant
  - inference duration histogram
  - event publish success/failure counters
  - trace spans for ingestion → inference → persistence → publish

## Target module shape (proposed)
- `backend/services/skill-inference-service/app/main.py`
- `backend/services/skill-inference-service/app/schemas.py`
- `backend/services/skill-inference-service/app/models.py`
- `backend/services/skill-inference-service/app/service.py`
- `backend/services/skill-inference-service/app/store.py`
- `backend/services/skill-inference-service/src/audit.py`
- `backend/services/skill-inference-service/src/observability.py`
- `backend/services/skill-inference-service/src/events.py`
- `backend/services/skill-inference-service/tests/test_skill_inference_api.py`
- `backend/services/skill-inference-service/tests/test_skill_inference_service.py`
- `backend/services/skill-inference-service/tests/test_audit_and_events.py`
- `backend/services/skill-inference-service/migrations/0001_create_skill_inference_tables.sql`

## API contract requirements
Version namespace: `/api/v1`.

Minimum endpoints:
1. `POST /api/v1/skills/infer`
   - Triggers inference for a learner (optionally scoped by course/lesson/time window).
   - Must support idempotency key.
2. `GET /api/v1/skills/users/{user_id}/profile`
   - Returns current learner skill profile + progression + explainability metadata.
3. `GET /health`
   - Liveness/readiness signal.

Optional but recommended:
- `GET /api/v1/skills/users/{user_id}/evidence`
- `GET /metrics`

## Data + model expectations
Define clear models for:
- `SkillInferenceRun`
- `UserSkillProfile`
- `SkillProficiency`
- `SkillEvidence`
- `SkillProgressionSnapshot`
- `InferenceExplanation`

Ensure each model includes:
- tenant keying
- provenance metadata
- versioning metadata
- audit timestamps

## Event contract expectations
Publish at least:
- `lms.ai.skill_inference.completed.v1`
- `lms.ai.skill_profile.updated.v1`
- `lms.ai.skill_gap.detected.v1` (when applicable)

Event payloads must include:
- tenant_id
- learner/user id
- inference_run_id
- model/rule version
- top inferred skills with confidence
- explainability/evidence references
- correlation + causation identifiers

## Inference flow expectations
Define end-to-end flow:
1. collect upstream references (events/results/progress/graph)
2. validate tenant and access scope
3. normalize evidence
4. perform inference/scoring
5. produce explainable output
6. persist derived profile + run record
7. emit domain events
8. write audit record
9. expose retrieval via profile endpoint

Include failure handling for:
- missing upstream data
- partial inference completion
- event bus publish failure (with retry/dead-letter strategy)

## Migration notes expectations
Document:
- how this coexists with existing runtime entities
- no ownership transfer from progress/assessment services
- backfill/recompute strategy for existing learners
- rollback strategy for inference model/rule versions
- tenant-safe data retention and deletion behavior

## Testing expectations
Provide tests for:
- API validation + error envelopes
- tenant isolation
- idempotent inference execution
- explainability payload completeness
- audit log coverage
- event publication coverage
- observability instrumentation calls
- boundary integrity (no writes into non-owned stores)

## Output format required from implementation
Return a single structured document with these sections:
1. Service module structure
2. API routes
3. Schemas
4. Domain models
5. Service logic
6. Inference flow
7. Storage contract
8. Events
9. Tests
10. Migration notes
11. QC LOOP report

## QC LOOP (mandatory, iterative)
Evaluate and score each category from **1–10**:
1. service boundary correctness
2. alignment with repo runtime entities
3. skill inference design quality
4. auditability
5. tenant safety
6. API quality
7. observability completeness
8. maintainability

If **any score < 10**:
- identify the exact defect
- correct the implementation/design
- rerun QC
- repeat until **all categories are 10/10**

Do not finalize output until QC target is met.

---

## Suggested acceptance checklist
- [ ] No runtime entity ownership violations.
- [ ] All API endpoints versioned and tenant-aware.
- [ ] Every inference output has explainability + audit trail.
- [ ] Events include required metadata and are published reliably.
- [ ] Tests cover boundary, tenancy, explainability, and observability.
- [ ] QC LOOP ends with all categories 10/10.
