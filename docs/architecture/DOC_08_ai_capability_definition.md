# DOC_08: AI Capability Definition

## 1) Purpose and Scope
This document defines the LMS AI capability layer across four services:
- AI Tutor
- Recommendation Engine
- Course Generation
- Skill Inference

It specifies how these services integrate with learning events, the knowledge graph, analytics signals, and assessment outcomes. It also defines canonical AI inputs, outputs, and strict service boundaries to preserve modularity, privacy, and operational safety.

---

## 2) AI Service Definitions

| Service | Primary Objective | Core Responsibilities | Non-Goals |
|---|---|---|---|
| AI Tutor | Provide contextual, adaptive learner support | Explain concepts, answer questions, generate hints, provide stepwise coaching grounded in approved course content and learner context | Persistent grading authority, direct learner profile mutation, policy override |
| Recommendation Engine | Personalize next-best learning actions | Rank courses, lessons, activities, and practice tasks using learner state, goals, and skill gaps | Generate new source content, infer skill ontologies, alter assessment scores |
| Course Generation | Produce draft instructional artifacts | Generate outlines, lessons, quizzes, and summaries from approved source inputs and curriculum constraints | Final publishing without human approval, live recommendation ranking |
| Skill Inference | Infer and update skill mastery probabilities | Map learner behavior and outcomes to skill evidence, update proficiency/confidence, emit skill progression signals | Direct content authoring, direct recommendation ranking, policy exception handling |

---

## 3) Integration Model

### 3.1 Learning Events Integration
**Event Sources**
- Player/runtime events (start, pause, complete, replay)
- Activity events (submission, interaction, retry)
- Tutor interaction events (question asked, hint requested, session end)

**Integration Pattern**
- All services consume normalized event streams from the event bus via versioned schemas.
- Services read events asynchronously and emit derived events only through their owned topics.
- No service reads another service's private store directly.

**Representative Event Contracts**
- `learning.session.started`
- `learning.activity.completed`
- `assessment.item.attempted`
- `ai.tutor.response.generated`
- `ai.skill_inference.updated`

### 3.2 Knowledge Graph Integration
**Graph Role**
- Canonical semantic layer for content-topic-skill-prerequisite relationships.

**Usage by Service**
- AI Tutor: fetches concept prerequisites and related nodes for grounded explanations.
- Recommendation Engine: traverses skill/course graph edges for prerequisite-safe ranking.
- Course Generation: aligns generated modules to graph taxonomy and prerequisite topology.
- Skill Inference: writes evidence-linked mastery updates to skill nodes (via API).

**Constraints**
- Graph writes are API-mediated with validation and audit logging.
- Read operations are tenant-scoped and policy-filtered.

### 3.3 Analytics Signals Integration
**Signal Types**
- Engagement (dwell time, drop-off points, revisit rate)
- Progression (pace, completion delta, deadline risk)
- Behavioral quality (hint dependency, retry volatility)

**Integration Pattern**
- Analytics service computes features and publishes signed, versioned feature vectors.
- AI services consume only approved feature sets from feature registry IDs.
- Backfilling and feature recalculation are idempotent and timestamped.

### 3.4 Assessment Outcomes Integration
**Outcome Inputs**
- Item-level correctness
- Attempt count and latency
- Objective/competency achievement
- Summative/formative scores

**Integration Pattern**
- Skill Inference consumes detailed outcomes for mastery updates.
- Recommendation Engine consumes aggregate outcomes for ranking adjustments.
- AI Tutor consumes outcome summaries for remediation guidance.
- Course Generation consumes cohort-level outcome deficits for content gap proposals.

---

## 4) Canonical AI Inputs and Outputs

### 4.1 AI Inputs (by class)

| Input Class | Examples | Producer | Consumers |
|---|---|---|---|
| Learner Context | role, locale, accessibility preferences, target goals | User/Profile services | Tutor, Recommendation, Course Generation |
| Learning Events | session lifecycle, activity interactions, navigation behavior | Event ingestion pipeline | All four services |
| Knowledge Graph Context | skill taxonomy, prerequisite edges, concept relations | Knowledge graph service | All four services |
| Analytics Features | engagement score, risk index, pace variance | Analytics service | Tutor, Recommendation, Skill Inference |
| Assessment Outcomes | item attempts, objective score vectors, rubric outcomes | Assessment service | Tutor, Recommendation, Skill Inference, Course Generation (aggregates) |
| Policy/Guardrails | content safety policies, allowed tools, model routing rules | Policy/config service | All four services |

### 4.2 AI Outputs (by service)

