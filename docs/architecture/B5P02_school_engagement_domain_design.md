# B5P02 — School Engagement Domain Design

> **CAPABILITY DOMAIN EXTENSION (2026-04-04):** This document defines a use-case capability domain extension — a group of capabilities designed for the school engagement use-case profile. It is NOT a segment-forked product or a separate platform branch. All capabilities described here are accessed via the entitlement system using `segment_type` and `plan_type` as selection inputs. The core platform (learning, enrollment, progress, certification) remains unchanged. Reference: Master Spec §5.19, `docs/architecture/domain_capability_extension_model.md`.
>
> **DF-05 RESOLVED (2026-04-11):** Body text audit complete — no segment-product framing found. Document uses domain-appropriate terms ("school engagement", "teacher/parent/student roles") throughout. `segment_type` appears only as a technical entitlement input in this preamble.

## 1) Purpose

Design a **School Engagement domain** that operationalizes classroom-facing school workflows while maximizing **real-time parent visibility**.

Scope includes:
- Attendance tracking
- Grading publication and correction workflow
- Parent portal integration
- Homework/classwork assignment visibility
- Teacher-parent communication handoff

This domain is optimized for school execution (teacher, parent, student roles) and explicitly avoids duplication with learning-core and academy-operations responsibilities.

---

## 2) Guardrails (QC FIX RE QC 10/10)

1. **No overlap with academy operations**
   - Excludes admissions, fee plans, commerce checkout, and academy franchise operations.
   - Consumes student roster and section assignment as upstream inputs only.

2. **No duplication with learning core**
   - Learning core remains source of truth for content authoring, lesson sequencing, mastery/attempt scoring, and pedagogical recommendation logic.
   - School Engagement stores only engagement-facing snapshots and publication states needed for parent and student visibility.

3. **Parent visibility first**
   - Every attendance mark, grade publication, and assignment status change must produce a parent-visible state update within real-time SLA.
   - Parent-facing timeline is a first-class read model, not an afterthought.

4. **Clear role separation**
   - **Teacher:** captures attendance, publishes grades, posts assignment outcomes, initiates communication requests.
   - **Parent/Guardian:** reads child engagement status, acknowledges updates, responds through portal-mediated channels.
   - **Student:** views own attendance/grades/homework status and teacher feedback scoped to self.

5. **No communication logic duplication**
   - This domain never decides channel routing, template selection, throttling, or delivery retries.
   - It emits communication intents/events to the **Communication Engine (Batch 4)** and consumes delivery outcomes for status display.

---

## 3) Domain Boundary and Integrations

## 3.1 In-Scope Capabilities

- Attendance session management and per-student status capture
- Gradebook publication states (draft → published → corrected)
- Assignment engagement view (assigned/submitted/overdue/reviewed)
- Parent visibility timeline and acknowledgment state
- Engagement event emission to communication engine

## 3.2 Out-of-Scope Capabilities

- Course/lesson authoring, rubric scoring engines, or mastery logic (learning core)
- Enrollment billing, discounts, checkout, fee collection (academy operations/commerce)
- SMS/email/WhatsApp dispatch behavior and channel fallback policies (communication engine)

## 3.3 Required Integrations

1. **Learning System (required)**
   - Pulls roster-section context, assignment metadata pointers, and assessment outcome references.
   - Receives published engagement states back for learner dashboards.

2. **Communication Engine — Batch 4 (required)**
   - Receives normalized engagement communication intents.
   - Returns delivery/engagement receipts (sent/delivered/read/failed) for portal display.

---

## 4) Core Components

## 4.1 Attendance Tracking Service

Responsibilities:
- Create attendance session per class period/date.
- Capture statuses: `present`, `absent`, `late`, `excused`.
- Support teacher correction window with audit history.
- Publish parent-visible absence/late updates in near real-time.

Key invariants:
- One final status per student per session version.
- All corrections require actor + reason.
- Published attendance changes must emit parent visibility event.

## 4.2 Grade Publication Service

Responsibilities:
- Accept grade entries from teacher workflow as `draft`.
- Publish grades to student/parent portal when teacher confirms.
- Manage correction chain (`published` → `corrected`) with immutable prior versions.

Key invariants:
- Draft grades are teacher-only.
- Parent and student can only view published/corrected versions.
- Correction must preserve prior value and timestamp lineage.

## 4.3 Assignment Engagement Service

Responsibilities:
- Maintain assignment engagement state:
  - `assigned`
  - `submitted`
  - `late_submitted`
  - `missing`
  - `reviewed`
- Surface classwork/homework completion and overdue indicators to parent and student views.
- Attach teacher feedback summary references (not full content ownership).

## 4.4 Parent Visibility Read Model

Responsibilities:
- Build child-centric timeline across attendance, grades, and assignments.
- Provide unified parent portal query endpoints with low-latency read patterns.
- Track acknowledgment markers (`unseen`, `seen`, `acknowledged`).

## 4.5 Engagement Communication Adapter (Domain-side)

Responsibilities:
- Transform domain events into communication-intent payloads.
- Enforce idempotent intent keys.
- Persist outbound intent status mirror.

Non-responsibilities:
- No template rendering orchestration.
- No direct channel provider integrations.
- No retry policy ownership.

---

## 5) Role-Based Access Model (Teacher / Parent / Student)

