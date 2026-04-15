# Operations OS Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.10 | **Service:** `services/operations-os/`

---

## Capability Domain: §5.10 Admin Operations Capabilities

Covers: operational dashboards | action prioritisation | system alerts

---

## Scope

The Operations OS is the admin-facing operational intelligence layer. It aggregates operational state across the platform and surfaces prioritised actions for operators, academy admins, and platform administrators. It is a read-optimised layer — it consumes events and state from other services, never owning transactional records.

---

## Capabilities Defined

### CAP-OPERATIONS-DASHBOARD
- Real-time operational dashboards aggregating: enrollment pipeline, attendance rates, fee collection status, batch health, at-risk learner counts
- Read from: SoR (lifecycle), academy-ops (attendance), commerce (fee status)
- Shared model: `shared/models/operations_dashboard.py`
- Owner: `services/operations-os/`

### CAP-ACTION-PRIORITISATION
- Surfaces and ranks pending operator actions by urgency and impact
- Examples: overdue fee follow-ups, at-risk learners, unfilled batch slots, pending approvals
- Output: sorted action queue per operator role
- Integrates with: workflow engine for action execution

### CAP-SYSTEM-ALERTS
- Rule-based alert generation for threshold breaches and anomalies
- Examples: enrollment drop below capacity threshold, payment failure rate spike, batch completion overdue
- Delivery via: notification service
- Configuration: via config service (thresholds are config-driven, not hardcoded)

---

## Boundary Rules

- Operations OS never writes to transactional records — all writes route through owning services
- Alert rules are config-driven — stored in config service, not hardcoded in operations-os
- Dashboards are projections — eventual consistency with source-of-truth services is acceptable

---

## Service Files

- `services/operations-os/service.py` — service logic
- `services/operations-os/models.py` — data models
- `services/operations-os/qc.py` — QC validation
- `shared/models/operations_dashboard.py` — shared dashboard models

---

## References

- Master Spec §5.10
- `docs/architecture/B5P01_academy_operations_domain.md`
- `docs/specs/workflow_engine_spec.md`
- `docs/specs/notification_service_spec.md`

---

## Behavioral Contracts (BOS Overlay — 2026-04-04)

*The following sections add behavioral requirements per `platform_behavioral_contract.md` and `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md`. They constrain HOW the capabilities above must behave, not WHAT they contain.*

---

### BC-OPS-01 — Proactive Pattern Detection and Suggested Next Steps (BOS§4.1 / GAP-003)

**Rule:** The Operations OS MUST proactively detect operational patterns and surface suggested next steps to operators WITHOUT requiring the operator to query or navigate.

**Specification:**
- The system must continuously monitor state signals (attendance trends, fee collection rates, enrollment pipeline, batch health) and evaluate them against pattern thresholds.
- When a pattern threshold is crossed, the system must generate a proactive suggestion — not merely an alert — that includes the detected pattern, its implication, and a specific suggested next step.
- Suggestions must be delivered to the operator's primary active channel (dashboard queue, notification, or message) automatically.

**Required output format:**
```
Pattern: [what was detected]
Implication: [what this means]
Suggested action: [specific action with one-click trigger where possible]
```

**Examples:**
- "Attendance dropped 18% this week in Batch A → Send attendance reminder to absent students?"
- "5 students have unpaid fees overdue by 7+ days → Send fee reminder to all 5?"
- "Batch B is 40% under capacity with 3 days to enrolment close → Send open seat notification to waitlist?"

---

### BC-OPS-02 — Three-Tier Action Classification (BOS§4.2 / GAP-004)

**Rule:** All actions surfaced by the Operations OS MUST be classified into three tiers and displayed in tier order.

**Tiers:**
| Tier | Label | Definition | Examples |
|---|---|---|---|
| 1 | CRITICAL | Requires action today — financial, compliance, or dropout risk | Overdue fees >14 days, learner at drop-off point, batch oversubscribed |
| 2 | IMPORTANT | Requires action within 48 hours — operational efficiency | Attendance below 70% this week, pending approvals, at-risk learner |
| 3 | OPTIONAL | Useful but not urgent — insights and optimisation | Low engagement course, benchmark comparison, upsell opportunity |

