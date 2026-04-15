# Platform Behavioral Contract

**Type:** Governing Behavioral Specification | **Date:** 2026-04-04 | **BOS§:** §1, §14, §15
**Source authority:** `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md`
**Rule:** This document is additive to all service and architecture specs. Any service, feature, or interaction that conflicts with these principles must be corrected.

---

## Purpose

This document establishes the **meta-behavioral contract** for the LMS platform. It defines HOW the system must behave as experienced by users — not WHAT the system contains (that is the Master Spec's role).

Every service spec, capability spec, and architecture doc in this repo operates WITHIN the constraints defined here. If a spec is silent on a behavioral principle, this document is the tiebreaker.

---

## §1 — The System Acts as an OPERATOR, Not a Tool

### Rule
The platform must behave as an operator that thinks, acts, and guides on behalf of its users — not as a passive tool that waits for input and returns data.

### What this means in practice

| Operator Behavior (REQUIRED) | Tool Behavior (PROHIBITED) |
|---|---|
| Proactively surfaces what needs to be done | Waits for the user to open a dashboard |
| Suggests the next action based on system state | Returns raw data for the user to interpret |
| Automates repetitive tasks without being asked | Requires the user to configure automation manually |
| Guides users through complexity with smart defaults | Presents all options at once and expects configuration |
| Acts on patterns it detects (e.g., 5 unpaid fees → suggest reminder) | Stores data without acting on implications |

### Applies to
All user-facing services: `operations-os`, `notification-service`, `interaction-layer`, `analytics-service`, `reporting-service`, `manager-dashboard`, `onboarding`, and all AI services.

---

## §14 — User Psychology Alignment

### Rule
Every user interaction with the platform must be designed to reduce cognitive load, build trust through consistency, provide quick wins early, and reinforce value continuously.

### Behavioral requirements

**14.1 Reduce Cognitive Load**
- The system must never present more information than the user needs to take the next action.
- Dashboards, reports, and lists must be filtered to relevance by default — raw unfiltered views require an explicit user opt-in.
- When multiple actions are possible, the system must rank and present the most important first.

**14.2 Build Trust Through Consistency**
- The same action must produce the same result regardless of which channel, device, or interface the user uses.
- System messages must use consistent, plain language — no technical codes surfaced to non-technical users.
- If the system takes an automated action on behalf of the user, it must notify the user and allow reversal.

**14.3 Provide Quick Wins Early**
- New users and new tenants must experience a meaningful outcome (first course published, first student enrolled, first reminder sent) within the first session — without manual setup.
- Onboarding flows must be structured to deliver visible value at each step, not defer value until full configuration is complete.

**14.4 Reinforce Value Continuously**
- The system must surface moments of value proactively: completion milestones, revenue collected, attendance improved, risk avoided.
- These signals must be delivered as operator nudges ("You collected 12 fees this week") not buried in reports.

---

## §15 — Final Behavioral Principle

### Rule
The platform must THINK for the user, ACT with the user, and GUIDE the user at every interaction point.

### What this prohibits
- Showing a user data without a suggested action
- Requiring a user to navigate to find out what to do next
- Blocking a user with an error code without telling them what to do
- Automating a task as opt-in when it is universally beneficial

### What this requires
- Every page, notification, message, and report must answer: "What should the user do next?"
- Every detection of a problem must be paired with a suggested resolution
- Every capability gate must explain itself and suggest the path forward
- Every new user session must begin with the most important action for that user, not a generic home screen

---

---

## Architectural Contract: MS-UX-01 — Mobile-First UX (MS§8)

**Contract name:** MS-UX-01
**Source authority:** Master Spec §8 — mobile-first as non-negotiable UX principle.

**Rule:** ALL primary user journeys — for learners, operators, and instructors — MUST be fully functional on mobile-class devices without feature degradation.

**What "fully functional without feature degradation" means:**
- A learner must be able to start a course, complete lessons, submit assessments, and receive feedback on a mobile device without being told to switch to desktop.
- An operator must be able to view and act on the Daily Action List, respond to alerts, approve pending items, and send communications from a mobile device.
- An instructor must be able to view student progress, respond to queries, and review submissions from a mobile device.
- Dashboard-equivalent functionality must be available through mobile-native interaction patterns (list views, reply commands, progressive disclosure) — not only through complex dashboard UIs.

**What this prohibits:**
- Features that are desktop-only without a mobile-accessible equivalent.
- "Simplified" mobile views that remove core task capabilities.
- Workflows that require file upload or multi-column table interaction that is impossible on mobile without a separate "use desktop" prompt.

**Relationship to market enforcements:** MS-UX-01 applies to all user-facing surfaces. The mobile-first capability in MS-MARKET-01 covers infrastructure (offline sync, lightweight delivery). This contract covers the UX behavior layer — the surfaces must be built mobile-first, not just capable of mobile access.

---

## Architectural Contract: MS-UX-02 — Outcome-Driven UX (MS§8)

**Contract name:** MS-UX-02
**Source authority:** Master Spec §8 — outcome-driven as non-negotiable UX principle.

**Rule:** Every data surface in the platform MUST answer "what should I do next?" Raw data without a suggested action or outcome framing is a UX defect.

**What outcome-driven means in practice:**

| Surface type | REQUIRED (outcome-driven) | PROHIBITED (raw data) |
|---|---|---|
| Analytics dashboard | "3 learners haven't completed Module 2 — Send reminder?" | A table showing completion percentages with no call to action |
| Fee collection report | "7 fees overdue — Follow up now?" | A list of outstanding fees with no suggested action |
| Learner progress view | "Learner is at risk — Assign intervention?" | A progress bar at 23% with no implication surfaced |
| Enrollment pipeline | "14 learners enrolled this week — On track for batch target." | Raw enrollment count with no context |

**Relationship to BC-ANALYTICS-01:** MS-UX-02 is broader than BC-ANALYTICS-01 (insight over reports in analytics). MS-UX-02 applies to ALL surfaces — analytics, operations, billing, learner dashboards, instructor views. If a surface shows data, it must also show what to do with it.

**Enforcement:** Any new data surface delivered without an outcome framing or suggested next action is non-conformant with this contract. Surfaces must be reviewed for MS-UX-02 compliance before release.

---

## Architectural Contract: MS-SIMPLE-01 — Simplicity Preservation (MS§10.7)

**Contract name:** MS-SIMPLE-01
**Source authority:** Master Spec §10 rule 7: "Simplicity must be preserved."

**Rule:** New capabilities and configuration options MUST NOT increase operator cognitive load without explicit justification. Three sub-rules apply:

1. **Sensible defaults are mandatory.** Every new capability MUST have a sensible default configuration that works for the majority of tenants without any manual setup. A capability that requires 10 configuration steps before it is usable violates this contract.

2. **Default tenant experience must be navigable without training.** A new operator who has never used the platform must be able to complete a meaningful operational workflow (enroll a student, send a reminder, view attendance) within their first session without reading documentation.

3. **Configurability must be hidden behind defaults.** Advanced configuration options may exist, but they must be in a secondary layer — not the primary interface. Operators who want to customize must be able to do so; operators who don't must not be confronted with complexity they don't need.

**What this prohibits:**
- Releasing a new capability without defining its default-on/default-off state and default configuration values.
- Adding configuration panels to primary operational surfaces without a sensible pre-filled default state.
- Making advanced settings visible in the primary workflow without progressive disclosure.

**Why this rule exists:** MS§10 rule 7 requires simplicity as a first-class constraint. New capabilities, left unchecked, accumulate configuration surface — each individually reasonable, but collectively creating an unusable product for operators without technical support. Simplicity is preserved by design, not by restraint.

---

## §2 — Interaction Model

### Rule
Every user-facing surface must present what to do next — not what exists. The system must minimise the input required from users by inferring defaults, auto-configuring, and reusing patterns. The primary interaction model is conversational (chat-like), not dashboard-driven.

### §2.1 Action-First
Every screen, message, and notification must answer: "What should the user do now?" A surface that displays state without a suggested action is an incomplete output.

### §2.2 Minimal Input
Users must input the minimum data necessary. Forms must not require information the system can infer. Configuration must not be required before a user can do their first meaningful task.

### §2.3 Conversational-First
The system must support reply-based actions, command shortcuts, and natural flow interactions across all user types (learner, operator, instructor, manager).

---

## Architectural Contract: BC-PAY-01 — Payment Confirmation Triggers Instant Access

**Contract name:** BC-PAY-01
**Source authority:** Master Behavioral Spec §7.3 | Market Research §10 (Gap 3), §11 (payment friction finding)

**Rule:** The interval between a confirmed payment and the activation of the corresponding capability, content, or enrollment MUST be zero manual steps. The system must: (1) receive the payment callback from the payment adapter, (2) automatically confirm the transaction, (3) immediately activate the entitled access, (4) notify the payer — without any operator intervention.

**What this prohibits:**
- Manual payment reconciliation steps of any kind for standard payment flows
- Delayed activation pending "payment review" for standard flows
- Requiring the operator to "mark as paid" before access is granted
- Silent payment failures — every failure must present a resolution path

**What this requires:**
- Payment adapter callbacks must directly trigger entitlement activation events
- Activation notification must reach the payer via their primary channel (WhatsApp or SMS) immediately on confirmation
- Payment gateway downtime must present a user-facing fallback — not a silent hold

---

## Architectural Contract: BC-FREE-01 — Free Entry Delivers a Complete Operational Flow

**Contract name:** BC-FREE-01
**Source authority:** Master Behavioral Spec §7.5 | Market Research §9.2 (freemium model), §11 (free tier expected)

**Rule:** The free tier must not be a restricted demo. It must be a complete, working operational environment. It must enable at minimum: enrolling students and tracking attendance, delivering course content, sending basic fee reminders via the primary communication channel, collecting payments via at least one local method, and viewing a basic Daily Action List.

**What this prohibits:**
- Limiting the free tier to a non-functional student count (e.g., 3 students)
- Disabling payment collection in the free tier
- Blocking primary communication channel (WhatsApp) in the free tier
- Making the free tier a passive demo that cannot run a real institution

**What this requires:**
- Free tier limits must be defined by capability scope depth (advanced analytics, multi-branch management, AI assist are paid) — not by disabling core operations
- The free-to-paid upgrade must unlock depth, not enable basic function
- Free tier operators must experience at least one automated action before being asked to upgrade

---

## Architectural Contract: BC-LANG-01 — Business Impact Language Only

**Contract name:** BC-LANG-01
**Source authority:** Master Behavioral Spec §7.6 | Market Research §7 (users value ROI over features), §18.1 (Education Business Platform)

**Rule:** All capability introductions, onboarding prompts, upgrade paths, and help text must use business impact language. Technical capability keys, system code names, and engineering terminology must never be surfaced to operators or learners.

| REQUIRED (Business Impact) | PROHIBITED (Technical Language) |
|---|---|
| "Automatically remind students when fees are overdue" | "Enable: auto_reminder_capability" |
| "Protect your video content from screen recording" | "Enable: media_security_watermark_v2" |
| "Let students pay instantly and access their course immediately" | "Configure: payment_adapter_jazzcash" |
| "See which students are at risk before it's too late" | "Enable: learner_risk_analytics" |
| "Run attendance from WhatsApp — no portal required" | "Enable: whatsapp_interaction_layer" |

**What this requires:**
- Every capability must carry a `business_impact_description` field at registration time
- Onboarding flows, upgrade prompts, and help docs must use this field — not the capability key
- Support documentation must be written in operator/learner language

---

## Architectural Contract: BC-EXAM-01 — High-Stakes Sessions Are Inviolable

**Contract name:** BC-EXAM-01
**Source authority:** Master Behavioral Spec §10.3 | Market Research §9 (site crashes during mock tests — top complaint), §5.2 (coaching academies — server crashes during exams)

**Rule:** During an active exam or high-stakes assessment session, the platform must operate in stability-prioritised mode. No platform operation may interrupt or degrade an active exam session.

**What this prohibits:**
- Forced session re-authentication during an active exam
- Capability gate interruptions mid-exam (if a tenant plan lapses, enforcement applies AFTER session ends)
- Background software updates or sync operations competing with exam session bandwidth
- Losing submitted answers due to a mid-session network interruption

**What this requires:**
- Exam answers saved to server on every question submission — not only at final submit
- Graceful reconnection: if a learner drops and reconnects, the session resumes from the last checkpointed state
- The exam engine must handle the full expected concurrent load for the tenant's largest batch without degradation
- No upgrade prompts or capability gates inside an active exam flow

---

## Architectural Contract: BC-ERR-01 — No Error State Without a Resolution Path

**Contract name:** BC-ERR-01
**Source authority:** Master Behavioral Spec §10.4 | Market Research §7 (low technical literacy), §5.4 (low teacher tech-literacy in schools)

**Rule:** Every error, failure, or blocked state the user encounters must include: (1) a plain-language description of what went wrong, (2) a specific resolution step the user can take immediately, (3) a fallback path if self-resolution is not available.

**What this prohibits:**
- Displaying HTTP error codes or exception messages to non-technical users
- "Something went wrong. Please try again." without stating what failed and how to fix it
- Blocking a workflow with an error that has no user-visible resolution path
- Silent failures where a user's action appears to succeed but has not taken effect

**What this requires:**
- All user-facing error states must be mapped to plain-language resolution templates before release
- Every form validation error must identify specifically which field is wrong and the correct format
- System-level failures (payment gateway down, sync failure) must present a fallback path without technical terminology

---

## Architectural Contract: BC-AI-02 — AI Facilitates Teacher Authority, Does Not Substitute It

**Contract name:** BC-AI-02
**Source authority:** Master Behavioral Spec §8.3 | Market Research §15 (AI contradiction — users want teacher access, not AI replacement) | Extends: MS-AI-01

**Rule:** Every AI-generated output must make the teacher or human instructor the visible authority. AI assists; the teacher leads. This contract extends MS-AI-01 (which governs code-level AI boundaries) with the behavioral presentation layer.

**What this prohibits:**
- AI responses that present as authoritative without a "review with your teacher" path
- Interfaces where AI is the default respondent and the human teacher is secondary
- AI-generated course content published without an instructor approval gate
- Removing or obscuring the AI-generated label to make outputs appear human-authored

**What this requires:**
- All AI-facing interaction surfaces to display: AI-generated indicator, guidance level, and path to human review
- Instructor override available on all AI output surfaces
- AI assist to default to suggestion mode — not advisory or instructional mode — unless explicitly configured by the operator
- When a human instructor is available and reachable, the AI path must surface the human path alongside it

---

## Architectural Contract: BC-CONTENT-02 — Content Protection Default-On for Paid Content

**Contract name:** BC-CONTENT-02
**Source authority:** Master Behavioral Spec §9 | Market Research §10 (Gap 5 — no anti-piracy system), §6 (piracy top pain point) | Extends: MS-CONTENT-01

**Rule:** Content protection (session-token-gated delivery, watermarking, playback controls) must be active by default for all content flagged as paid or premium. This is a platform enforcement, not a configuration option. This contract extends MS-CONTENT-01 (which governs the code gate) with the behavioral governance layer.

**What this prohibits:**
- Paid content delivery without a valid session token, even if the operator has not configured protection settings
- Making content protection an opt-in setting for paid content
- Delivering paid content via a generic CDN URL bypassing the media security layer

**What this requires:**
- All `content_tier = "paid"` content must pass through the media security gate before delivery
- Session tokens must have short TTLs and be non-transferable
- Playback must stop immediately if a session token is revoked mid-session
- Watermarking configuration absence must not disable the session gate — they are independent protections

---

## Architectural Contract: BC-BRANCH-01 — Multi-Branch Operations: Unified Visibility Without Context Switching

**Contract name:** BC-BRANCH-01
**Source authority:** Master Behavioral Spec §5.4 | Market Research §5.2 (coaching academies — multi-branch complexity, lack of cross-branch analytics)

**Rule:** Operators who manage multiple branches, campuses, or franchise locations must be able to see and act on cross-branch operational status without switching tenant contexts or running separate reports.

**What this prohibits:**
- Requiring a HQ operator to log into each branch separately to view branch status
- Aggregating cross-branch data only through a manually generated report
- Applying single-branch permission models to users who operate across branches

**What this requires:**
- RBAC to support a multi-branch view role that spans branches without merging operational data
- Daily Action List filterable by branch for HQ operators; scoped to one branch for branch operators
- Analytics surfaces to default to cross-branch aggregate for HQ-role users
- Branch-level isolation for operational actions (branch A operator cannot act on branch B students)

---

## Architectural Contract: BC-LEARN-01 — Learning Behavior: Progress Visibility and Intervention

**Contract name:** BC-LEARN-01
**Source authority:** Master Behavioral Spec §8.1–8.2

**Rule:** The system must clearly surface each learner's progress, highlight gaps, and suggest improvements without requiring the learner or instructor to search for the information. When low engagement or poor performance is detected, the system must automatically trigger an appropriate intervention or surface a corrective action suggestion.

**What this prohibits:**
- Progress presented as a bare percentage with no outcome framing or gap identification
- Low engagement or performance detected but not escalated to any action
- Intervention triggers that require manual configuration to activate

**What this requires:**
- Progress framed in outcome terms ("2 modules remaining before completion") not only percentages
- Automatic intervention triggers on detection of low engagement or poor performance
- Suggested corrective actions delivered to the instructor or operator, not just stored in a log

---

## Architectural Contract: BC-ECON-01 — Economic Behavior: Revenue Insights Must Convert to Actions

**Contract name:** BC-ECON-01
**Source authority:** Master Behavioral Spec §11 | Market Research §8.1 (manage revenue, not just users)

**Rule:** Every revenue insight surfaced by the platform must carry a proposed action. Revenue data without a suggested next step is an incomplete output. The system must convert revenue signals into operator tasks, not just reports.

**What this prohibits:**
- Revenue dashboards that display totals without suggested follow-up actions
- Overdue fee lists with no embedded "send reminder" or "escalate" action
- Profitability warnings that appear in a report without a linked corrective step

**What this requires:**
- Revenue insights to be surfaced as part of the Daily Action List, not only in the reports section
- Every overdue fee, lapsing subscription, or churn signal to generate an action item automatically
- Economic insights to use plain operational language ("10% of revenue is at risk — send reminders?") not accounting format

---

## Architectural Contract: BC-FAIL-01 — Trust and Reliability: Proactive Offline and Failure Resilience

**Contract name:** BC-FAIL-01
**Source authority:** Master Behavioral Spec §10.1–10.2 | Market Research §10 (Gap 6 — no offline-first LMS), §14.2 (offline mode as Must-Build)

**Rule:** The platform must not wait for a user to go offline before enabling offline access. Offline readiness must be proactive. The system must gracefully handle all failures, retry automatically, and sync when connectivity is restored. Failures must never result in silent data loss.

**What this prohibits:**
- Offline mode that only works if the user manually downloads content before losing connectivity
- Silent sync failures — every failed sync must notify the user with a recovery path
- Exam sessions that cannot queue submissions for delivery on reconnect

**What this requires:**
- Critical learning content (current course materials, upcoming assessments) must be pre-cached on device while the user is connected
- Sync status must be visible as a persistent, unobtrusive indicator in the mobile interface (synced / syncing / offline — X items pending)
- When connectivity is detected, sync must begin automatically without user action
- Conflict resolution must be automatic for non-critical data; for critical data (exam submissions, fee payments), conflicts must be surfaced with a clear resolution choice

---

## Relationship to Other Docs

| Document | Role | Relationship |
|---|---|---|
| `LMS PLATFORM — MASTER PRODUCT & BUILD SPEC.md` | Defines WHAT exists | This doc defines HOW it behaves |
| `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md` | Source behavioral authority (archived) | This doc is the repo-facing translation of that authority |
| `LMS_Platform_Master_Behavioral_Spec.md` | Master behavioral spec (merged BOS + market-derived rules) | This doc implements the repo-facing contracts from that authority |
| All `*_spec.md` and `B*P*` docs | Define service capabilities | Must operate within behavioral rules stated here |
| `gap_register.md` | Tracks BOS overlay gaps | All 18 gaps resolved 2026-04-04 |
| `ms_overlay_gap_register.md` | Tracks MS overlay gaps | All 14 contracts resolved 2026-04-11 |

### Named Contracts in This Document

| Contract | Section | Source Authority |
|---|---|---|
| §1 — System as Operator | §1 | BOS §1 |
| §2 — Interaction Model | §2 | BOS §2 / Master Behavioral Spec §3 |
| MS-UX-01 — Mobile-First UX | MS§8 | Master Spec §8 |
| MS-UX-02 — Outcome-Driven UX | MS§8 | Master Spec §8 |
| MS-SIMPLE-01 — Simplicity Preservation | MS§10.7 | Master Spec §10.7 |
| BC-PAY-01 — Payment Confirmation Triggers Instant Access | §7.3 | Market Research §10 Gap 3 |
| BC-FREE-01 — Free Entry Delivers a Complete Operational Flow | §7.5 | Market Research §9.2 |
| BC-LANG-01 — Business Impact Language Only | §7.6 | Market Research §7 |
| BC-EXAM-01 — High-Stakes Sessions Are Inviolable | §10.3 | Market Research §9 |
| BC-ERR-01 — No Error State Without a Resolution Path | §10.4 | Market Research §7 |
| BC-AI-02 — AI Facilitates Teacher Authority, Does Not Substitute | §8.3 | Market Research §15 |
| BC-CONTENT-02 — Content Protection Default-On for Paid Content | §9 | Market Research §10 Gap 5 |
| BC-BRANCH-01 — Multi-Branch Operations: Unified Visibility | §5.4 | Market Research §5.2 |
| BC-LEARN-01 — Learning Behavior: Progress Visibility and Intervention | §8.1–8.2 | Master Behavioral Spec §8 |
| BC-ECON-01 — Economic Behavior: Revenue Insights Must Convert to Actions | §11 | Market Research §8.1 |
| BC-FAIL-01 — Trust and Reliability: Proactive Offline and Failure Resilience | §10.1–10.2 | Market Research §10 Gap 6 |
| §14 — User Psychology Alignment | BOS §14 | BOS §14 |
| §15 — Final Behavioral Principle | BOS §15 | BOS §15 |

---

## References

- `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md` §1, §14, §15 (archived — `C:\LMS\LMS New\_archive\`)
- `LMS_Platform_Master_Behavioral_Spec.md` — merged master behavioral authority (`C:\LMS\LMS New\`)
- `LMS_Pakistan_Market_Research_MASTER.md` — market research source (`C:\LMS\LMS New\`)
- `docs/specs/operations_os_spec.md` — primary operations behavioral surface
- `docs/specs/interaction_layer_spec.md` — conversational interaction layer
- `docs/specs/onboarding_spec.md` — instant start and smart defaults
- `docs/architecture/capability_gating_model.md` — capability gate UX contract
- `docs/specs/media_security_spec.md` — content protection implementation (BC-CONTENT-02)
- `docs/specs/exam_engine_spec.md` — exam session integrity (BC-EXAM-01)
- `docs/specs/financial_ledger_spec.md` — revenue insights (BC-ECON-01)
- `docs/specs/offline_sync_spec.md` — offline resilience (BC-FAIL-01)