| Action | Teacher | Parent | Student |
|---|---|---|---|
| Mark attendance | Create/Update own class sessions | No | No |
| View attendance | Own class + assigned students | Linked children only | Self only |
| Enter/edit draft grades | Yes | No | No |
| Publish grades | Yes (with policy checks) | No | No |
| View published grades | Yes | Linked children only | Self only |
| View homework/classwork status | Yes | Linked children only | Self only |
| Acknowledge updates | Optional | Yes | Optional/self |
| Trigger communication intent | Yes (through domain action) | Reply via portal flow | No direct trigger |

Access enforcement notes:
- Parent-child linkage is mandatory for parent reads.
- Multi-child parents see partitioned timelines per child.
- Student endpoints never expose sibling data.

---

## 6) Data Contracts (Canonical Domain Objects)

## 6.1 AttendanceRecord

```json
{
  "attendance_record_id": "att_01",
  "tenant_id": "t_01",
  "school_id": "sch_01",
  "section_id": "sec_09",
  "session_date": "2026-03-30",
  "student_id": "stu_100",
  "status": "late",
  "marked_by_teacher_id": "tea_22",
  "version": 2,
  "reason_code": "transport_delay",
  "published_at": "2026-03-30T08:05:00Z"
}
```

## 6.2 GradePublication

```json
{
  "grade_entry_id": "gr_778",
  "tenant_id": "t_01",
  "student_id": "stu_100",
  "subject_id": "math_g7",
  "assessment_ref_id": "asmt_450",
  "score_value": 84,
  "score_scale": 100,
  "state": "published",
  "version": 1,
  "entered_by_teacher_id": "tea_22",
  "published_at": "2026-03-30T10:12:00Z"
}
```

## 6.3 AssignmentEngagement

```json
{
  "assignment_engagement_id": "asg_881",
  "tenant_id": "t_01",
  "student_id": "stu_100",
  "assignment_ref_id": "learn_hw_309",
  "assignment_type": "homework",
  "status": "submitted",
  "due_at": "2026-03-31T23:59:00Z",
  "submitted_at": "2026-03-30T17:21:00Z",
  "teacher_feedback_ref_id": "fb_62"
}
```

## 6.4 ParentTimelineItem

```json
{
  "timeline_item_id": "pt_991",
  "parent_id": "par_20",
  "student_id": "stu_100",
  "item_type": "attendance_absence|grade_published|assignment_missing",
  "event_ref_id": "att_01",
  "visibility_state": "unseen",
  "created_at": "2026-03-30T08:06:00Z"
}
```

---

## 7) Event Contracts and Integration Handshakes

## 7.1 Domain Events (Produced)

- `school.attendance.marked.v1`
- `school.attendance.corrected.v1`
- `school.grade.published.v1`
- `school.grade.corrected.v1`
- `school.assignment.status_changed.v1`
- `school.parent.timeline_item_created.v1`

## 7.2 Communication Intents (Produced to Batch 4 Engine)

- `comm.intent.school.attendance_alert.v1`
- `comm.intent.school.grade_update.v1`
- `comm.intent.school.assignment_alert.v1`

Payload principle:
- Include `tenant_id`, `student_id`, `guardian_ids[]`, `event_type`, `event_time`, `portal_deeplink`, `idempotency_key`.
- Exclude channel instructions and template-rendering directives.

## 7.3 Delivery Outcomes (Consumed from Communication Engine)

- `comm.delivery.sent.v1`
- `comm.delivery.delivered.v1`
- `comm.delivery.read.v1`
- `comm.delivery.failed.v1`

Usage:
- Update parent timeline communication badge states only.
- Do not attempt channel-level fallback inside this domain.

---

## 8) Key Workflows

## 8.1 Attendance Workflow (Teacher → Parent Visibility)

1. Teacher opens class attendance session.
2. Teacher marks each student status.
3. Service validates one status per student and persists versioned records.
4. Parent Visibility model updates immediately for relevant guardians.
5. Domain emits `school.attendance.marked.v1`.
6. Communication intent `comm.intent.school.attendance_alert.v1` sent to Batch 4 engine.
7. Delivery outcomes are reflected in parent portal timeline badges.

## 8.2 Grading Workflow (Teacher Publication → Parent + Student)

1. Teacher enters grades in draft mode.
2. Teacher confirms publish action for selected students/assessment.
3. Grade Publication Service transitions entries to `published` with immutable version.
4. Student and parent portals fetch newly published grade entries.
5. Domain emits `school.grade.published.v1`.
6. Communication intent `comm.intent.school.grade_update.v1` sent to Batch 4 engine.
7. If correction is needed, new `corrected` version is created and prior version retained.

## 8.3 Parent Update Workflow (Unified Timeline)

1. Any attendance/grade/assignment update creates normalized timeline item.
2. Parent portal marks item `seen` when opened and `acknowledged` on explicit guardian action.
3. Teacher sees acknowledgment state but not parent private channel metadata.
4. Student sees own item status without guardian response details.
5. Communication outcome events update timeline communication status indicators.

---

## 9) Real-Time Parent Visibility SLA and Tracking

Minimum expectations:
- Parent timeline write latency target: **< 5 seconds** from domain event creation.
- Read model freshness target: **99% under 10 seconds**.
- Idempotent event processing to avoid duplicate parent alerts.

Student tracking views include:
- Daily attendance streak and absence count.
- Published grade trend (subject/time).
- Assignment completion and missing-work counters.

---

## 10) QC Acceptance Checklist (Pass Criteria)

- [x] No academy operations overlap (no billing/admission/commerce logic).
- [x] No learning core duplication (no content sequencing/scoring engine ownership).
- [x] Parent visibility is explicit, real-time, and first-class.
- [x] Role separation is clear and enforced (teacher/parent/student).
- [x] Communication logic is delegated to Batch 4 engine; only intents/events are handled here.

