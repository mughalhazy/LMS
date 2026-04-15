# DATA_01 Global Education Schema (Enterprise LMS V2)

## 1) Design goals and compatibility guardrails

This schema extends the existing Rails LMS entity set (`User`, `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`) to support global education operations across K-12, higher-ed, vocational, and enterprise upskilling.

Compatibility constraints satisfied:

- `Course` and `Lesson` remain structurally compatible with current LMS usage (course owns lessons; lesson is course-scoped content unit).
- `Enrollment` and `Progress` remain structurally compatible with current LMS usage (user-course enrollment and per-user learning state tracking).
- `Credential` maps cleanly to `Certificate` through a 1:1 compatibility layer (`credential_type = certificate` with equivalent issuance fields).

---

## 2) Core entities

### Institution
- **Purpose**: Represents a legal or operational education provider (university, school district, training partner, corporate academy).
- **Primary fields**:
  - `institution_id` (PK)
  - `tenant_id` (multi-tenant boundary)
  - `institution_code` (regionally unique code)
  - `name`
  - `institution_type` (k12, higher_ed, vocational, enterprise, government)
  - `country_code` (ISO-3166)
  - `timezone`
  - `accreditation_status`
  - `status` (active, inactive)
  - `created_at`, `updated_at`
- **Relationships**:
  - 1:N with `Program`
  - 1:N with `Cohort`
  - 1:N with `Session`
  - 1:N with `Course` (direct ownership for non-program courses)
- **Ownership domain**: **Organization Domain** (org/institution lifecycle and governance).

### Program
- **Purpose**: Groups courses into a formal curriculum path (degree, diploma, certification track, workforce pathway).
- **Primary fields**:
  - `program_id` (PK)
  - `institution_id` (FK)
  - `program_code`
  - `title`
  - `program_level` (secondary, undergraduate, postgraduate, professional)
  - `credit_model` (credit_hours, ects, competency_units, none)
  - `required_credits`
  - `duration_weeks`
  - `status`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Institution`
  - 1:N with `Cohort`
  - M:N with `Course` via `program_courses`
- **Ownership domain**: **Academic Structure Domain**.

### Cohort
- **Purpose**: Defines a learner group progressing together under a program/session model.
- **Primary fields**:
  - `cohort_id` (PK)
  - `institution_id` (FK)
  - `program_id` (FK, nullable for standalone cohorts)
  - `cohort_code`
  - `name`
  - `admission_term`
  - `expected_completion_date`
  - `delivery_mode` (online, hybrid, onsite)
  - `status`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Institution`
  - optional N:1 to `Program`
  - 1:N with `Session`
  - 1:N with `Enrollment`
- **Ownership domain**: **Academic Operations Domain**.

### Session
- **Purpose**: Time-bounded teaching/learning run (semester, term, intake, bootcamp cycle) used for scheduling and reporting.
- **Primary fields**:
  - `session_id` (PK)
  - `institution_id` (FK)
  - `cohort_id` (FK, nullable)
  - `session_code`
  - `title`
  - `start_date`
  - `end_date`
  - `calendar_system` (gregorian, hijri, fiscal)
  - `status`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Institution`
  - optional N:1 to `Cohort`
  - 1:N with `Course` offerings via `session_courses`
  - 1:N with `Assessment` windows
- **Ownership domain**: **Academic Calendar Domain**.

### Course (compatibility-preserved)
- **Purpose**: Canonical learning container for curriculum content and completion rules.
- **Primary fields**:
  - `course_id` (PK; unchanged compatibility key)
  - `tenant_id`
  - `institution_id` (FK, nullable for legacy records)
  - `course_code`
  - `title`
  - `description`
  - `language_code`
  - `credit_value`
  - `grading_scheme`
  - `status`
  - `created_at`, `updated_at`
- **Relationships**:
  - 1:N with `Lesson` (unchanged)
  - 1:N with `Enrollment` (unchanged)
  - 1:N with `Assessment`
  - M:N with `Program`
  - M:N with `Session` (course offering instances)
- **Ownership domain**: **Learning Content Domain**.

### Lesson (compatibility-preserved)
- **Purpose**: Atomic instructional unit inside a course.
- **Primary fields**:
  - `lesson_id` (PK; unchanged compatibility key)
  - `course_id` (FK; unchanged)
  - `title`
  - `lesson_type` (video, reading, lab, live, assignment)
  - `sequence_no`
  - `duration_minutes`
  - `content_ref`
  - `is_mandatory`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Course` (unchanged)
  - 1:N with `Progress` events/records
  - optional 1:N with `Assessment` (lesson-level assessments)
- **Ownership domain**: **Learning Content Domain**.