**Specification:**
- The action queue (CAP-ACTION-PRIORITISATION) must return actions pre-classified into these tiers.
- Tier classification rules are config-driven (via config service) so thresholds can be adjusted per tenant.
- The operator interface must present CRITICAL items first, with clear visual separation between tiers.
- An operator must never have to scroll past OPTIONAL items to reach CRITICAL ones.

---

### BC-OPS-03 — Daily Action List as First-Class System Output (BOS§5.1 / GAP-005)

**Rule:** The Operations OS MUST generate a Daily Action List as a first-class structured output artifact — not merely a filtered dashboard view.

**Specification:**
- At the start of each operator's working day (configurable time, default: 08:00 local timezone), the system must produce a Daily Action List for that operator.
- The Daily Action List is a structured document, not a dashboard. It must be deliverable via notification/message channel so the operator can act without opening a UI.
- Required sections:

```
DAILY ACTION LIST — [Date] — [Operator Name / Role]

CRITICAL (requires action today):
  - [item 1]: [description] → [action link/command]
  - [item 2]: [description] → [action link/command]

IMPORTANT (action within 48h):
  - [item 1]: [description] → [action link/command]

PAYMENTS:
  - [N] unpaid fees overdue → [action]

ATTENDANCE:
  - [N] absentees yesterday → [action]

INACTIVE USERS:
  - [N] learners with no activity in [X] days → [action]
```

- The Daily Action List must be delivered to the operator's notification channel (in-app, email, WhatsApp, SMS — per tenant channel config).
- Delivery is opt-out, not opt-in.

---

### Architectural Contract: MS-REDUCE-01 — Automation Coverage (MS§10.6)

**Contract name:** MS-REDUCE-01
**Source authority:** Master Spec §10 rule 6: "System must reduce manual work."
**Enforcement scope:** Operations OS and all services that surface operational workflows.

**Rule:** Every repeatable operational action type MUST have a corresponding automation path available. A manual-only workflow for an automatable operation is a platform deficiency — not a feature.

**Automatable operation types (minimum required coverage):**

| Operation type | Required automation path | Manual-only = defect? |
|---|---|---|
| Attendance recording | Auto-trigger via session events or bulk import via message command | Yes |
| Fee collection reminders | Scheduled rule-based reminder workflows | Yes |
| Enrollment confirmation | Auto-confirm on payment completion event | Yes |
| Compliance tracking | Automated completion state tracking against required modules | Yes |
| At-risk learner alerts | Proactive risk detection and notification (BC-OPS-01) | Yes |
| Daily action list generation | Scheduled daily generation per operator (BC-OPS-03) | Yes |

**Rule for new operation types:** Any new operational action type introduced into the Operations OS or a supporting service MUST include an automation path as part of its initial delivery. "We'll automate it later" is not an acceptable delivery state for any repeatable operation.

**Why this rule exists:** MS§10 rule 6 states the system must reduce manual work. Without a named coverage contract, automatable operations default to manual workflows, and automation becomes a separate workstream that is perpetually deferred. The contract makes automation the expected default, not an enhancement.

---

### BC-OPS-04 — Zero-Dashboard Entry Mode (BOS§5.2 / GAP-006)

**Rule:** The Operations OS MUST support full operational capability without the operator ever opening a dashboard UI.

**Specification:**
- Every action in the Daily Action List must be executable via notification reply, message command, or guided flow — without requiring dashboard navigation.
- The system must support at minimum:
  - Mark attendance via message reply
  - Confirm/waive a fee via message reply
  - Send a reminder via message command
  - Approve/reject pending items via message reply
  - View today's action list via a single message command (e.g., "status")
- Zero-dashboard mode is achieved by the combination of: Daily Action List delivery (BC-OPS-03) + actionable messages (BOS§6.1, see `interaction_layer_spec.md`) + guided flows.
- This does not mean dashboards are removed — it means dashboards are optional, not required for daily operations.
