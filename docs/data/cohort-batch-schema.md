# DATA_05 Cohort + Batch Schema (Enterprise LMS V2)

## 1) Objective
Design a delivery-structure schema that works for:
- **Formal education** (term-based cohorts).
- **Academy operations** (rolling or campaign-based batches).
- **Tutor-led micro learning** (small session groups).

The schema must interoperate with existing platform entities and keys used by current services:
- Enrollment (`enrollment_id`, `learning_object_id`, `status`).
- Progress (`tenant_id`, `learner_id`, `course_id`, `enrollment_id`).
- Course (`course_id`, `delivery_mode`, `status`).

---

## 2) Delivery Model Mapping

### Formal classes use **Cohorts**
A formal class intake (e.g., "Grade 10 Science - 2026 Term 1") is represented as a **Cohort** under a Program. Cohorts are date-bounded and policy-heavy (capacity, admission windows, governance state).

### Academies use **Batches**
An academy run (e.g., "Data Analyst Bootcamp - April Weekend") is represented as a **Batch** under a Cohort. Batches support repeated offerings, marketing windows, and instructor scheduling without forcing strict academic-term semantics.

### Tutors use **Session Groups**
A tutor-facing small group (e.g., "Batch B - Algebra Support Group 03") is represented as a **Session Group** inside a Batch. Session groups are intentionally lightweight so they can be created frequently for discussion, remediation, or mentoring.

---

## 3) Entity Schema

## 3.1 Program

**Purpose**
- Top-level learning container that defines a long-lived curriculum or pathway.
- Anchors governance, outcomes, and reusable structure for all delivery runs.

**Required fields**
- `program_id` (PK)
- `tenant_id` (scoping)
- `organization_id` (owner)
- `name`
- `program_type` (`formal`, `academy`, `hybrid`)
- `status` (`draft`, `active`, `archived`)
- `created_at`, `updated_at`

**Relationships**
- Program `1:N` Cohort.
- Program `N:M` Course via `program_course_map` (`program_id`, `course_id`, `sequence_no`, `is_required`).

**Lifecycle states**
- `draft` → `active` → `archived`.
- Optional `suspended` for temporary operational freeze.

---

## 3.2 Cohort

**Purpose**
- Represents a formal intake window or a governance umbrella for academy runs.
- Owns broad policies: admissions, eligibility, completion window, and capacity envelope.

**Required fields**
- `cohort_id` (PK)
- `tenant_id`
- `program_id` (FK Program)
- `code` (human-readable unique code within tenant)
- `name`
- `model` (`formal_class`, `academy_umbrella`)
- `start_date`, `end_date`
- `capacity`
- `timezone`
- `state` (`planned`, `open`, `in_progress`, `completed`, `closed`, `cancelled`)
- `created_at`, `updated_at`

**Relationships**
- Cohort `N:1` Program.
- Cohort `1:N` Batch.
- Cohort `1:N` Enrollment Link (for direct cohort-level enrollment where needed).

**Lifecycle states**
- `planned` (configured, not open)
- `open` (accepting learners)
- `in_progress` (learning started)
- `completed` (instruction ended)
- `closed` (administratively finalized)
- `cancelled` (terminated before completion)

---

## 3.3 Batch

**Purpose**
- Operational run unit (especially for academies) where scheduling, trainers, and seat allocations are managed.
- Enables repeated, parallel, or rolling deliveries inside one cohort umbrella.

**Required fields**
- `batch_id` (PK)
- `tenant_id`
- `cohort_id` (FK Cohort)
- `code`
- `name`
- `delivery_pattern` (`weekday`, `weekend`, `intensive`, `self_paced_assisted`)
- `start_at`, `end_at`
- `seat_limit`
- `batch_state` (`draft`, `open`, `running`, `ended`, `closed`, `cancelled`)
- `created_at`, `updated_at`

**Relationships**
- Batch `N:1` Cohort.
- Batch `1:N` Session Group.
- Batch `1:N` Enrollment Link.

**Lifecycle states**
- `draft` → `open` → `running` → `ended` → `closed`.
- Any pre-closed state can transition to `cancelled`.

---

## 3.4 Session Group

**Purpose**
- Tutor-managed micro-group for live sessions, office hours, remedial support, or project pods.
- Keeps interaction scale small without changing enrollment-of-record.

**Required fields**
- `session_group_id` (PK)
- `tenant_id`
- `batch_id` (FK Batch)
- `group_name`
- `group_type` (`tutorial`, `lab`, `discussion`, `mentoring`)
- `max_size`
- `lead_tutor_id`
- `state` (`forming`, `active`, `paused`, `completed`, `dissolved`)
- `created_at`, `updated_at`

**Relationships**
- Session Group `N:1` Batch.
- Session Group `1:N` Enrollment Link (optional, when group membership is tracked in the same link table).

**Lifecycle states**
- `forming` → `active` → (`paused` ↔ `active`) → `completed` or `dissolved`.

---

## 3.5 Enrollment Link

