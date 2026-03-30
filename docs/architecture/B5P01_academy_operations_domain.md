# B5P01 — Academy Operations Domain

## 1) Purpose

Define an **operations-only academy domain** for tuition centers and coaching networks that governs:
- batch/class operations
- enrollment operations tracking
- attendance capture and compliance
- fee operations status tracking (integrated with commerce)
- branch/franchise operational control

This domain is intentionally designed to:
1. Reuse existing learning and commerce ownership boundaries.
2. Orchestrate cross-domain workflows without duplicating core logic.
3. Support both small single-branch academies and large multi-branch networks.

---

## 2) Scope Boundaries (QC FIX RE QC 10/10)

## 2.1 In scope (operations ownership)

1. **Batch/Class Operations**
   - Branch-level class batch creation templates.
   - Capacity and seat utilization operations view.
   - Faculty assignment and substitution planning.
   - Operational schedule exceptions (holiday, makeup, room changes).

2. **Enrollment Operations Tracking**
   - Intake-to-active operational pipeline visibility.
   - Enrollment state transitions from an operations perspective.
   - Waitlist, transfer, and branch reassignment operations.

3. **Attendance Operations**
   - Session attendance capture workflows.
   - Late arrival / excused absence operations policies.
   - Attendance exception queue and escalation.

4. **Fee Operations Tracking (integration layer only)**
   - Track fee state for operations actions (clearance holds, reminders, escalation).
   - Consume invoice/payment/subscription states from commerce systems.
   - Trigger communication workflows for reminders and notices.

5. **Branch/Franchise Operations**
   - Branch activation and operating calendar setup.
   - Branch-level service SLAs and runbooks.
   - Franchise governance overlays (policy packs, reporting, audits).

## 2.2 Explicit non-goals (duplication prevention)

1. **No learning core duplication**
   - Does not own course, lesson, content, assessment, or progression semantics.

2. **No commerce core duplication**
   - Does not own pricing, checkout, invoices, receipts, payment orchestration, or ledgers.

3. **No communication channel implementation**
   - Does not send SMS/email/WhatsApp directly.
   - Emits communication intents and consumes delivery outcomes.

---

## 3) Domain Model (Operations-Focused)

## 3.1 Core aggregates

1. **OperationsBranch**
   - `branch_id`, `tenant_id`, `status`, `region_code`, `timezone`, `operating_calendar_id`, `capacity_profile`.

2. **OperationsBatch**
   - `ops_batch_id`, `branch_id`, `cohort_ref`, `delivery_pattern`, `seat_capacity`, `assigned_staff_refs`, `status`.

3. **EnrollmentOpsRecord**
   - `enrollment_ops_id`, `student_id`, `ops_batch_id`, `ops_state`, `state_reason`, `intake_channel`, `risk_flags`.

4. **AttendanceOpsRecord**
   - `attendance_ops_id`, `session_ref`, `student_id`, `attendance_status`, `mark_source`, `exception_flag`.

5. **FeeOpsStatus**
   - `fee_ops_id`, `student_id`, `enrollment_ref`, `commerce_invoice_ref`, `ops_fee_state`, `risk_level`, `next_action`.

6. **BranchPolicyPack**
   - `policy_pack_id`, `branch_id`, `attendance_policy`, `transfer_policy`, `late_fee_policy_ref`, `escalation_matrix`.

## 3.2 Service components

- **Batch Operations Service**: branch class-run management and seat operations.
- **Enrollment Operations Service**: operational pipeline and reassignment workflow.
- **Attendance Operations Service**: capture, exception handling, and compliance export.
- **Fee Operations Tracker**: fee-state read model + operational actions.
- **Branch Operations Governance Service**: branch policy, hierarchy, and operating health.

---

## 4) Integration Contracts (No Ownership Violation)

## 4.1 Learning system integration (existing repo)

Consume references/events from learning-owned services:
- `course_ref`, `cohort_ref`, `session_ref`, `instructor_ref`, `learner_ref`.
- Events such as session lifecycle updates and learning enrollment activation.

Operations domain behavior:
- Maintains operational mirrors (`*_ref`) only.
- Uses learning lifecycle signals to open/close attendance windows.

## 4.2 Commerce system integration (Batch 3)

Consume commerce-owned states:
- order confirmation status
- invoice status
- installment/payment status
- outstanding balance indicators

Operations domain behavior:
- Builds **fee operations state** for branch teams (`clear`, `watch`, `hold`, `escalated`).
- Never computes amount due or payment schedules.

## 4.3 Communication workflows integration (Batch 4)

Emit communication intents:
- `ops.attendance.absence_alert.requested`
- `ops.fee.reminder.requested`
- `ops.enrollment.incomplete_followup.requested`
- `ops.branch.notice.requested`

Consume outcomes:
- delivery result summary (`delivered`, `failed`, `retry_scheduled`)
- preferred channel performance tags for future routing.

---

## 5) Lifecycle & State Machines

## 5.1 Enrollment operations state machine (business vs academic separation)

Operational states:
- `lead_captured`
- `screening_pending`
- `documents_pending`
- `commerce_clearance_pending`
- `seat_provisionally_reserved`
- `active_in_batch`
- `branch_transfer_pending`
- `on_hold`
- `closed`

Boundary enforcement:
- Academic completion/certification outcomes remain in learning domain.
- Financial settlement truth remains in commerce domain.

