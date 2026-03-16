# DATA 07: AI Interaction Schema (Enterprise LMS V2)

## Objective
Define a tenant-safe, auditable, and extensible AI interaction data schema supporting:
- AI tutor conversations
- recommendation generation
- skill inference outputs
- course generation requests

This schema is designed to integrate with existing LMS V2 entities: `User`, `Course`, `Lesson`, `Enrollment`, and `Progress`.

## Design Principles
- **Tenant-first isolation**: all records carry `tenant_id` and are query-scoped by tenant.
- **Service isolation**: AI services own AI tables; cross-domain entities are linked by immutable foreign IDs and snapshots, not hard business coupling.
- **Auditability by default**: every request/response pair is traceable, reproducible, and hash-verifiable.
- **Safety and minimal exposure**: prompt payloads store redacted references where possible; sensitive raw content is encrypted and access-controlled.
- **Extensibility**: nullable domain anchors and JSON metadata allow new AI use cases without schema breaks.

## Entity Definitions

### 1) AI Interaction
**Purpose**
- Canonical envelope for one AI-driven workflow instance (e.g., tutor turn, recommendation run, skill inference job, course generation session).

**Required fields**
- `ai_interaction_id` (UUID, PK)
- `tenant_id` (UUID, required)
- `interaction_type` (enum: `tutor_conversation`, `recommendation_generation`, `skill_inference`, `course_generation`)
- `status` (enum: `received`, `processing`, `completed`, `failed`, `partially_completed`)
- `initiated_by_user_id` (UUID, FK -> `User.user_id`)
- `created_at`, `updated_at` (timestamp)
- `trace_id` (string, distributed trace correlation)

**Relationships**
- 1:N with `AI Request`
- 1:N with `AI Response`
- 1:N with `Recommendation Record`
- 1:N with `Skill Inference Record`
- 1:N with `Prompt Context`
- N:1 logical link to `User`
- Optional contextual links to `Course`, `Lesson`, `Enrollment`, `Progress` via anchor IDs on child entities

**Retention requirements**
- Retain envelope for **24 months** minimum for operational and compliance traceability.
- Soft-delete not allowed; use lifecycle states + archival storage.

**Audit requirements**
- Immutable audit trail for status transitions (`from_status`, `to_status`, actor/service, timestamp).
- Record `trace_id` and calling service identity for each state change.

---

### 2) AI Request
**Purpose**
- Stores each concrete request sent to an AI model/provider within an interaction.

**Required fields**
- `ai_request_id` (UUID, PK)
- `ai_interaction_id` (UUID, FK -> `AI Interaction`)
- `tenant_id` (UUID, required)
- `request_sequence` (int, required; unique per interaction)
- `request_type` (enum: `chat_turn`, `recommendation_query`, `skill_inference_query`, `course_generation_query`)
- `prompt_context_id` (UUID, FK -> `Prompt Context`)
- `model_metadata_id` (UUID, FK -> `Model Metadata`)
- `request_payload_ref` (encrypted object reference or secure blob key)
- `payload_hash_sha256` (string)
- `idempotency_key` (string)
- `requested_at` (timestamp)

**Relationships**
- N:1 to `AI Interaction`
- N:1 to `Prompt Context`
- N:1 to `Model Metadata`
- 1:1 or 1:N to `AI Response` (depending on streaming/chunked responses)

**Retention requirements**
- Retain payload reference + hash for **24 months**.
- Raw payload body retained for **90 days** in encrypted store, then redacted or tokenized.

**Audit requirements**
- Log requester principal (user/service), auth scope, and policy decision.
- Persist deterministic hash to prove payload integrity for replay validation.

---

### 3) AI Response
**Purpose**
- Captures model outputs and serving metadata for each AI request.

**Required fields**
- `ai_response_id` (UUID, PK)
- `ai_request_id` (UUID, FK -> `AI Request`)
- `ai_interaction_id` (UUID, FK -> `AI Interaction`)
- `tenant_id` (UUID, required)
- `response_sequence` (int, required)
- `response_status` (enum: `success`, `safety_blocked`, `validation_failed`, `model_error`, `timeout`)
- `response_payload_ref` (encrypted object reference)
- `payload_hash_sha256` (string)
- `token_usage_input`, `token_usage_output` (int)
- `latency_ms` (int)
- `responded_at` (timestamp)

**Relationships**
- N:1 to `AI Request`
- N:1 to `AI Interaction`
- Can be materialized into `Recommendation Record` and `Skill Inference Record`

**Retention requirements**
- Response metadata: **24 months**.
- Raw generated text/artifacts: **180 days** by default, configurable by tenant policy.