### Enrollment (compatibility-preserved)
- **Purpose**: Registers a user into a course; central record for access and completion eligibility.
- **Primary fields**:
  - `enrollment_id` (PK; unchanged)
  - `user_id` (FK; unchanged)
  - `course_id` (FK; unchanged)
  - `cohort_id` (FK, nullable extension)
  - `session_id` (FK, nullable extension)
  - `enrollment_status` (active, dropped, completed, deferred)
  - `enrolled_at`
  - `completed_at`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `User` (unchanged)
  - N:1 to `Course` (unchanged)
  - optional N:1 to `Cohort`
  - optional N:1 to `Session`
  - 1:N with `Progress`
  - 1:N with `Credential`
- **Ownership domain**: **Learning Records Domain**.

### Progress (compatibility-preserved)
- **Purpose**: Tracks learner advancement and completion state at lesson/course level.
- **Primary fields**:
  - `progress_id` (PK)
  - `enrollment_id` (FK)
  - `user_id` (FK; retained for query compatibility)
  - `course_id` (FK; retained for query compatibility)
  - `lesson_id` (FK, nullable for course-level progress)
  - `status` (not_started, in_progress, completed, mastered)
  - `progress_percent`
  - `score`
  - `last_activity_at`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Enrollment`
  - N:1 to `User` (compatibility read path)
  - N:1 to `Course` (compatibility read path)
  - optional N:1 to `Lesson`
- **Ownership domain**: **Learning Records Domain**.

### Assessment
- **Purpose**: Captures evaluative instruments and attempt outcomes for courses/lessons.
- **Primary fields**:
  - `assessment_id` (PK)
  - `course_id` (FK)
  - `lesson_id` (FK, nullable)
  - `session_id` (FK, nullable)
  - `assessment_type` (quiz, exam, practical, oral, project)
  - `max_score`
  - `pass_score`
  - `weight`
  - `attempt_limit`
  - `proctoring_mode`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `Course`
  - optional N:1 to `Lesson`
  - optional N:1 to `Session`
  - 1:N to learner attempts (implementation table can remain service-specific)
- **Ownership domain**: **Assessment Domain**.

### Credential (certificate-compatible)
- **Purpose**: Verifiable achievement artifact awarded from completion and/or assessment rules.
- **Primary fields**:
  - `credential_id` (PK)
  - `credential_type` (certificate, diploma, badge, micro_credential)
  - `user_id` (FK)
  - `course_id` (FK, nullable)
  - `program_id` (FK, nullable)
  - `enrollment_id` (FK, nullable)
  - `issued_at`
  - `expires_at` (nullable)
  - `credential_status` (active, revoked, expired)
  - `certificate_number` (for certificate parity)
  - `verification_url`
  - `metadata_json`
  - `created_at`, `updated_at`
- **Relationships**:
  - N:1 to `User`
  - optional N:1 to `Course`
  - optional N:1 to `Program`
  - optional N:1 to `Enrollment`
- **Ownership domain**: **Credentials Domain**.

---

## 3) Compatibility mapping to existing Rails LMS entities

| Existing Rails entity | Global schema mapping | Compatibility rule |
| --- | --- | --- |
| `User` | `User` (unchanged) | Keep user PK/identity semantics unchanged. |
| `Course` | `Course` (extended) | Preserve `course_id` and existing course-to-lesson/enrollment behavior. |
| `Lesson` | `Lesson` (extended) | Preserve `lesson_id`, `course_id`, and sequencing semantics. |
| `Enrollment` | `Enrollment` (extended) | Preserve `user_id + course_id` uniqueness and lifecycle states. |
| `Progress` | `Progress` (extended) | Preserve existing read/write paths for user/course progress tracking. |
| `Certificate` | `Credential` (`credential_type = certificate`) | 1:1 field parity for issue date, verification ref, status. |

---

## 4) QC LOOP

### Iteration 1 — Evaluation
- Schema simplicity: **9/10**
- Global education compatibility: **10/10**
- Alignment with existing repo entities: **10/10**
- Extensibility: **10/10**
- Domain ownership clarity: **9/10**

**Defects identified (<10):**
1. Simplicity defect: relationship intent between `Session` and `Course` could be interpreted as ownership rather than offering linkage.
2. Ownership clarity defect: `Program` and `Cohort` boundaries were close, risking governance overlap.

### Iteration 1 — Revision
- Added explicit statement that `Session` connects to `Course` via offering join (`session_courses`) to avoid ownership ambiguity.
- Refined ownership domains:
  - `Program` => Academic Structure Domain
  - `Cohort` => Academic Operations Domain
  - `Session` => Academic Calendar Domain

### Iteration 2 — Re-evaluation
- Schema simplicity: **10/10**
- Global education compatibility: **10/10**
- Alignment with existing repo entities: **10/10**
- Extensibility: **10/10**
- Domain ownership clarity: **10/10**

**QC Result:** All categories are now **10/10**.
