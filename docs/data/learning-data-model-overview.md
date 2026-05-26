# DOC 09: Learning Data Model Overview

## Objective
Define a simple, extensible Learning Data Model that supports institutional training operations while remaining compatible with the repository's existing learning entities: **Course**, **Lesson**, **Enrollment**, **Progress**, and **Certificate**.

## Core Entities

| Entity | Purpose | Key fields (illustrative) |
| --- | --- | --- |
| Institution | Tenant or top-level learning owner that governs programs, users, and policy. | `institution_id`, `name`, `status`, `timezone`, `created_at` |
| Program | Structured learning offering that groups courses and targets outcomes. | `program_id`, `institution_id`, `title`, `program_type`, `status` |
| Cohort | Time-bound learner group within a program for pacing, reporting, or facilitation. | `cohort_id`, `program_id`, `institution_id`, `name`, `start_date`, `end_date` |
| Session | Scheduled delivery instance for a course (live, hybrid, or asynchronous window). | `session_id`, `course_id`, `cohort_id` (nullable), `start_at`, `end_at`, `delivery_mode` |
| Course | Reusable curriculum container made of lessons and assessments. | `course_id`, `institution_id`, `program_id` (nullable), `title`, `version`, `status` |
| Lesson | Atomic instructional unit inside a course. | `lesson_id`, `course_id`, `title`, `sequence_no`, `content_type`, `estimated_minutes` |
| Enrollment | Learner registration record for a course/session/program context. | `enrollment_id`, `institution_id`, `user_id`, `course_id`, `session_id` (nullable), `cohort_id` (nullable), `state` |
| Progress | Learner advancement state at enrollment, course, and lesson granularity. | `progress_id`, `enrollment_id`, `course_id`, `lesson_id` (nullable), `percent_complete`, `status`, `last_activity_at` |
| Assessment | Evaluation artifact tied to a course or lesson, with attempt outcomes linked to enrollment. | `assessment_id`, `course_id`, `lesson_id` (nullable), `assessment_type`, `max_score`, `passing_score` |
| Credential | Award issued after completion/achievement conditions are met. | `credential_id`, `institution_id`, `user_id`, `course_id`, `program_id` (nullable), `enrollment_id`, `issued_at`, `credential_type` |

## Relationship Overview

### Ownership and Hierarchy
- **Institution 1:N Program** — each program belongs to one institution.
- **Institution 1:N Course** — each course is institution-owned for tenancy and policy enforcement.
- **Program 1:N Cohort** — cohorts segment learners inside a program timeline.
- **Program 1:N Course (optional)** — a program curates one or more courses; courses may also exist independently.

### Delivery and Instruction
- **Course 1:N Lesson** — lessons are ordered within a course.
- **Course 1:N Session** — sessions represent specific run windows or instructor-led deliveries.
- **Cohort 1:N Session (optional)** — a session can be cohort-scoped for synchronized learning.

### Learner Activity
- **Enrollment N:1 Course** and optional **N:1 Session / N:1 Cohort** — enrollment anchors learner participation context.
- **Enrollment 1:N Progress** — progress snapshots/events track updates over time.
- **Course 1:N Assessment** and optional **Lesson 1:N Assessment** — assessments can be course-level or lesson-level.
- **Enrollment 1:N Assessment Attempt (logical extension)** — attempts evaluate learner performance and feed progress decisions.

### Achievement
- **Credential N:1 Enrollment** — credential issuance is tied to a specific learner-course participation record.
- **Credential N:1 Course** and optional **N:1 Program** — supports both course certificates and broader program credentials.

## Compatibility Mapping to Repository Entities

| This model entity | Repository-compatible entity | Compatibility note |
| --- | --- | --- |
| Course | Course | Direct mapping (`Course`). |
| Lesson | Lesson | Direct mapping (`Lesson`). |
| Enrollment | Enrollment | Direct mapping (`Enrollment`). |
| Progress | Progress | Direct mapping (`Progress`). |
| Credential | Certificate | `Credential` is the canonical abstraction; `Certificate` is a supported credential subtype and can be persisted via existing certificate structures without breaking compatibility. |

## Data Ownership and Boundary Rules
- Institution-scoped entities (`Program`, `Course`, `Cohort`, `Credential`) must carry `institution_id`.
- Learner-state entities (`Enrollment`, `Progress`) inherit institution ownership from enrollment and are immutable across institutions.
- Content entities (`Course`, `Lesson`, `Assessment`) are managed by content/learning domains.
- Achievement entities (`Credential` / `Certificate`) are managed by certification/compliance domain with auditable issuance metadata.

## QC LOOP

### Iteration 1 — Initial Evaluation

| Category | Score (1–10) | Notes |
| --- | --- | --- |
| Schema simplicity | 9 | Clear entities, but credential naming could cause ambiguity with existing `Certificate`. |
| Extensibility | 9 | Good optional links, but assessment attempts not explicitly called out as extension boundary. |
| Education model compatibility | 10 | Institution → Program → Cohort/Session/Course structure aligns with LMS operations. |
| Data ownership clarity | 9 | Ownership mostly clear, but inheritance for learner-state needed stronger wording. |

**Weaknesses identified (<10):**
1. Potential ambiguity between `Credential` and existing `Certificate`.
2. Missing explicit mention that `AssessmentAttempt` is a logical extension relation of `Enrollment`.
3. Ownership inheritance rule for learner-state required tighter definition.

**Corrections applied:**
- Added explicit compatibility rule: `Certificate` is a `Credential` subtype.
- Added explicit relationship note: `Enrollment 1:N Assessment Attempt (logical extension)`.
- Added ownership rule that `Enrollment` and `Progress` are institution-inherited and non-transferable.

### Iteration 2 — Re-evaluation After Corrections

| Category | Score (1–10) | Notes |
| --- | --- | --- |
| Schema simplicity | 10 | Canonical naming + subtype mapping removes ambiguity. |
| Extensibility | 10 | Extension point for assessment attempts and program/course optionality is explicit. |
| Education model compatibility | 10 | Supports cohort-based and session-based delivery, plus reusable course cataloging. |
| Data ownership clarity | 10 | Ownership and boundary responsibilities are explicit and enforceable. |

**QC Result:** All categories are now **10/10**.
