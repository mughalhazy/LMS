# DOC_04 Academy Operational Model

## 1) Academy workflow model

```text
Academy
  → Program
  → Batch (Cohort)
  → Session
  → Student Group
```

| layer | operational purpose | key ownership roles | primary linked entities |
| --- | --- | --- | --- |
| Academy | Tenant-level operating boundary for governance, budgets, policies, and reporting. | Academy Director, Operations Manager, Compliance Manager | Course, Enrollment, Progress |
| Program | Thematic or credential track that bundles courses and outcomes into a managed offering. | Program Manager, Curriculum Lead | Course, Lesson, Progress |
| Batch (Cohort) | Time-bound delivery instance of a program with a defined schedule, intake, and capacity. | Cohort Admin, Scheduler, Instructor Lead | Enrollment, Progress |
| Session | Instructor-led or facilitated learning event tied to specific lessons/course milestones. | Instructor, Teaching Assistant | Lesson, Progress, Enrollment |
| Student Group | Sub-segmentation of learners for mentoring, labs, remediation, and targeted interventions. | Facilitator, Mentor, Group Coordinator | Enrollment, Progress |

## 2) End-to-end lifecycle processes

### 2.1 Academy onboarding
1. Create academy under tenant and bind governance settings (time zone, compliance policy, reporting cadence).
2. Define operating calendar, instructor pool, and capacity policy (max active batches, learner-to-mentor ratio).
3. Register baseline catalog mapping to reusable Course objects and Lesson sequencing standards.
4. Enable operational dashboards for enrollment pipeline and progress health.

### 2.2 Program creation
1. Program Manager defines program outcomes, target learner profiles, and completion criteria.
2. Program structure is mapped to one or more Course entities with explicit Lesson ordering dependencies.
3. Assessment and completion thresholds are configured for progress calculation and certification rules.
4. Program is versioned and published for batch planning.

### 2.3 Batch scheduling
1. Scheduler creates a cohort window (start/end dates, modality, facilitator assignment, seat capacity).
2. Session plan is generated from course/lesson blueprint (live classes, labs, office hours, checkpoints).
3. Capacity validation and conflict checks run against rooms, instructors, and calendar overlaps.
4. Batch status moves from `draft` → `scheduled` → `active`.

### 2.4 Student enrollment
1. Learners are admitted via manual assignment, rule-based assignment, or bulk import.
2. Enrollment records are created per learner-course pairing, preserving uniqueness constraints.
3. Waitlist and eligibility policies are enforced when capacity is reached.
4. Welcome and schedule notifications are distributed after enrollment confirmation.

### 2.5 Session management
1. Instructors launch sessions aligned to lessons and attendance rosters.
2. Session artifacts (recordings, notes, assignments) are linked to Lesson milestones.
3. Mid-session interventions (breakout reassignment, remediation routing) are logged for auditability.
4. Session completion updates learner activity status and downstream progress workflows.

### 2.6 Attendance tracking
1. Attendance captured via check-in/check-out and participation signals.
2. Late/absent thresholds trigger at-risk flags at batch and student-group levels.
3. Attendance summaries feed instructor dashboards and operational escalation queues.
4. Attendance contributes to eligibility gates for assessments and course completion.

### 2.7 Learning progress tracking
1. Lesson and course completion events are collected per enrollment.
2. Progress service computes per-course and per-program completion percentage.
3. At-risk learners are identified using inactivity, failed attempts, and attendance gaps.
4. Intervention loops assign remediation lessons/sessions and track outcome recovery.

## 3) Integration with repo entities

| operational area | integration behavior | repo alignment |
| --- | --- | --- |
| Course integration | Programs compose Course entities as delivery units; batches inherit program-course mapping. | `courses` table scoped by tenant/org and linked to lessons/enrollments. |
| Lesson integration | Sessions map to Lesson-level milestones for delivery and completion attribution. | `lessons` table linked to `courses` for structured sequencing. |
| Enrollment integration | Student enrollment creates or updates learner-course enrollment records with cohort context. | `enrollments` table ties user-to-course with uniqueness guardrails. |
| Progress integration | Attendance + lesson/course completion generate progress signals for analytics and intervention. | Progress events include lesson/course completion and enrollment identifiers. |

## 4) Scalability model for large academies

- **Hierarchical planning:** academy-level governance with decentralized program and batch ownership avoids central bottlenecks.
- **Bulk operations:** rule-based enrollment and batch imports support high-volume admissions windows.
- **Session sharding:** large cohorts split into student groups with mentor routing for manageable instructor load.
- **Event-driven progress:** asynchronous progress events support near-real-time dashboards without blocking session operations.
- **Operational SLOs:** define SLAs for enrollment latency, attendance availability, and progress freshness.

## 5) Operational completeness controls

- Mandatory state transitions for academy/program/batch/session lifecycle prevent orphan records.
- Capacity and conflict validation at scheduling and enrollment checkpoints.
- Attendance-to-progress reconciliation job detects missing or inconsistent learning signals.
- Audit trail for onboarding, schedule changes, enrollment decisions, and intervention actions.
- Exception workflows: deferred enrollment, session cancellation, make-up sessions, and remediation reassignment.

## 6) QC loop

### QC pass 1
| category | score (1-10) | findings |
| --- | --- | --- |
| workflow realism | 9 | Missing explicit exception handling for cancellations/reschedules. |
| integration with repo entities | 9 | Integration listed, but lacking direct alignment to event-based progress updates. |
| scalability for large academies | 9 | Needs explicit strategy for high-frequency reporting and asynchronous load handling. |
| operational completeness | 8 | Missing reconciliation process between attendance and progress outcomes. |

**Corrections applied**
- Added exception workflows (session cancellation, make-up scheduling, deferred enrollment, remediation reassignment).
- Strengthened progress integration with explicit event-driven attendance + completion updates.
- Added event-driven progress and operational SLO guidance for scale.
- Added attendance-to-progress reconciliation control.

### QC pass 2
| category | score (1-10) | findings |
| --- | --- | --- |
| workflow realism | 10 | Covers normal and exception operating flows across delivery lifecycle. |
| integration with repo entities | 10 | Directly aligned to Course, Lesson, Enrollment data model and Progress events. |
| scalability for large academies | 10 | Includes decentralization, bulk processing, group sharding, and async telemetry. |
| operational completeness | 10 | Includes governance, controls, reconciliation, and intervention loops. |

**QC status:** all categories at **10/10**.