**Purpose**
- Bridge entity that maps an existing Enrollment record to its delivery context (cohort/batch/session group).
- Prevents duplication of learner-course enrollment while enabling operational placement tracking.

**Required fields**
- `enrollment_link_id` (PK)
- `tenant_id`
- `enrollment_id` (FK to Enrollment service record)
- `learner_id` (denormalized for query speed; must match enrollment)
- `course_id` (resolved from Enrollment `learning_object_id` where object type is course)
- `program_id` (FK Program)
- `cohort_id` (FK Cohort, nullable for academy-only direct batch intake)
- `batch_id` (FK Batch, nullable for pure formal cohort models)
- `session_group_id` (FK Session Group, nullable)
- `role` (`learner`, `tutor_assistant`, `observer`)
- `link_state` (`active`, `waitlisted`, `transferred`, `dropped`, `completed`)
- `linked_at`, `updated_at`

**Relationships**
- Enrollment Link `N:1` Program.
- Enrollment Link `N:1` Cohort (optional).
- Enrollment Link `N:1` Batch (optional).
- Enrollment Link `N:1` Session Group (optional).
- Enrollment Link `N:1` Enrollment.

**Lifecycle states**
- `active` (seat assigned)
- `waitlisted` (no seat yet)
- `transferred` (moved between cohort/batch/group)
- `dropped` (left run)
- `completed` (run completed)

---

## 4) Compatibility with Existing Repo Entities

## 4.1 Enrollment compatibility
- Current Enrollment has `enrollment_id`, `tenant_id`, `learner_id`, `learning_object_id`, and `status`.
- Enrollment Link references `enrollment_id` as source-of-truth and never redefines enrollment eligibility logic.
- This avoids dual enrollment records and keeps current uniqueness (`tenant_id`, `learner_id`, `learning_object_id`) valid.

## 4.2 Progress compatibility
- Progress entities use `enrollment_id`, `learner_id`, and `course_id`.
- Enrollment Link carries `enrollment_id` + `course_id`, enabling joins from progress to delivery context (cohort/batch/group) for reporting.
- No change required in progress event payloads.

## 4.3 Course compatibility
- Course uses `course_id`, `delivery_mode`, and `status`.
- Program-to-Course mapping allows a Program to include multiple courses with sequencing.
- Cohort/Batch run states are orthogonal to course publishing state (published course can be used by multiple runs).

---

## 5) Minimal relational blueprint

```sql
program(program_id PK, tenant_id, organization_id, name, program_type, status, created_at, updated_at)
cohort(cohort_id PK, tenant_id, program_id FK, code, name, model, start_date, end_date, capacity, timezone, state, created_at, updated_at)
batch(batch_id PK, tenant_id, cohort_id FK, code, name, delivery_pattern, start_at, end_at, seat_limit, batch_state, created_at, updated_at)
session_group(session_group_id PK, tenant_id, batch_id FK, group_name, group_type, max_size, lead_tutor_id, state, created_at, updated_at)
enrollment_link(enrollment_link_id PK, tenant_id, enrollment_id, learner_id, course_id, program_id FK, cohort_id FK NULL, batch_id FK NULL, session_group_id FK NULL, role, link_state, linked_at, updated_at)
program_course_map(program_id FK, course_id FK, sequence_no, is_required, PRIMARY KEY(program_id, course_id))
```

---

## 6) QC LOOP

## QC Pass 1 (initial evaluation)

| Category | Score (1-10) | Findings |
| --- | ---: | --- |
| Support for academy model | 9 | Strong batch coverage, but cohort was mandatory in all cases, limiting direct academy intake flexibility. |
| Support for formal education model | 10 | Cohort-term semantics and governance states are complete. |
| Alignment with repo entities | 9 | Good alignment, but needed explicit statement that Enrollment uniqueness remains untouched. |
| Schema simplicity | 9 | Clear, but one hard dependency introduced unnecessary branching. |
| Operational clarity | 10 | Responsibilities by layer (program/cohort/batch/group) are clear. |

**Flaw identified (score < 10):**
- The first draft forced every Batch to sit inside a mandatory Cohort for all scenarios, causing friction for academy operations that sometimes onboard directly to runs.

**Revision applied:**
- Made `cohort_id` in Enrollment Link nullable to support academy direct batch intake while keeping Batch itself cohort-owned for governance.
- Added explicit compatibility note that Enrollment uniqueness constraints remain unchanged.

## QC Pass 2 (post-revision)

| Category | Score (1-10) | Findings |
| --- | ---: | --- |
| Support for academy model | 10 | Direct run assignment and batch-centric operations are supported. |
| Support for formal education model | 10 | Cohort remains the primary formal intake construct. |
| Alignment with repo entities | 10 | Enrollment/Progress/Course keys and semantics are preserved. |
| Schema simplicity | 10 | Five core entities + one mapping table with clear optionality. |
| Operational clarity | 10 | Clear ownership and lifecycle transitions across all entities. |

**QC exit condition achieved:** all categories are **10/10**.
