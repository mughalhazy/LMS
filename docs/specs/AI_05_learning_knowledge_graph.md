# AI_05_learning_knowledge_graph

## Engineering + Implementation Prompt (Enterprise LMS V2)

You are implementing the **Learning Knowledge Graph** component for Enterprise LMS V2.

### Objective
Build a **derived intelligence graph layer** around existing LMS runtime entities and V2 structural entities to power AI tutoring, recommendations, and skill inference.

### Runtime entities to wrap (existing ownership remains unchanged)
- Course
- Lesson
- Assessment
- Certificate

### V2 structural entities to represent
- Program
- Cohort
- Session
- Concept
- Skill

---

## 1) Architecture and boundary rules

### Hard constraints
- The graph is a **derived intelligence layer**, not source-of-truth for Course, Lesson, Assessment, or Certificate.
- Do not replace repository runtime ownership of domain entities.
- Graph updates must be traceable with provenance.
- No shared database writes into source runtime services.

### Responsibilities
- Represent concept relationships.
- Represent skill relationships.
- Map lessons to concepts.
- Map assessments to concepts.
- Map credentials to skills.
- Support AI tutor, recommendation, and skill inference services via query interface.

---

## 2) Deliverables (must be implemented)

1. Graph schema.
2. Node definitions.
3. Edge definitions.
4. Update rules.
5. Consumer query contract.
6. Storage/update contract.
7. Tests.
8. Migration notes.

---

## 3) Graph schema definition

Define a versioned schema (`schema_version`) that includes:

### Required node types
- `ProgramNode`
- `CohortNode`
- `SessionNode`
- `CourseNode`
- `LessonNode`
- `AssessmentNode`
- `CertificateNode`
- `ConceptNode`
- `SkillNode`

### Required edge types
- `PROGRAM_CONTAINS_COURSE`
- `COHORT_RUNS_PROGRAM`
- `SESSION_DELIVERS_COURSE`
- `COURSE_CONTAINS_LESSON`
- `LESSON_TEACHES_CONCEPT`
- `CONCEPT_PREREQUISITE_OF_CONCEPT`
- `CONCEPT_RELATES_TO_CONCEPT`
- `ASSESSMENT_TESTS_CONCEPT`
- `SKILL_PREREQUISITE_OF_SKILL`
- `CONCEPT_SUPPORTS_SKILL`
- `CERTIFICATE_VALIDATES_SKILL`

### Required common metadata (nodes + edges)
- `tenant_id`
- `entity_id`
- `entity_version`
- `is_active`
- `created_at`
- `updated_at`
- `source_system`
- `source_event_id`
- `source_event_ts`
- `schema_version`

---

## 4) Node definitions

For each node type define:
- Stable identity key (`node_id`, `entity_id`, `tenant_id`).
- Domain reference (`source_table`, `source_service`, `source_pk`).
- Human-readable attributes (title/name/description where relevant).
- Status/lifecycle fields (`status`, `effective_from`, `effective_to` where relevant).
- Governance/provenance fields (`confidence`, `attribution`, `review_state` for AI-inferred links only).

Minimum node payload contracts:
- `CourseNode`: title, status, level, modality.
- `LessonNode`: title, order_index, duration_minutes.
- `AssessmentNode`: assessment_type, max_score, pass_threshold.
- `CertificateNode`: certificate_type, issuer, validity_window.
- `ConceptNode`: taxonomy_path, cognitive_level.
- `SkillNode`: framework, level, proficiency_scale.
- `Program/Cohort/Session`: schedule + lifecycle alignment fields.

---

## 5) Edge definitions

For each edge type define:
- `from_node_id`, `to_node_id`, `edge_type`, `tenant_id`.
- Weighting semantics where applicable (`weight`, `coverage_weight`, `relevance_weight`).
- Temporal semantics (`effective_from`, `effective_to`).
- Provenance and version.

### Relationship-specific requirements
- `LESSON_TEACHES_CONCEPT`: include `coverage_weight` and `instruction_depth`.
- `ASSESSMENT_TESTS_CONCEPT`: include `measurement_weight` and `measurement_type`.
- `CERTIFICATE_VALIDATES_SKILL`: include `required_level`, `validation_strength`.
- `CONCEPT_PREREQUISITE_OF_CONCEPT` and `SKILL_PREREQUISITE_OF_SKILL`: must remain acyclic (validate DAG rules).

---

## 6) Graph update pipeline

Implement pipeline stages:

1. **Ingest** domain events from source services (course/lesson/assessment/certificate/program/cohort/session).
2. **Normalize** payload into canonical graph update DTOs.
3. **Validate** tenant, schema, referential integrity, version ordering.
4. **Resolve conflicts** via monotonic version/timestamp policy.
5. **Upsert** nodes/edges idempotently.
6. **Emit audit record** for every mutation.
7. **Emit observability metrics/traces/logs** for each stage.
8. **Reconcile** with scheduled backfill job for drift correction.