**Audit requirements**
- Record applied safety policy version and moderation outcome.
- Store output hash and provenance (`provider_response_id`) for non-repudiation.

---

### 4) Recommendation Record
**Purpose**
- Persists recommendation outputs consumable by learner UI, manager views, or automation (e.g., recommended course/lesson/action).

**Required fields**
- `recommendation_record_id` (UUID, PK)
- `ai_interaction_id` (UUID, FK -> `AI Interaction`)
- `ai_response_id` (UUID, FK -> `AI Response`)
- `tenant_id` (UUID, required)
- `user_id` (UUID, FK -> `User.user_id`)
- `recommendation_type` (enum: `course`, `lesson`, `learning_path_action`, `study_plan`)
- `target_course_id` (UUID, nullable FK -> `Course.course_id`)
- `target_lesson_id` (UUID, nullable FK -> `Lesson.lesson_id`)
- `target_enrollment_id` (UUID, nullable FK -> `Enrollment.enrollment_id`)
- `target_progress_id` (UUID, nullable logical FK -> `Progress.progress_id`)
- `rank_score` (decimal)
- `rationale_summary` (text, redacted-safe)
- `created_at`, `expires_at` (timestamp)

**Relationships**
- N:1 to `AI Interaction`
- N:1 to `AI Response`
- N:1 to `User`
- Optional N:1 to `Course`, `Lesson`, `Enrollment`, `Progress`

**Retention requirements**
- Keep active recommendations through `expires_at`.
- Archive recommendation metadata for **18 months** for explainability and reporting.

**Audit requirements**
- Record why recommended (`feature_vector_ref` / policy snapshot id).
- Track recommendation lifecycle events: shown, clicked, accepted, dismissed.

---

### 5) Skill Inference Record
**Purpose**
- Stores inferred skill signals derived from learner interactions, progress, and model output.

**Required fields**
- `skill_inference_record_id` (UUID, PK)
- `ai_interaction_id` (UUID, FK -> `AI Interaction`)
- `ai_response_id` (UUID, FK -> `AI Response`)
- `tenant_id` (UUID, required)
- `user_id` (UUID, FK -> `User.user_id`)
- `skill_taxonomy_id` (string/UUID)
- `skill_id` (string/UUID)
- `inferred_level` (enum/int scale)
- `confidence_score` (decimal)
- `evidence_ref` (object ref or event ids)
- `source_course_id` (UUID, nullable FK -> `Course.course_id`)
- `source_lesson_id` (UUID, nullable FK -> `Lesson.lesson_id`)
- `source_enrollment_id` (UUID, nullable FK -> `Enrollment.enrollment_id`)
- `source_progress_id` (UUID, nullable logical FK -> `Progress.progress_id`)
- `inferred_at` (timestamp)

**Relationships**
- N:1 to `AI Interaction`
- N:1 to `AI Response`
- N:1 to `User`
- Optional N:1 links to `Course`, `Lesson`, `Enrollment`, `Progress`

**Retention requirements**
- Active inference state retained until superseded.
- Historical inference versions retained **24 months** for trend analysis and audit replay.

**Audit requirements**
- Version each inference with model/prompt lineage.
- Maintain supersession chain (`supersedes_skill_inference_record_id`).

---

### 6) Prompt Context
**Purpose**
- Captures normalized context used to construct prompts (without overexposing sensitive source data).

**Required fields**
- `prompt_context_id` (UUID, PK)
- `ai_interaction_id` (UUID, FK -> `AI Interaction`)
- `tenant_id` (UUID, required)
- `context_type` (enum: `tutor`, `recommendation`, `skill_inference`, `course_generation`)
- `user_id` (UUID, nullable FK -> `User.user_id`)
- `course_id` (UUID, nullable FK -> `Course.course_id`)
- `lesson_id` (UUID, nullable FK -> `Lesson.lesson_id`)
- `enrollment_id` (UUID, nullable FK -> `Enrollment.enrollment_id`)
- `progress_id` (UUID, nullable logical FK -> `Progress.progress_id`)
- `context_snapshot_ref` (encrypted object ref)
- `context_hash_sha256` (string)
- `created_at` (timestamp)

**Relationships**
- N:1 to `AI Interaction`
- 1:N to `AI Request`
- Optional N:1 links to `User`, `Course`, `Lesson`, `Enrollment`, `Progress`

**Retention requirements**
- Store context hashes and pointers for **24 months**.
- Raw snapshots retained **90 days** unless legal hold/compliance extension applies.

**Audit requirements**
- Include data classification labels and redaction policy version.
- Track source datasets used to build context (`source_system`, `source_record_ids`).

---

### 7) Model Metadata
**Purpose**
- Versioned registry of model/provider configuration used for requests and responses.

