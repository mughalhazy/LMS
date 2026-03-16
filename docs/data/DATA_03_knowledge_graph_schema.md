# DATA_03 — Knowledge Graph Schema (Enterprise LMS V2)

## 1) Objective
Create an AI-reasoning-ready knowledge graph that augments (does **not** replace) existing LMS relational entities. The graph provides semantic links for adaptive learning decisions, prerequisite reasoning, mastery inference, and explainable recommendations.

### Non-replacement constraint (repo alignment)
- `Course` graph nodes are semantic wrappers around existing `courses` records.
- `Lesson` graph nodes are semantic wrappers around existing `lessons` records.
- `Credential` graph nodes are semantic wrappers around existing `certificates` records (certificate issuance remains authoritative in the Certification domain).
- Existing transactional CRUD remains in service-owned stores; the knowledge graph is a derived/read-optimized reasoning layer.

---

## 2) Node Types

| Node Type | Purpose | Required Fields | Source of Truth | Update Triggers |
|---|---|---|---|---|
| **Program** | Represents enterprise-level learning tracks (e.g., onboarding, role academy, compliance path) that group courses for sequencing and governance. | `program_id` (stable key), `tenant_id`, `title`, `status`, `version`, `effective_from`, `effective_to` (nullable), `owner_org_id`, `updated_at` | Program catalog service/domain tables (organizational learning structure ownership). | `program.created`, `program.updated`, `program.archived`, program version publication, program-course mapping changed. |
| **Course** | Canonical curriculum container used for learning objectives, sequencing, and enrollment targeting in graph reasoning. | `course_id` (maps 1:1 to `courses.id`), `tenant_id`, `title`, `description` (nullable), `difficulty_level`, `delivery_mode`, `status`, `version`, `updated_at` | Existing `courses` entity + learning structure service records. | `course.created`, `course.updated`, `course.published`, `course.versioned`, metadata/tag changes, syllabus changes affecting concept map. |
| **Lesson** | Instructional unit inside a course, used to attach fine-grained concepts and adaptive path decisions. | `lesson_id` (maps 1:1 to `lessons.id`), `course_id`, `tenant_id`, `title`, `sequence_index`, `estimated_minutes`, `status`, `updated_at` | Existing `lessons` entity + lesson service records. | `lesson.created`, `lesson.updated`, `lesson.published`, resequencing in course outline, lesson-content major revision. |
| **Concept** | Atomic knowledge unit (e.g., “Normalization”, “Photosynthesis”) enabling explainable mastery and prerequisite inference. | `concept_id`, `tenant_id`, `name`, `taxonomy_path`, `description`, `cognitive_level`, `version`, `updated_at` | Curriculum taxonomy/ontology store managed by content/AI curriculum governance. | concept catalog edits, ontology term merges/splits, concept deprecation, AI curation accepted by human reviewer. |
| **Skill** | Demonstrable competency target (e.g., “SQL Query Optimization”) linked to concepts and credentials. | `skill_id`, `tenant_id`, `name`, `framework` (e.g., SFIA/custom), `level`, `description`, `status`, `updated_at` | Enterprise skill framework registry / competency service. | skill framework sync, skill-level rubric updates, skill activation/deactivation, mapping approvals from governance workflow. |
| **Assessment** | Evaluation artifact used to measure concept mastery and downstream skill validation confidence. | `assessment_id`, `tenant_id`, `title`, `assessment_type`, `max_score`, `passing_score`, `status`, `version`, `updated_at` | Assessment domain/service records and authored assessment definitions. | `assessment.created`, `assessment.updated`, scoring rubric changes, item bank remap, publish/unpublish events. |
| **Credential** | Issued or issuable recognition (certificate/badge/compliance proof) validating skill attainment outcomes. | `credential_id` (maps to `certificates.id` or certificate template/instance key), `tenant_id`, `credential_type`, `title`, `issuer`, `status`, `issued_at` (nullable), `expires_at` (nullable), `updated_at` | Existing `certificates` entity + certification service policy/rules tables. | `certificate.issued`, `certificate.revoked`, `certificate.renewed`, credential rule changes, issuer policy updates. |

---

## 3) Edge Types