Pipeline behavior requirements:
- Idempotency key: `tenant_id + source_event_id + schema_version`.
- Out-of-order handling: reject stale updates, record audit reason.
- Soft-delete handling: mark `is_active=false` instead of hard delete for replayability.
- Dead-letter queue path for invalid events.

---

## 7) Tenant-aware graph partitioning/scoping

Implement one:
- Physical partition per tenant, or
- Logical partition with strict tenant filters and row-level access guards.

Mandatory safeguards:
- Every write path requires explicit `tenant_id`.
- Every read/query API enforces tenant predicate first.
- Cross-tenant traversal is disallowed by default.
- Multi-tenant load tests validate isolation.

---

## 8) Query interface for AI consumers

Provide a stable query contract for AI tutor/recommendation/inference consumers.

### Required query operations
- `get_concept_graph(course_id | lesson_id)`
- `get_skill_graph(skill_id | certificate_id)`
- `get_lesson_concept_map(lesson_ids[])`
- `get_assessment_concept_map(assessment_ids[])`
- `get_certificate_skill_map(certificate_ids[])`
- `infer_skill_readiness(learner_evidence)`
- `recommend_next_concepts(learner_context)`

### Query contract requirements
- Tenant-scoped request envelope (`tenant_id`, `request_id`, `actor_context`).
- Explainability payload (`reasoning_path`, `edge_weights_used`, `evidence_refs`).
- Version metadata (`graph_snapshot_version`, `as_of_ts`).
- Pagination/limits and deterministic ordering.

---

## 9) Storage/update contract

Define interfaces (language-idiomatic protocol/abstract classes):
- `GraphStore`
- `GraphUpdater`
- `GraphQueryService`
- `GraphAuditSink`

Required methods:
- `upsert_node(node_record)`
- `upsert_edge(edge_record)`
- `deactivate_node(node_id, reason)`
- `deactivate_edge(edge_id, reason)`
- `query_subgraph(query_spec)`
- `record_audit(audit_record)`
- `health_status()`

Contract guarantees:
- Idempotent upserts.
- Optimistic concurrency with entity version checks.
- Tenant isolation invariants.
- No direct writes into upstream runtime service stores.

---

## 10) Audit logging for graph updates

Audit record must include:
- `audit_id`, `tenant_id`, `mutation_type`, `node_or_edge_type`, `entity_id`.
- Before/after hashes.
- `source_event_id`, `source_system`, `actor_type` (system/human).
- Mutation outcome (`applied`, `rejected_stale`, `rejected_invalid`, `noop_idempotent`).
- Timestamp and correlation IDs.

Retention and replay:
- Keep immutable audit stream.
- Support replay by `tenant_id` and time window.

---

## 11) Observability hooks + health endpoint

### Observability
Add:
- Structured logs at each pipeline stage.
- Metrics:
  - ingest throughput
  - update latency
  - stale-event rejection count
  - idempotent noop count
  - tenant-isolation violation count (must remain zero)
  - query p95/p99 latency
- Distributed traces across ingest → update → query.

### Health endpoint
Expose `/health` with:
- dependency checks (store, queue, audit sink)
- latest successful update timestamp
- lag metrics (event lag, reconciliation lag)
- status summary (`ok`, `degraded`, `down`)

---

## 12) Tests (required)

Implement test suites:

1. **Schema tests**: node/edge validation, required metadata enforcement.
2. **Pipeline tests**: idempotency, out-of-order rejection, DLQ routing, soft-delete behavior.
3. **Tenant isolation tests**: cross-tenant read/write denial.
4. **Query contract tests**: response shape, explainability fields, pagination determinism.
5. **Audit tests**: complete audit payload on applied + rejected mutations.
6. **Observability tests**: metrics increments and trace propagation.
7. **Health tests**: dependency failure and degraded-state reporting.
8. **Migration tests**: backward-compatible schema evolution.

---

## 13) Migration notes (required)

Document:
- Initial bootstrap strategy from existing runtime entities.
- Event backfill cutover strategy.
- Dual-run period (legacy intelligence output vs graph-driven output).
- Rollback strategy if graph quality regression occurs.
- Schema evolution policy (`vN -> vN+1`) with replay compatibility.

---

## 14) Definition of done

Done only when:
- All required node/edge contracts are implemented.
- Update pipeline, query APIs, audit, observability, and health endpoint are complete.
- Test suites pass.
- Migration notes are published.
- Constraints are explicitly validated in tests/documentation.

---

## 15) QC LOOP (must execute until all 10/10)

Evaluate implementation and score each category 1–10:

- graph usefulness for AI
- alignment with repo runtime entities
- correctness of derived-data role
- tenant safety
- query interface quality
- observability completeness
- maintainability
- future extensibility

### QC execution rule
If any category is < 10:
1. Identify the defect precisely.
2. Correct implementation/docs/tests.
3. Re-run QC scoring.
4. Repeat until all categories are 10/10.

### QC exit condition
All categories = **10/10** with defects resolved and verified by tests.
