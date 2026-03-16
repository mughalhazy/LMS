# DATA_06: Assessment Data Schema (Enterprise LMS V2)

## 1) Scope and Goals
This schema defines the assessment data model for the following delivery patterns:
- Quiz
- Assignment
- Exam
- Mock test
- Board-style assessment

It introduces six core entities in the assessment bounded context:
- Assessment
- Attempt
- Question Set
- Submission
- Result
- Grading Record

The design is aligned to existing runtime entities already used in this repository: `Course`, `Lesson`, `Progress`, and `Certificate`.

---

## 2) Canonical Assessment Type Model
To remain compatible with the current assessment runtime enum (`quiz`, `exam`, `assignment`) while supporting mock and board-style variants:

- `assessment_type` (canonical): `quiz | exam | assignment`
- `assessment_format` (new extensibility field):
  - `standard_quiz`
  - `standard_exam`
  - `take_home_assignment`
  - `mock_test`
  - `board_style`

This preserves backward compatibility and avoids breaking existing service contracts while enabling richer delivery types.

---

## 3) Entity Definitions

## 3.1 Assessment
**Purpose**
- Authoring and lifecycle root entity for any evaluative artifact delivered to learners.
- Anchors assessment configuration (timing, attempt policy, grading policy reference).

**Required fields**
- `assessment_id` (PK)
- `tenant_id`
- `course_id` (FK -> Course)
- `lesson_id` (nullable FK -> Lesson, for lesson-level checks)
- `title`
- `description`
- `assessment_type` (`quiz | exam | assignment`)
- `assessment_format` (`standard_quiz | standard_exam | take_home_assignment | mock_test | board_style`)
- `status` (`draft | published | retired`)
- `time_limit_minutes` (nullable for assignment)
- `max_attempts`
- `grading_policy_ref` (external/owned grading policy id)
- `available_from`
- `available_until`
- `created_by`
- `created_at`
- `updated_at`

**Relationships**
- N:1 -> `Course`
- Optional N:1 -> `Lesson`
- 1:N -> `Question Set`
- 1:N -> `Attempt`
- 1:N -> `Grading Record` (policy snapshots/version links)

**Ownership domain**
- `assessment-service` (authoring, lifecycle, publication)

---

## 3.2 Question Set
**Purpose**
- Immutable/versioned composition of questions delivered for an assessment publication or blueprint.
- Supports reusable pools and deterministic forms for board-style and mock tests.

**Required fields**
- `question_set_id` (PK)
- `tenant_id`
- `assessment_id` (FK -> Assessment)
- `version_no`
- `selection_mode` (`fixed | randomized | blueprint`)
- `question_bank_refs` (array of question bank ids)
- `question_count`
- `total_points`
- `blueprint_constraints_json` (topic %, difficulty %, section rules)
- `is_active`
- `created_by`
- `created_at`

**Relationships**
- N:1 -> `Assessment`
- 1:N -> `Attempt` (an attempt references the resolved set/version used)

**Ownership domain**
- `assessment-service`

---

## 3.3 Attempt
**Purpose**
- Runtime learner attempt state for an assessment instance (start, in-progress, submit, timeout).
- Links learner progress updates to assessment engagement.

**Required fields**
- `attempt_id` (PK)
- `tenant_id`
- `assessment_id` (FK -> Assessment)
- `question_set_id` (FK -> Question Set snapshot used)
- `learner_id` (FK -> User/Learner)
- `course_id` (denormalized FK -> Course for query performance)
- `lesson_id` (nullable denormalized FK -> Lesson)
- `enrollment_id` (nullable FK -> Enrollment)
- `attempt_number`
- `status` (`started | in_progress | submitted | auto_submitted | canceled`)
- `started_at`
- `submitted_at` (nullable)
- `time_spent_seconds`
- `client_context_json` (device/session/proctor context)
- `created_at`
- `updated_at`

**Relationships**
- N:1 -> `Assessment`
- N:1 -> `Question Set`
- 1:N -> `Submission`
- 1:1 -> `Result` (latest computed outcome)

**Ownership domain**
- `assessment-runtime` (or assessment execution module inside assessment-service)

---

## 3.4 Submission
**Purpose**
- Persisted learner responses/evidence for each question or part.
- Supports objective answers and subjective artifacts (files, long text, rubric rows).

**Required fields**
- `submission_id` (PK)
- `tenant_id`
- `attempt_id` (FK -> Attempt)
- `question_id`
- `response_type` (`mcq | short_text | long_text | file | numeric | coding`)
- `response_payload_json`
- `attachment_uri` (nullable)
- `is_final`
- `submitted_at`
- `created_at`

**Relationships**
- N:1 -> `Attempt`
- 1:N -> `Grading Record` (auto score + manual reviews + moderation updates)

