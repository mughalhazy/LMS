# Workflow Engine Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.8 | **Service:** `services/workflow-engine/`

---

## Capability Domain: §5.8 Workflow Capabilities

Covers: event-driven automation | rule engine | multi-step workflows

---

## Service Boundary

The workflow engine is the platform's automation backbone. It consumes domain events and executes pre-configured multi-step workflows without requiring code changes. It does NOT own any domain data — it orchestrates actions across domain services.

---

## Capabilities Defined

### CAP-EVENT-DRIVEN-AUTOMATION
- Trigger automated actions in response to domain events
- Example: enrollment.completed → trigger certificate issuance → send congratulations notification
- Trigger sources: any domain event on the event bus
- Action targets: any platform service that exposes an action API

### CAP-RULE-ENGINE
- Evaluate business rules against event payload and context to determine workflow path
- Rule types: condition checks, threshold comparisons, time-based triggers
- Rules are stored in config service — not hardcoded in workflow engine

### CAP-MULTI-STEP-WORKFLOWS
- Execute sequences of actions across multiple services with state tracking
- Supports: parallel steps, conditional branching, retry on failure, human approval gates
- State persistence: workflow execution state stored in workflow engine

---

## Service Files

- `services/workflow-engine/service.py` — workflow execution engine
- `services/workflow-engine/test_workflow_engine.py` — test coverage

---

## Integration

- Consumes: all domain events via event bus
- Produces: workflow action calls to domain services
- State stored in: workflow engine internal store (not SoR)

---

## References

- Master Spec §5.8
- `docs/architecture/ARCH_05_event_driven_architecture.md`
- `docs/architecture/event_bus_design.md`

---

## Behavioral Contract (BOS Overlay — 2026-04-04)

### BC-WF-01 — Default-On Automation Posture (BOS§3.1 / GAP-001)

**Rule:** All workflow automations provided by the platform MUST be active by default (opt-out), not inactive by default (opt-in).

**Specification:**
- Every workflow template shipped with the platform must have `enabled: true` as its default state in the config service.
- Tenants may disable specific automations via config — but they must actively choose to disable, not actively choose to enable.
- New tenants provisioned onto the platform must receive the full standard workflow automation bundle pre-activated as part of the onboarding capability bundle.

**Standard automations that must be default-on:**

| Event Trigger | Default Automated Action |
|---|---|
| `enrollment.completed` | Certificate issuance + congratulations notification |
| `student.absence_threshold_crossed` (3 sessions) | Admin alert + optional student nudge |
| `fee.overdue_threshold_crossed` (7 days) | Fee reminder to student/guardian |
| `learner.inactivity_threshold_crossed` (configurable, default 7 days) | Re-engagement notification |
| `batch.capacity_below_threshold` | Admin alert + optional open-seat notification |
| `assessment.failed` | Remediation suggestion to learner + instructor alert |

- The list of default-on automations is stored in the config service and can be extended by tenants or platform admins — it is not hardcoded in the workflow engine.
- Automation state changes (enable/disable) must be logged in the audit layer.