**Required fields**
- `model_metadata_id` (UUID, PK)
- `tenant_id` (UUID, nullable for global default)
- `provider` (string)
- `model_name` (string)
- `model_version` (string)
- `deployment_region` (string)
- `temperature`, `top_p`, `max_tokens` (numeric)
- `safety_profile` (string)
- `prompt_template_version` (string)
- `effective_from`, `effective_to` (timestamp)
- `created_at` (timestamp)

**Relationships**
- 1:N with `AI Request`
- Referenced indirectly by `AI Response` for lineage checks

**Retention requirements**
- Retain all historical versions for **minimum 36 months**.
- Never hard-delete model metadata used by any request.

**Audit requirements**
- Record approver and change ticket for each new config version.
- Immutable config checksum for reproducibility.

## Safe Linkage to Existing LMS V2 Entities

### Referential Linking Rules
- Every AI table includes `tenant_id`; all joins to LMS entities must include `(tenant_id, foreign_id)` validation.
- `user_id` links to canonical `User`.
- Optional anchors allow contextual linkage to `Course`, `Lesson`, `Enrollment`, and `Progress` without forcing all interactions to be course-bound.
- `Progress` links are treated as **logical foreign keys** where physical FK cannot be guaranteed cross-service; enforce through application-level integrity checks and event-driven validators.

### Safety Constraints
- No AI table may own or mutate canonical learner state in `Enrollment`/`Progress`; AI outputs are advisory unless accepted by domain services.
- Sensitive prompt/response content is referenced via encrypted object storage keys, not duplicated in plaintext columns.
- PII minimization: only necessary identity keys are stored; derived text uses redacted summaries.

## Service Isolation Model
- **AI Tutor Service** owns: `AI Interaction`, `AI Request`, `AI Response`, `Prompt Context`, `Model Metadata`.
- **Recommendation Service** owns materialized `Recommendation Record` projections.
- **Skill Analytics Service** owns materialized `Skill Inference Record` projections.
- Cross-service writes occur via events (`AIResponseGenerated`, `RecommendationMaterialized`, `SkillInferenceMaterialized`) and idempotent consumers.

## Future Extensibility
- Add `Tool Invocation Record` for retrieval/tool-use traces without changing existing entities.
- Add `Human Review Record` for HITL adjudication workflows.
- Extend `interaction_type` and `request_type` enums with backward-compatible values.
- Support multi-model orchestration by allowing multiple `AI Request` rows under one `AI Interaction`.

## QC LOOP

### Iteration 1 — Evaluation

| Category | Score (1–10) | Findings |
| --- | --- | --- |
| AI auditability | 9 | Strong hashes and lineage, but missing explicit immutable event log requirement for access to sensitive blobs. |
| Schema safety | 9 | Tenant scope is strong, but legal-hold retention override not explicit across all entities. |
| Alignment with existing repo entities | 10 | Clear linkage to `User`, `Course`, `Lesson`, `Enrollment`, `Progress`. |
| Service isolation | 9 | Domain ownership defined, but write-contract boundaries need explicit prohibition on direct cross-service table writes. |
| Future extensibility | 10 | Supports new interaction types and multi-model orchestration. |

**Flaws identified (<10)**
1. Audit coverage gap for sensitive artifact access events.
2. Retention policy did not consistently include legal-hold override language.
3. Service isolation needed stricter cross-service persistence rule.

**Schema revisions applied**
- Added requirement: immutable access audit events for `request_payload_ref`, `response_payload_ref`, and `context_snapshot_ref` reads.
- Added global legal-hold override rule to retention behavior.
- Added strict rule: services consume events and may not directly write tables owned by other services.

### Iteration 2 — Re-evaluation After Revisions

| Category | Score (1–10) | Findings |
| --- | --- | --- |
| AI auditability | 10 | End-to-end lineage plus immutable access logging enables forensic replay. |
| Schema safety | 10 | Tenant scoping, encrypted references, logical FK checks, and legal-hold overrides are complete. |
| Alignment with existing repo entities | 10 | Safe contextual links to all required LMS entities are explicit and constrained. |
| Service isolation | 10 | Ownership boundaries and event-only cross-service materialization are enforceable. |
| Future extensibility | 10 | Additive enum growth, modular projections, and orchestration support preserve compatibility. |

**QC Result:** All categories are **10/10**.

## Global Controls (Applied Across All Entities)
- **Legal hold override**: any record under legal/compliance hold is exempt from purge/TTL jobs.
- **Immutable access audit**: each read of encrypted payload/context objects emits append-only audit events with actor, reason, and timestamp.
- **Cross-service write prohibition**: only owning service writes its tables; other services integrate through events/APIs.
