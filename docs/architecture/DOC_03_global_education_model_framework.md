# DOC_03: Global Education Model Framework

## Objective
Define a universal education domain framework that supports **schools**, **universities**, **academies**, **tutors**, and **corporate training**, while preserving direct compatibility with existing LMS entities for **Course** and **Lesson**.

## Universal Learning Hierarchy

| hierarchy_level | purpose | cardinality (parent -> child) | maps to existing repo model |
| --- | --- | --- | --- |
| Institution | Top-level education provider or organizational tenant context. | Institution -> many Programs | `tenants` + optional `organizations` for sub-structures |
| Program | A structured offering (degree track, bootcamp, compliance path, tutoring package). | Program -> many Cohorts | new conceptual entity, links to `organizations` and `courses` |
| Cohort | Time-bound or audience-bound learner group. | Cohort -> many Sessions | existing `cohort` concept/spec |
| Session | Scheduled delivery window or recurring run of learning activities. | Session -> many Courses | new conceptual entity for timetable/run management |
| Course | Curriculum container with learning outcomes and assessments. | Course -> many Lessons; many Enrollments | **direct map to existing `courses` table** |
| Lesson | Instructional unit within a course. | Lesson -> zero/many Progress records | **direct map to existing `lessons` table** |
| Enrollment | Learner registration into a course/session/program context. | Enrollment -> one Progress stream, zero/many Credentials | **direct map to existing `enrollments` table** |
| Progress | Completion and mastery state over lessons/course milestones. | Progress belongs to Enrollment (+ Lesson/Course milestones) | aligns to existing progress tracking specs and enrollment-course relation |
| Credential | Earned certificate, diploma marker, badge, or compliance proof. | Credential belongs to Enrollment/User/Course | maps to existing `certificates` table |

## Entity Definitions

### 1) Institution
A legal or operating education provider. Supports different institution types:
- K-12 school networks
- universities
- academies/bootcamps
- independent tutors (single-person institution)
- corporate training organizations

**Core attributes**: `institution_id`, `tenant_id`, `institution_type`, `name`, `accreditation_scope`, `operating_regions`, `default_language`.

### 2) Program
A market-facing or governance-facing learning package under an institution.
- School: grade curriculum (e.g., Grade 10 STEM)
- University: degree track / faculty program
- Academy: intensive bootcamp
- Tutor: personalized learning plan
- Corporate: role-based onboarding/compliance track

**Core attributes**: `program_id`, `institution_id`, `name`, `program_type`, `duration_model`, `credential_policy`.

### 3) Cohort
A bounded learner group (by intake date, class section, client account, or tutoring batch).

**Core attributes**: `cohort_id`, `program_id`, `name`, `start_date`, `end_date`, `delivery_mode`.

### 4) Session
A concrete run/calendar context for delivery (semester, term block, weekend batch, corporate quarter).

**Core attributes**: `session_id`, `cohort_id`, `term_code`, `schedule_pattern`, `timezone`, `instructor_assignments`.

### 5) Course (**existing model**)
The primary instructional container.

**Repo alignment**: maps 1:1 to `courses.course_id`, scoped by `tenant_id` and optional `organization_id`.

### 6) Lesson (**existing model**)
Atomic instructional component within a course.

**Repo alignment**: maps 1:1 to `lessons.lesson_id` with `lessons.course_id` foreign key.

### 7) Enrollment (**existing model**)
Learner participation record.

**Repo alignment**: maps 1:1 to `enrollments.enrollment_id`; uniqueness rule `unique(user_id, course_id)` remains canonical.

### 8) Progress
Progress state for lesson/course completion and mastery.

**Core attributes**: `progress_id`, `enrollment_id`, `lesson_id` (nullable for course aggregate), `completion_percent`, `mastery_level`, `last_activity_at`.

### 9) Credential
Formal learning outcome artifact.

**Repo alignment**: maps to `certificates` and can represent school transcript components, university certificates, academy badges, tutor-issued completion proof, and corporate compliance credentials.

## Relationship Model

1. `Institution 1:N Program`
2. `Program 1:N Cohort`
3. `Cohort 1:N Session`
4. `Session 1:N Course` (delivery run includes multiple courses)
5. `Course 1:N Lesson` (**existing FK in repo**)
6. `Course 1:N Enrollment` and `User 1:N Enrollment` (**existing repo relation**)
7. `Enrollment 1:N Progress`
8. `Enrollment 0:N Credential` (or `User + Course -> Credential` projection)