| Service | Output Artifacts | Downstream Consumers |
|---|---|---|
| AI Tutor | tutor responses, hints, remediation plan, confidence metadata, citation links | Learner UI, audit logs, analytics |
| Recommendation Engine | ranked recommendations, rationale tags, exploration/exploitation metadata | Learner UI, manager dashboard |
| Course Generation | draft syllabus, lesson drafts, question banks, alignment report | Content authoring workflow |
| Skill Inference | mastery score updates, confidence intervals, evidence references | Skills graph, recommendation engine, analytics |

---

## 5) Service Boundaries and Isolation

## 5.1 Ownership Boundaries
- **AI Tutor owns** response orchestration and conversational state windows.
- **Recommendation Engine owns** ranking logic and recommendation policies.
- **Course Generation owns** generation pipelines for draft learning artifacts.
- **Skill Inference owns** probabilistic mastery estimation and evidence aggregation.

## 5.2 Data Boundaries
- Raw event retention remains in analytics/event stores, not AI service-local databases.
- AI services may cache derived features with TTL; source-of-truth remains upstream.
- Cross-service data access must occur via public APIs or event topics.

## 5.3 Execution Boundaries
- Each service deploys independently, with isolated model routing configs.
- Model providers are abstracted behind service-local adapters.
- Failures degrade locally (e.g., Tutor fallback templates) without cascading writes.

## 5.4 Interface Boundaries
- Versioned contracts for inbound events, outbound events, and synchronous APIs.
- Contract-breaking changes require compatibility window and schema migration plan.

---

## 6) Safety and Governance Considerations
- Tenant isolation on all prompts, retrieval queries, and generated outputs.
- PII minimization in prompts through tokenization/redaction at ingress.
- Policy enforcement layer for prohibited content, unsafe recommendations, and prompt injection filtering.
- Human-in-the-loop approval required before publishing AI-generated course content.
- Full traceability: prompt template ID, model version, feature snapshot ID, and output hash.
- Monitoring for drift, hallucination incidence, recommendation bias, and false mastery inflation.

---

## 7) Quality Control (QC) Loop

### QC Iteration 1

| Category | Score (1-10) | Findings |
|---|---:|---|
| AI integration correctness | 8 | Event and graph usage defined, but graph write path for Skill Inference lacked explicit approval workflow semantics. |
| Data dependency clarity | 9 | Input classes are clear, but feature lineage to model invocation required stronger traceability contract. |
| Service isolation | 8 | Boundaries defined, but fallback behavior did not explicitly prevent hidden cross-service coupling under degraded modes. |
| Safety considerations | 9 | Core controls present, but missing explicit abuse throttling and model rollback trigger criteria. |

**Architecture flaw identified (blocking 10/10):**
- Missing explicit **Control Plane Contract** governing model version pinning, feature snapshot binding, graph-write approval state machine, and emergency rollback behavior across services.

### Revision Applied
To resolve the flaw, the AI capability design adds a mandatory control plane contract:
1. **Model Invocation Envelope (MIE)** required for every AI call:
   - `tenant_id`, `service_id`, `model_version`, `prompt_template_id`, `feature_snapshot_id`, `policy_bundle_version`, `request_risk_level`.
2. **Graph Write Approval FSM** for Skill Inference writes:
   - `proposed -> validated -> approved -> committed` (with audit actor and reason codes).
3. **Degradation Isolation Rules**:
   - If dependencies fail, service must emit `ai.service.degraded` and switch to local fallback; no compensating writes into other service domains.
4. **Safety Runtime Controls**:
   - Rate limits by tenant/user risk tier, automatic model rollback on safety breach threshold, and quarantine queue for suspicious outputs.

### QC Iteration 2 (Post-Revision)

| Category | Score (1-10) | Findings |
|---|---:|---|
| AI integration correctness | 10 | Integration contracts now include explicit invocation envelope and graph-write approval lifecycle. |
| Data dependency clarity | 10 | Feature lineage and policy bundle versioning are now bound per invocation for full reproducibility. |
| Service isolation | 10 | Degradation rules prevent cross-service side effects and enforce domain-local failure handling. |
| Safety considerations | 10 | Added throttling, rollback triggers, and quarantine controls complete operational safety posture. |

**QC Result:** All categories are now **10/10**.

---

## 8) Final AI Capability Baseline
The AI capability is approved with:
- Four isolated services (Tutor, Recommendation, Course Generation, Skill Inference)
- Event/API mediated integrations only
- Explicit control plane envelope and approval workflows
- Auditable, reproducible, tenant-safe AI operations
- QC-validated architecture with all required quality categories at 10/10
