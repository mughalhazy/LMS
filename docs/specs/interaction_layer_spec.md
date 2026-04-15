# Interaction Layer Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.9 | **Status:** BUILT — `services/interaction-service/` implemented (CGAP-025, T3-D, 2026-04-05) | **DF-03 resolved 2026-04-11**

---

> ✓ **BUILD STATUS: BUILT.** `services/interaction-service/service.py` was implemented in Phase B T3-D (CGAP-025, 2026-04-05). All three capability domains below are implemented. See Drift Flag DF-03 — resolved.

---

## Capability Domain: §5.9 Interaction Layer Capabilities

Covers: conversational interaction | action-based replies | stateful interaction flows

---

## Intent

The interaction layer enables platforms to communicate with learners and operators through conversational, action-driven channels (WhatsApp-style) rather than dashboard-driven interfaces. This is a first-class capability domain per Master Spec §8 UX principle: "interaction-first, not dashboard-first."

---

## Capabilities to Be Built

### CAP-CONVERSATIONAL-DELIVERY
- Deliver structured messages via WhatsApp (and other conversational channels) with rich formatting
- Support: text, quick replies, list pickers, media attachments
- Integrates with: `integrations/communication/whatsapp_adapter.py`

### CAP-ACTION-BASED-REPLIES
- Parse learner/operator replies and trigger platform actions
- Examples: reply "1" to enroll, reply "pay" to initiate payment flow
- Integrates with: `services/workflow-engine/` for action execution

### CAP-STATEFUL-INTERACTION-FLOWS
- Maintain conversation state across multiple message exchanges
- Multi-step flows: enrollment wizards, quiz delivery, fee payment via WhatsApp
- Session state must survive channel disconnections and timeouts

---

## Service Implementation

**Service path:** `services/interaction-service/service.py` ✓ BUILT (CGAP-025, 2026-04-05)

**What was built:**
- `CAP-CONVERSATIONAL-DELIVERY` — `build_action_message()` enforcing BC-INT-01 for all 6 mandatory message types (fee overdue, attendance alert, enrollment invitation, at-risk, pending approval, new batch open), each with embedded action options.
- `CAP-ACTION-BASED-REPLIES` — `handle_inbound_reply()` classifies to 13 action categories with BC-INT-01 idempotency via `action_id` deduplication within session.
- `CAP-STATEFUL-INTERACTION-FLOWS` — `get_or_create_session()` with `ConversationSession` tracking `flow_step`/`context`/`history` across exchanges.
- BC-INT-02 persona-aware routing: learner/operator/manager/instructor command shortcuts (status/today/pending/approve/remind); `send_onboarding_message()` with role-specific available commands; `get_persona_commands()` per persona type.

**Dependencies wired:**
- `integrations/communication/whatsapp_adapter.py` ✓
- `services/workflow-engine/` ✓
- `services/notification-service/` ✓
- `services/system-of-record/` ✓

---

## Building Blocks (All Exist)

| Asset | Path | Status |
|---|---|---|
| Interaction service | `services/interaction-service/service.py` | BUILT (CGAP-025) |
| WhatsApp adapter | `integrations/communication/whatsapp_adapter.py` | EXISTS |
| WhatsApp integration tests | `validation/tests/test_whatsapp_integration_consolidation.py` | EXISTS |
| Notification orchestration | `services/notification-service/orchestration.py` | EXISTS |
| Workflow engine | `services/workflow-engine/service.py` | EXISTS |

---

## Boundary Rules

- Interaction layer handles channel delivery and state — it does NOT own learning, enrollment, or payment logic
- All triggered actions route through existing capability services via the workflow engine
- Conversation state is stored in the interaction service — not in the learning or operations services

---

## References

- Master Spec §5.9, §8 (interaction-first UX principle), §7 (async interaction market enforcement)
- `docs/architecture/communication_adapter_interface_contract.md`
- `docs/architecture/DOC_NORM_02_market_enforcements_capability_map.md` (items 2, 3)

---

## Behavioral Contracts (BOS Overlay — 2026-04-04)

*The following sections add behavioral requirements per `platform_behavioral_contract.md`. These contracts govern the interaction layer once built, and also define the behavioral target for the build.*

---

### BC-INT-01 — Action Inside Message (BOS§6.1 / GAP-007)

**Rule:** Every outbound message sent by the platform MUST support at least one executable action that can be completed without the recipient opening a dashboard or app.

**Specification:**
- Outbound messages from `notification-service` and the interaction layer must carry embedded action options wherever an action is relevant to the message content.
- Actions must be executable via channel-native reply mechanisms: numbered replies (WhatsApp), inline buttons (in-app), linked commands (email), or SMS reply keywords.
- The workflow engine must accept action triggers from the interaction layer and route them to the appropriate capability service.

**Required message types with mandatory embedded actions:**

| Message Type | Required Embedded Action(s) |
|---|---|
| Fee overdue reminder | "Reply PAY to initiate payment" or "Reply WAIVE with reason" |
| Attendance alert | "Reply 1 for Present, 2 for Absent, 3 for Late" |
| Enrollment invitation | "Reply ENROLL to confirm" or "Reply INFO for details" |
| At-risk learner alert | "Reply CONTACT to send learner a message" |
| Pending approval | "Reply APPROVE or REJECT" |
| New batch open | "Reply JOIN to reserve a seat" |

- The system must never send an alert or notification about a situation that requires action without also embedding the action trigger in the same message.
- Action replies must be idempotent — duplicate replies must not trigger duplicate actions.

---

### BC-INT-02 — Conversational-First Interaction for All Personas (BOS§2.3 / GAP-017)

**Rule:** The interaction layer MUST support conversational-first operation for ALL platform user types — operators, managers, instructors, and learners — not only for AI tutor interactions.

**Scope expansion beyond current spec:**
The current spec focuses on learner-facing conversational delivery. This contract expands the scope to all personas:

| Persona | Required Conversational Capability |
|---|---|
| Learner | Enroll in course, check progress, access lesson, submit assessment, get AI tutor help |
| Operator / Admin | View daily action list, mark attendance, chase fees, approve enrollments, send announcements |
| Manager / HR | View team completion, assign training, get at-risk alerts, approve requests |
| Instructor | Mark attendance, send message to batch, view today's session roster |

**Specification:**
- For each persona, the top 5 most frequent daily actions must be achievable entirely through the conversational channel — no dashboard required.
- The interaction layer must maintain persona-aware conversation context: the same message command ("status") returns role-appropriate content for each persona type.
- Command shortcuts must be available for frequent actions: e.g., "status", "today", "pending", "approve [id]", "remind [batch]".
- The platform must make conversational access discoverable: new users must receive onboarding messages that explain available commands for their role.
- This does not replace dashboard access — it makes dashboard access optional for daily operations.
