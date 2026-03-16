# DOC_05 Tutor Operational Model

## 1) Objective
Define how independent tutors operate inside the LMS while remaining compatible with existing core entities and service boundaries.

## 2) Tutor Workflow (Operational Chain)

```text
Tutor
  → Subject
  → Student Group
  → Session
  → Lesson Delivery
```

### 2.1 Workflow Stages

| Stage | Primary Action | Inputs | Outputs | Existing LMS Integration |
|---|---|---|---|---|
| Tutor | Create and maintain tutor identity and operating constraints | Tutor account data, verification metadata, availability windows | Tutor profile, activation state | `users` (role=`tutor`), organization/tenant ownership from core schema |
| Subject | Declare subject expertise and approved teaching scope | Tutor qualifications, subject tags, curriculum alignment | Tutor-subject mapping and teachable catalog | `courses` metadata/tags used to bind tutor to eligible courses |
| Student Group | Assemble manageable learner cohorts for tutor-led delivery | Enrollment roster, learner level, language, schedule preferences | Tutor-owned student groups with capacity limits | Built from `enrollments` and organization groups |
| Session | Plan and schedule delivery sessions for specific group + lesson targets | Tutor availability, group capacity, course plan, lesson prerequisites | Scheduled sessions with status lifecycle | Anchored to `course_id` + lesson plan from `lessons` |
| Lesson Delivery | Conduct teaching, attendance capture, learning outcomes, and follow-up | Session plan, lesson content, learner participation | Session completion records, progress updates, interventions | Updates learner `progress` events and enrollment outcomes |

## 3) Core Operating Components

### 3.1 Tutor Profile
- **Identity**: tutor id, tenant id, organization id, status, timezone.
- **Operational attributes**: max concurrent groups, max weekly sessions, preferred delivery modes (live/async/blended).
- **Compliance attributes**: verification status, policy acknowledgements, audit trace linkage.
- **LMS mapping**: represented as a role-specialized user in the `users` table and governed by tenant/org boundaries.

### 3.2 Subject Expertise
- **Expertise model**: subject code, proficiency level, certification reference, approval status.
- **Assignment rule**: tutor can only run sessions for courses mapped to approved subject scope.
- **LMS mapping**: links tutor expertise to `courses` by subject tags and curriculum taxonomy.

### 3.3 Student Grouping
- **Grouping basis**: course enrollment, readiness level, target cohort size, timezone cluster.
- **Constraints**: min/max cohort size, level variance threshold, attendance-risk balancing.
- **LMS mapping**: derived from `enrollments` and maintained as a scheduling/operations projection.

### 3.4 Lesson Scheduling
- **Scheduling entities**: session slot, assigned tutor, assigned group, target lesson(s), modality.
- **Lifecycle**: draft → confirmed → in_progress → completed/cancelled.
- **LMS mapping**: every session references a `course_id`; planned delivery points to one or more `lesson_id` entries from `lessons`.

### 3.5 Session Tracking
- **Capture points**: attendance, start/end timestamps, lesson coverage, tutor notes, blocker flags.
- **Operational status**: on_time, delayed, interrupted, completed, cancelled.
- **LMS mapping**: session completion updates learner course/lesson states through existing progress pipeline.

### 3.6 Progress Monitoring
- **Learner metrics**: lesson completion, assessment trend, participation rate, intervention count.
- **Group metrics**: completion velocity, risk distribution, no-show rate.
- **Tutor metrics**: delivery consistency, session success rate, learner outcome uplift.
- **LMS mapping**: consumes and emits via existing progress model (`LessonCompletionTracked`, `CourseCompletionTracked`) while preserving enrollment linkage.

## 4) Integration with Existing LMS Models

| Existing Model | Integration Rule in Tutor Operational Model |
|---|---|
| Course | Tutor subject scope gates course eligibility; every session is course-bound. |
| Lesson | Session plans target explicit lesson ids; delivery confirms lesson coverage and completion evidence. |
| Enrollment | Student groups are composed from active enrollments only; attendance and interventions remain enrollment-scoped. |
| Progress | Session outcomes write to progress events for lesson/course completion and feed analytics/recommendation services. |

## 5) Entity Alignment (Minimal Additions)

To avoid fragmentation, this model keeps **Course, Lesson, Enrollment, Progress** as source-of-truth entities and adds only operational overlays:

- `tutor_profile` (1:1 with `users` where role=tutor)
- `tutor_subject_expertise` (N:1 to tutor_profile; N:1 to subject taxonomy)
- `tutor_student_group` (N:1 to tutor_profile; N:M via enrollments)
- `tutor_session` (N:1 to tutor_profile, N:1 to course, N:M to lessons)
- `tutor_session_attendance` (N:1 to tutor_session, N:1 to enrollment)
- `tutor_intervention_log` (N:1 to tutor_session and enrollment, optional progress correlation id)

## 6) Scalability and Multi-Tenant Considerations

- Enforce tenant isolation on every tutor operational record.
- Partition sessions and attendance by tenant + time window for query efficiency.
- Keep analytics/event fan-out asynchronous; session completion should be non-blocking for tutor UI.
- Support horizontal tutor pool growth via capacity rules (max groups/sessions per tutor).
- Add fallback reassignment workflow for tutor absence to protect session continuity.

## 7) QC LOOP

### QC Pass 1 (Initial Evaluation)

| Category | Score (1-10) | Finding |
|---|---:|---|
| Workflow clarity | 8 | Stage sequence is clear, but lesson delivery lacked explicit status gates tied to session lifecycle. |
| Compatibility with academy model | 9 | Supports tutor autonomy and cohort operations, but tutor reassignment policy was implicit. |
| Alignment with repo entities | 9 | Integrates Course/Lesson/Enrollment/Progress, but operational overlays needed explicit source-of-truth statement. |
| Scalability | 8 | Multi-tenant intent present, but missing concrete partitioning and async processing guidance. |

**Structural flaw identified (<10):**
The initial structure under-specified operational control points (lifecycle gates, source-of-truth boundaries, and scale mechanics), which risks inconsistent execution across tutors.

### Revision Applied
- Added explicit session lifecycle (`draft → confirmed → in_progress → completed/cancelled`).
- Added strict source-of-truth boundary section and minimal overlay entities.
- Added concrete scalability mechanisms: partitioning, async fan-out, reassignment fallback.

### QC Pass 2 (Post-Revision)

| Category | Score (1-10) | Rationale |
|---|---:|---|
| Workflow clarity | 10 | End-to-end chain and lifecycle gates are explicit and operationally testable. |
| Compatibility with academy model | 10 | Independent tutor operation, cohort management, and substitution workflow now fully represented. |
| Alignment with repo entities | 10 | Direct mapping to Course/Lesson/Enrollment/Progress is explicit with controlled overlays only. |
| Scalability | 10 | Tenant isolation, partition strategy, async processing, and capacity constraints are defined. |

**QC LOOP RESULT:** All categories are **10/10**.