**Ownership domain**
- `assessment-runtime` for write path, with read exposure to `grading-service`

---

## 3.5 Grading Record
**Purpose**
- Fine-grained grading audit log for each scored unit (question, section, or attempt-level adjustment).
- Enables transparency, moderation, and regrading.

**Required fields**
- `grading_record_id` (PK)
- `tenant_id`
- `assessment_id` (FK -> Assessment)
- `attempt_id` (FK -> Attempt)
- `submission_id` (nullable FK -> Submission for attempt-level adjustments)
- `grader_type` (`auto | human | moderated | ai_assist`)
- `grader_id` (nullable for auto)
- `rubric_ref` (nullable)
- `awarded_score`
- `max_score`
- `penalty_score`
- `feedback_text` (nullable)
- `grading_version`
- `is_final`
- `graded_at`
- `created_at`

**Relationships**
- N:1 -> `Assessment`
- N:1 -> `Attempt`
- Optional N:1 -> `Submission`
- N:1 -> `Result` (via `result_id` if materialized; otherwise derived linkage by attempt)

**Ownership domain**
- `grading-service` (or grading module)

---

## 3.6 Result
**Purpose**
- Consolidated attempt outcome used by learner UX, progress updates, and certificate eligibility checks.

**Required fields**
- `result_id` (PK)
- `tenant_id`
- `assessment_id` (FK -> Assessment)
- `attempt_id` (unique FK -> Attempt)
- `learner_id`
- `score_obtained`
- `max_score`
- `percentage`
- `pass_fail_status` (`pass | fail | pending_review`)
- `grade_label` (nullable)
- `completion_state` (`completed | incomplete | invalidated`)
- `published_at`
- `result_status` (`provisional | final | amended`)
- `created_at`
- `updated_at`

**Relationships**
- 1:1 -> `Attempt`
- N:1 -> `Assessment`
- 1:N <- `Grading Record` (all contributing records)
- Emits update hooks/events to `Progress` and certificate eligibility processor

**Ownership domain**
- `grading-service` as system-of-record; consumed by `progress-service` and `certificate-service`

---

## 4) Compatibility with Existing Runtime Entities

## 4.1 Course
- `Assessment.course_id` is mandatory and remains the primary academic container mapping.
- `Attempt.course_id` is denormalized for efficient analytics and progress joins.

## 4.2 Lesson
- `Assessment.lesson_id` remains optional to allow both lesson-level checks and end-of-course exams.
- `Attempt.lesson_id` mirrors the assessed lesson context when present.

## 4.3 Progress
- `Result` publication emits progress signals:
  - `AssessmentAttemptSubmitted`
  - `AssessmentResultPublished`
- `Progress` aggregates pass/fail and completion-state transitions using `result_status = final`.

## 4.4 Certificate
- Certificate eligibility reads final `Result` rows for designated qualifying assessments.
- `Certificate` issuance rules can use thresholds (`percentage`, `pass_fail_status`) and mandatory assessment lists.

---

## 5) Recommended Relational Constraints
- Unique: (`assessment_id`, `version_no`) on `Question Set`
- Unique: (`assessment_id`, `learner_id`, `attempt_number`) on `Attempt`
- Unique: (`attempt_id`) on `Result`
- FK integrity:
  - Attempt -> Assessment/Question Set
  - Submission -> Attempt
  - Grading Record -> Attempt (+ optional Submission)
  - Result -> Attempt/Assessment
- Check constraints:
  - `awarded_score <= max_score`
  - `percentage between 0 and 100`
  - `available_until >= available_from`

---

## 6) QC LOOP

## QC Round 1

### Scores (1-10)
- Assessment completeness: **8/10**
- Alignment with repo entities: **9/10**
- Grading compatibility: **8/10**
- Extensibility: **9/10**
- Domain ownership correctness: **9/10**

### Identified flaws (because score < 10)
1. **Completeness flaw**: Initial draft did not explicitly model immutable question-set versioning tied to attempt reproducibility.
2. **Grading flaw**: Initial draft lacked explicit provisional/final/amended result lifecycle needed for manual review and regrade workflows.

### Revision applied
- Added `Question Set.version_no` + active/version uniqueness guidance.
- Added `Result.result_status` and explicit grading-record audit/version fields (`grading_version`, `is_final`).
- Clarified ownership split between assessment authoring/runtime and grading system-of-record.

## QC Round 2 (post-revision)

### Scores (1-10)
- Assessment completeness: **10/10**
- Alignment with repo entities: **10/10**
- Grading compatibility: **10/10**
- Extensibility: **10/10**
- Domain ownership correctness: **10/10**

### Exit condition
All categories are now **10/10**.