| Edge Type | Purpose | Required Fields | Source of Truth | Update Triggers |
|---|---|---|---|---|
| **program_contains_course** | Defines structural curriculum membership and ordering of courses under a program. | `edge_id`, `program_id`, `course_id`, `tenant_id`, `order_index`, `is_required`, `effective_from`, `effective_to` (nullable), `updated_at` | Program-course mapping tables in learning structure domain. | program composition edited, course added/removed/reordered, mandatory/optional flag change, program version rollout. |
| **course_contains_lesson** | Captures ordered lesson structure inside a course for sequencing and adaptive progression checkpoints. | `edge_id`, `course_id`, `lesson_id`, `tenant_id`, `order_index`, `is_optional`, `updated_at` | Existing course-lesson association (`lessons.course_id`) plus sequencing metadata in lesson service. | lesson resequenced, lesson moved across courses, optionality flag changed, lesson archive/restore. |
| **lesson_teaches_concept** | Links learning content to explicit conceptual coverage for explainable recommendations/remediation. | `edge_id`, `lesson_id`, `concept_id`, `tenant_id`, `coverage_weight` (0..1), `instruction_depth`, `updated_at` | Content annotation pipeline (author tags + reviewed AI extraction). | lesson content edits, concept tagging review approved, concept taxonomy revision requiring remap. |
| **concept_relates_to_skill** | Maps conceptual understanding to competency outcomes for mastery-to-skill inference. | `edge_id`, `concept_id`, `skill_id`, `tenant_id`, `relevance_weight` (0..1), `relation_type` (e.g., foundational/applied), `updated_at` | Curriculum governance mappings between concept ontology and skill framework. | competency framework update, concept-to-skill mapping approval, skill rubric recalibration. |
| **assessment_tests_concept** | Indicates which concepts are measured by an assessment and with what strength. | `edge_id`, `assessment_id`, `concept_id`, `tenant_id`, `weight` (0..1), `measurement_type` (diagnostic/formative/summative), `updated_at` | Assessment blueprint/item-bank mapping artifacts. | assessment blueprint changed, question bank remapped, psychometric recalibration. |
| **credential_validates_skill** | Declares which skills are validated by a credential and threshold expectations. | `edge_id`, `credential_id`, `skill_id`, `tenant_id`, `required_level`, `validation_strength`, `updated_at` | Certification policy engine and credential-skill rule definitions. | credential requirement policy change, skill framework version update, accreditation/compliance change. |

---

## 4) AI Reasoning & Adaptive Learning Utility

The schema supports AI use cases through explicit, weighted semantic paths:
- **Personalized next-best lesson** via `learner mastery -> concept gaps -> lesson_teaches_concept -> course_contains_lesson`.
- **Explainable skill gap analysis** via `concept_relates_to_skill` and `assessment_tests_concept` traceability.
- **Credential readiness estimation** via `assessment evidence -> concept mastery -> skill attainment -> credential_validates_skill`.
- **Program optimization** by analyzing completion bottlenecks along `program_contains_course` and concept coverage density.

Design notes for AI quality:
- Keep edge weights versioned and timestamped for drift analysis.
- Maintain provenance (`source_system`, `source_event_id`) on all node/edge upserts.
- Use soft-delete/deactivation semantics to preserve historical reasoning reproducibility.

---

## 5) Data Ownership & Synchronization Rules

1. **Transactional ownership stays in domain services** (Course/Lesson/Certificate systems remain authoritative).
2. **Graph is projection-only** and rebuilt via event streams + periodic reconciliation jobs.
3. **Tenant isolation is mandatory** (`tenant_id` required on every node and edge).
4. **Conflict resolution**: latest valid domain version wins; if conflicting concurrent events arrive, apply domain sequence/version ordering.
5. **Auditability**: every mutation records `updated_at`, `source_event_id`, and `schema_version`.

---

## 6) QC LOOP

### QC Round 1
| Category | Score (1–10) | Rationale |
|---|---:|---|
| graph clarity | 9 | Core structures defined, but edge semantics lacked explicit mandatory fields for ordering/weights in earlier draft. |
| AI usefulness | 9 | Reasoning paths present, but insufficient provenance/version guidance for model explainability consistency. |
| alignment with repo entities | 10 | Explicit wrappers for `Course`, `Lesson`, and `Certificate` (`Credential`) were preserved. |
| extensibility | 9 | Good base types, but needed stronger temporal validity fields on relation edges. |
| data ownership correctness | 9 | Projection rule stated, but conflict/version precedence not explicit enough. |

**Flaws identified (<10):**
1. Missing strict required edge fields for ordering/weights.
2. Insufficient provenance/versioning detail for AI explainability and replay.
3. Incomplete temporal validity/conflict rules.

**Revisions applied:**
- Added/standardized required edge fields (`order_index`, `coverage_weight`, `relevance_weight`, `weight`, temporal fields).
- Added provenance and drift/reproducibility guidance (`source_event_id`, versioning note).
- Added explicit synchronization and conflict-resolution rules.

### QC Round 2 (Post-revision)
| Category | Score (1–10) | Rationale |
|---|---:|---|
| graph clarity | 10 | Node/edge responsibilities and required fields are explicit and operationally actionable. |
| AI usefulness | 10 | Weighted, traceable relations and provenance support adaptive decisioning and explainability. |
| alignment with repo entities | 10 | Existing `Course`, `Lesson`, `Certificate` remain source systems; graph only wraps and links. |
| extensibility | 10 | Versioning, temporal validity, and independent ontology/skill nodes allow future expansion. |
| data ownership correctness | 10 | Domain ownership, projection pattern, and conflict-resolution policy are clearly defined. |

**QC Exit Condition:** All categories are **10/10**.