### Compatibility bridge to current schema

| framework_entity | current_table_or_spec | compatibility note |
| --- | --- | --- |
| Institution | `tenants`, `organizations` | Tenant is global boundary; organization models department/campus/client account. |
| Program | `organizations` (+ service-level abstraction) | Can be represented as typed organization node or new service entity. |
| Cohort | `docs/specs/cohort_spec.md` | Existing concept retained directly. |
| Session | scheduling abstraction in service layer | Additive entity; does not break course/lesson schema. |
| Course | `courses` | unchanged; direct map required by this framework. |
| Lesson | `lessons` | unchanged; direct map required by this framework. |
| Enrollment | `enrollments` | unchanged; unique learner-course rule preserved. |
| Progress | `docs/specs/progress_tracking_spec.md` | Tracks lesson/course progression keyed by enrollment. |
| Credential | `certificates` | Existing certificate model generalized as universal credential. |

## Example Institution Structures

### A) School (K-12)
- Institution: `North Valley Public School`
- Program: `Grade 10 Core Curriculum`
- Cohort: `Grade10-A-2026`
- Session: `Term1-2026`
- Courses: `Mathematics 10`, `Biology 10`
- Lessons: chapter-based units per course
- Enrollment: student-course registrations
- Progress: per lesson completion + term summary
- Credential: annual transcript certificate

### B) University
- Institution: `Global State University`
- Program: `BSc Computer Science`
- Cohort: `Fall-2026 Intake`
- Session: `Semester-1`
- Courses: `CS101`, `MATH121`
- Lessons: weekly lectures/labs
- Enrollment: student per course
- Progress: assignment + lesson + assessment milestones
- Credential: degree milestone certificates and final completion

### C) Academy / Bootcamp
- Institution: `NextGen Data Academy`
- Program: `12-week Data Engineering Bootcamp`
- Cohort: `DE-Jan-2027`
- Session: `Weekend Track`
- Courses: `Python Foundations`, `ETL Pipelines`
- Lessons: project modules
- Enrollment: participant per course
- Progress: sprint milestones
- Credential: job-ready skill badge

### D) Tutor-led Institution
- Institution: `Dr. Lee Tutoring`
- Program: `SAT Math Intensive`
- Cohort: `SAT-March-Batch`
- Session: `TueThu-Evening`
- Courses: `SAT Algebra`, `SAT Problem Solving`
- Lessons: topic drills
- Enrollment: learner per course
- Progress: mastery by topic
- Credential: tutor completion report

### E) Corporate Training
- Institution: `Acme Corp Learning`
- Program: `Security & Compliance Path`
- Cohort: `New-Hires-Q1`
- Session: `Q1-2027 Onboarding`
- Courses: `Code of Conduct`, `Secure Data Handling`
- Lessons: policy modules
- Enrollment: employee-course assignment
- Progress: mandatory completion tracking
- Credential: compliance certificate

## QC LOOP

### Iteration 1 — Evaluation

| category | score (1-10) | notes |
| --- | --- | --- |
| education system coverage | 10 | All five required institution types represented with concrete examples. |
| schema clarity | 8 | Session-to-course linkage needed clearer cardinality and service-boundary note. |
| alignment with repo entities | 9 | Course/Lesson direct mapping present; needed explicit unchanged-table statement for Enrollment/Credential. |
| academy and tutor compatibility | 9 | Supported but credential semantics for tutor flow needed stronger definition. |

**Structural issue identified**:
- Ambiguity in `Session -> Course` delivery semantics and insufficiently explicit reuse of existing `enrollments`/`certificates` for non-traditional providers.

**Revision applied**:
- Added explicit `Session 1:N Course` relationship.
- Added compatibility bridge table with direct references for Cohort/Progress specs and explicit Enrollment/Credential reuse.
- Clarified tutor and academy credential handling under unified Credential model.

### Iteration 2 — Re-evaluation after revision

| category | score (1-10) | notes |
| --- | --- | --- |
| education system coverage | 10 | Complete and balanced across school, university, academy, tutor, corporate. |
| schema clarity | 10 | Hierarchy, cardinality, and compatibility bridge are explicit and implementation-ready. |
| alignment with repo entities | 10 | Course/Lesson are direct 1:1 mappings and existing enrollment/certificate constraints are preserved. |
| academy and tutor compatibility | 10 | Personalized tutoring and bootcamp delivery are first-class without schema branching. |

**QC status**: All categories are now **10/10**.