## 5.2 Attendance operations state machine

Attendance states:
- `unmarked`
- `present`
- `late`
- `absent_excused`
- `absent_unexcused`
- `exception_review`
- `locked`

Controls:
- Lock window configurable by branch policy.
- Override requires role + reason code + audit log.

## 5.3 Fee operations state machine

Fee operations states:
- `clear`
- `upcoming_due_watch`
- `payment_overdue_watch`
- `attendance_hold_candidate`
- `escalated_to_counselor`
- `resolved`

Controls:
- Transition only via commerce event inputs + configured policy thresholds.
- Operations can apply holds/workflows but not alter invoices/payments.

---

## 6) Core Workflows

## 6.1 Workflow A — Enrollment (operations orchestration)

1. Branch ops creates intake window and batch seat plan.
2. Student enters `lead_captured` in Enrollment Ops.
3. Screening/doc checks progress through ops states.
4. Commerce integration reports payment/plan clearance.
5. On clearance, ops marks `seat_provisionally_reserved` then `active_in_batch`.
6. Communication workflow triggered for onboarding messages.
7. Learning enrollment reference is linked; operations dashboard updated.

Outputs:
- enrollment queue metrics
- branch conversion funnel
- incomplete enrollment follow-up intents

## 6.2 Workflow B — Attendance (daily branch operations)

1. Session schedule reference arrives from learning/session system.
2. Attendance window opens for each session roster.
3. Faculty/coordinator marks attendance.
4. Exceptions (late bulk edits, medical note, system mismatch) route to review queue.
5. After lock cutoff, attendance status is finalized.
6. Absence pattern thresholds trigger communication intents.

Outputs:
- daily branch attendance compliance score
- per-batch risk list (chronic absenteeism)
- export feed for audits and parent/student communication

## 6.3 Workflow C — Fee Tracking (operations support, no billing logic)

1. Commerce emits invoice/installment/payment status events.
2. Fee Ops Tracker updates operational state per learner enrollment.
3. Rules mark watchlists and hold-candidate records by policy.
4. Branch counselor queue receives prioritized follow-up tasks.
5. Communication reminders triggered through Batch 4 workflows.
6. On commerce settlement update, status moves to `resolved` or `clear`.

Outputs:
- branch-wise overdue operations queue
- hold recommendations with policy evidence
- reconciliation report (ops state vs commerce source state)

---

## 7) Small Academy vs Large Network Operation Modes

## 7.1 Small academy mode (simple flows)

Characteristics:
- single branch or very few branches
- simpler approval chains
- manual-friendly operations

Configuration profile:
- minimal required states
- single-level escalation
- lightweight dashboards and daily digest reports

## 7.2 Large network mode (multi-branch/franchise)

Characteristics:
- regional branch clusters
- franchise governance overlays
- strict operational SLAs and audits

Configuration profile:
- hierarchical policy packs (global -> region -> branch)
- transfer workflows across branches
- role-segregated queue ownership and audit trails
- capacity forecasting and SLA heatmaps

Scalability mechanism:
- same aggregates + state machines, policy-driven behavior differences.
- no forked domain models between small and large customers.

---

## 8) Academic vs Business Flow Separation

## 8.1 Academic flow signals (from learning)
- session schedules
- curriculum progression context
- learner academic status references

## 8.2 Business flow signals (from commerce)
- invoice/payment/subscription status
- financial compliance checkpoints
- refund/adjustment effects on operational eligibility

## 8.3 Operations flow (this domain)
- translates academic + business signals into branch-operational actions:
  - who to schedule
  - who to follow up
  - who to escalate
  - what to hold/release operationally

**Rule:** operations domain can gate operational actions (e.g., attendance hold) but cannot mutate academic grading or financial ledgers.

---

## 9) Event Contract Examples

```json
{
  "event_name": "ops.enrollment.state_changed",
  "tenant_id": "t_001",
  "branch_id": "b_karachi_01",
  "student_id": "stu_1001",
  "ops_batch_id": "ob_2026_spring_math",
  "previous_state": "commerce_clearance_pending",
  "new_state": "active_in_batch",
  "reason_code": "commerce_clearance_confirmed",
  "occurred_at": "2026-03-30T09:30:00Z"
}
```

```json
{
  "event_name": "ops.fee.watchlist.updated",
  "tenant_id": "t_001",
  "branch_id": "b_lahore_central",
  "student_id": "stu_3344",
  "enrollment_ref": "enr_abc",
  "ops_fee_state": "payment_overdue_watch",
  "commerce_refs": {
    "invoice_id": "inv_998",
    "payment_plan_id": "pp_442"
  },
  "next_action": "counselor_followup",
  "occurred_at": "2026-03-30T10:10:00Z"
}
```

---

## 10) QC Conformance Checklist (QC FIX RE QC 10/10)

1. **No duplication with learning core**: only mirrors learning refs/events; no course/content/assessment ownership.
2. **No duplication with commerce logic**: consumes commerce truth for financial state; does not compute billing/pricing.
3. **Operations-focused only**: all aggregates and workflows center on branch operations execution.
4. **Scales across sizes**: policy-driven single model supports small academy and large network modes.
5. **Clear academic vs business separation**: learning and commerce remain source domains; operations translates them into action queues.
6. **Integration-ready by contract**: explicit event intents for communication workflows and ingest contracts for learning/commerce.

