# LMS Platform — Master Behavioral Operating Spec

> **Sources:** LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md · LMS_Market_Derived_Behavioral_Contract.md
> **Merged:** 2026-04-14
> **Rule:** No invention. All content sourced from one or both originals. No deletions. Conflicts resolved by reconciliation. Market-derived rules carry traceability references.

---

## Purpose

This document defines **HOW the system must behave** — how it interacts with users, how it guides, automates, and acts on their behalf. It is the behavioral authority for the platform.

**Relationship to other documents:**

| Document | Role |
|---|---|
| `LMS PLATFORM — MASTER PRODUCT & BUILD SPEC.md` | Defines WHAT exists — capabilities, architecture, domains |
| This document | Defines HOW it operates — behavior, interaction, automation, UX |
| `platform_behavioral_contract.md` | Repo-facing translation of this authority into named contracts |

**Core Principle:**

> *"Users should not have to figure out the system. The system should guide, automate, and act."*

---

## PART I — BEHAVIORAL FOUNDATION

---

### §1 — System Role: Operator, Not Tool

#### 1.1 The System Acts as an Operator

The system must behave as an operator that thinks, acts, and guides on behalf of its users — not as a passive tool that waits for input and returns data.

| Operator Behavior (REQUIRED) | Tool Behavior (PROHIBITED) |
|---|---|
| Proactively surfaces what needs to be done | Waits for the user to open a dashboard |
| Suggests the next action based on system state | Returns raw data for the user to interpret |
| Automates repetitive tasks without being asked | Requires the user to configure automation manually |
| Guides users through complexity with smart defaults | Presents all options at once and expects configuration |
| Acts on patterns it detects (e.g., 5 unpaid fees → suggest reminder) | Stores data without acting on implications |

#### 1.2 User Intent First

The system must prioritize user intent over system structure.

**Example:**

User intent: "I want to collect fees"

System must:
- Trigger reminders
- Suggest actions
- Automate follow-ups

Not: show a dashboard requiring interpretation.

---

### §2 — Interaction Model

#### 2.1 Action-First Interaction

The system must always present **what to do next** — not what exists. Every screen, message, and notification must answer: "What should the user do now?"

#### 2.2 Minimal Input Principle

Users must input minimum data, avoid complex forms, and avoid configuration overload. The system must infer defaults, auto-configure, and reuse patterns from prior context.

#### 2.3 Conversational Interaction

The primary interaction model is conversational (chat-like). The system must support reply-based actions, command shortcuts, and natural flow interactions.

#### 2.4 WhatsApp as Primary Operational Interface

*Market grounding: Research §6 (Gap 2 — no WhatsApp-native system), §9 (Shadow LMS finding — WhatsApp IS the real LMS), §7 (customers prefer WhatsApp over dashboards)*

WhatsApp must be treated as a first-class operational surface — not a notification channel. The following operational actions must be executable directly through a WhatsApp interaction without requiring the operator or learner to open the LMS portal:

- View daily action list
- Mark attendance
- Confirm or waive a fee
- Send a reminder to a student
- Approve or reject a pending action
- Receive enrollment confirmation (as a learner)
- Receive assessment result (as a learner)

**What this prohibits:**
- Treating WhatsApp as a one-way broadcast channel only
- Requiring "click here to open the portal" for actions that could be completed in-thread
- Sending notifications without actionable reply options where an action is possible

**What this requires:**
- All WhatsApp notification templates must include contextual reply actions where an action exists
- The interaction layer must complete the above operational flows via WhatsApp reply commands
- Operators must be able to run a meaningful portion of their daily operations without opening a browser

---

### §3 — Automation Principles

#### 3.1 Default Automation

The system must automate repetitive tasks by default. Automation requires opt-out, not opt-in.

Examples:
- Fee reminders auto-triggered on due date
- Inactivity alerts auto-generated after defined period
- Attendance tracking assisted via default session rules

#### 3.2 Event-Driven Behavior

The system must react to user actions, time triggers, and system state changes.

**Example:**

IF student misses 3 sessions → notify admin, suggest action, optionally trigger WhatsApp message.

---

## PART II — OPERATIONAL BEHAVIOR

---

### §4 — Decision Reduction

#### 4.1 System Suggests Actions

The system must detect patterns and surface suggested next steps — not raw data for the user to interpret.

Examples:
- "5 students have unpaid fees — send reminders?"
- "Attendance dropped this week — review batch?"
- "Batch performance declining — schedule intervention?"

#### 4.2 Prioritization Engine

The system must rank and present:
1. Critical actions (require immediate attention)
2. Important tasks (should be completed today)
3. Optional insights (available when user wants context)

The most important action must always appear first. Users must never have to decide what order to work through items.

---

### §5 — Daily Operations Model

#### 5.1 Daily Action List

The system must generate a Daily Action List automatically. It must include:
- Unpaid and overdue fees
- Absent students
- Inactive users
- Pending approvals
- Urgent system alerts

#### 5.2 Zero-Dashboard Entry

The system must be fully operable without a dashboard. Full operational capability must be accessible via notifications, WhatsApp messages, and guided flows. Dashboards are an optional view — not the required entry point.

#### 5.3 Revenue as a First-Class Operational Signal

*Market grounding: Research §8.1 (winning strategy: manage revenue not just learning), §7 (operators value ROI), §12 (financial system as core product requirement)*

Revenue metrics must surface as primary operational signals — not buried in reports. The following must be available at the operator's first interaction point (Daily Action List, WhatsApp summary, or main operational view):

- Total fees outstanding (count + amount)
- Fees collected today / this week
- Overdue fees with student names
- Upcoming fee due dates (next 7 days)
- Revenue at risk (enrolled students with no payment on record)

**What this prohibits:**
- Putting financial metrics behind a "Reports" navigation item requiring deliberate navigation
- Showing enrollment counts without corresponding payment status
- Treating revenue tracking as a finance-team feature rather than a daily operator signal

**What this requires:**
- Financial summary to be part of the Daily Action List output
- Overdue fees to generate action items automatically — not require a manual report pull
- Revenue signal language to be plain and operational ("7 fees overdue — follow up") not accounting-formatted

#### 5.4 Multi-Branch Operations: Unified Visibility Without Context Switching

*Market grounding: Research §5.2 (coaching academies — multi-branch complexity, lack of cross-branch analytics), §5.3 (scaling to 50,000+ students across franchises)*

Operators who manage multiple branches, campuses, or franchise locations must be able to see and act on cross-branch operational status without switching tenant contexts or running separate reports:

1. The main operational view must aggregate across all branches by default for HQ-level users
2. Branch-level isolation must be enforced for operational actions (branch A operator cannot act on branch B students) while HQ visibility spans all branches
3. Cross-branch performance comparison (attendance rates, fee collection, completion rates) must be a first-class view, not an ad-hoc report

**What this prohibits:**
- Requiring a HQ operator to log into each branch separately to view branch status
- Aggregating cross-branch data only through a manually generated report
- Applying single-branch permission models to users who operate across branches

**What this requires:**
- RBAC to support a multi-branch view role that spans branches without merging operational data
- Daily Action List filterable by branch for HQ operators; scoped to one branch for branch operators

---

### §6 — Communication Behavior

#### 6.1 Actionable Communication

Messages must allow action inside the message itself. Examples: "Mark attendance," "Confirm payment," "Send reminder." A message that only informs without enabling an action is a lower-quality output — action-enabled messages are the standard.

#### 6.2 Multi-Channel Consistency

The system must ensure consistent behavior across all channels (WhatsApp, SMS, email, mobile app, web). The same action must produce the same result regardless of which channel the user uses to initiate it.

---

## PART III — COMMERCE & MONETIZATION BEHAVIOR

---

### §7 — Commerce Behavior

#### 7.1 Value-First Upgrades

The system must expose full, meaningful value in the free tier. Upgrades are triggered when the user needs more scale or automation — not when core functionality is restricted. The free tier is not a demo; it is a functional entry point.

#### 7.2 Contextual Upsell

Upsells must appear when they are contextually relevant to what the user is trying to do — not as general promotions. Example: "Enable auto-reminders to recover unpaid fees" shown when the operator is viewing overdue fees.

#### 7.3 Payment Confirmation Triggers Instant, Automatic Access

*Market grounding: Research §9 (payment friction — screenshot bank transfers), §10 (Gap 3 — no integrated local payment flows), §11 (JazzCash/EasyPaisa/Raast instant activation requirement)*

The interval between a confirmed payment and the activation of the corresponding capability, content, or enrollment must be zero manual steps.

The system must:
1. Receive the payment callback from the payment adapter (JazzCash, EasyPaisa, Raast, card gateway)
2. Automatically confirm the transaction
3. Immediately activate the entitled capability or content access
4. Notify the learner/customer of activation — without any operator intervention

**What this prohibits:**
- Manual payment reconciliation steps (screenshot upload, manual confirmation, operator approval for standard payments)
- Delayed activation pending "payment review" for standard flows
- Requiring the operator to "mark as paid" before the learner gains access

**What this requires:**
- Payment adapter callbacks to directly trigger entitlement activation events
- Payment confirmation to include immediate in-channel notification to the payer
- Failed or pending payments to present a resolution path — not a silent hold

#### 7.4 Capability Gates Demonstrate Value Before Requesting Upgrade

*Market grounding: Research §7 (low upfront WTP; upgrade only after clear value), §9.2 (freemium → upgrade on demonstrated value, pay for capabilities not tiers)*

When a user encounters a capability gate, the system must:

1. Show what the capability does and what outcome it delivers in plain, business-impact language
2. Show a concrete example using the user's own context where possible ("With automated fee reminders, 3 of your overdue students would have been notified automatically last week")
3. Present the upgrade path clearly and simply after the value demonstration

**What this prohibits:**
- Bare "Upgrade Required" or "Feature Locked" messages without context
- Technical capability key names surfaced to users
- Upgrade prompts that lead with pricing before demonstrating value

#### 7.5 Free Entry Delivers a Complete Operational Flow

*Market grounding: Research §7 (low upfront WTP), §9.2 (freemium model expected), §11 (free entry tier expected across all segments)*

The free tier must enable a complete, working end-to-end operational flow, including:
- Enrolling students and tracking attendance
- Delivering course content to enrolled students
- Sending basic fee reminders via WhatsApp
- Collecting payments via at least one local payment method
- Viewing a basic Daily Action List

**What this prohibits:**
- Limiting free tier to a non-functional student count
- Disabling payment collection in the free tier
- Blocking WhatsApp communication in the free tier

**What this requires:**
- Free tier limits to be defined by capability scope depth (advanced analytics, multi-branch, AI assist are premium) — not by making core operations non-functional
- Free tier operators to experience at least one automated action before they are asked to upgrade

#### 7.6 Capability Introduction Uses Business Impact Language

*Market grounding: Research §7 (users value ROI over features), §18.1 (Education Business Platform — not LMS), §8.1 (help the operator make money)*

All capability introductions, onboarding prompts, upgrade paths, and help text must use business impact language — never feature names or technical capability keys.

| REQUIRED (Business Impact) | PROHIBITED (Feature Language) |
|---|---|
| "Automatically remind students when fees are overdue" | "Enable: auto_reminder_capability" |
| "Protect your video content from screen recording" | "Enable: media_security_watermark_v2" |
| "Let students pay instantly via JazzCash and access their course immediately" | "Configure: payment_adapter_jazzcash" |
| "See which students are at risk of dropping out before it happens" | "Enable: learner_risk_analytics" |
| "Run attendance from WhatsApp — no portal required" | "Enable: whatsapp_interaction_layer" |

---

## PART IV — LEARNING BEHAVIOR

---

### §8 — Learning Behavior

#### 8.1 Progress Visibility

The system must clearly show each learner's progress, highlight gaps, and suggest improvements. Progress must be framed in terms of outcomes ("2 modules remaining before completion") not just percentages.

#### 8.2 Intervention System

The system must detect low engagement and poor performance and automatically trigger appropriate interventions or suggest corrective actions to the instructor or operator.

#### 8.3 AI Assist Behavior: Facilitate Teacher Authority, Do Not Substitute It

*Market grounding: Research §15 (AI contradiction — users say they want AI tutors but actually value Teacher Access), §7 (teacher quality is the primary content differentiator)*

Every AI-generated output must make the teacher or human instructor the visible authority. AI assists; the teacher leads.

**Behavioral requirements:**

1. AI responses must be labeled as AI-generated in all surfaces
2. Every AI response must surface a path to reach the human instructor ("Ask your teacher directly" or equivalent)
3. AI must never be presented as the primary respondent when a human instructor is available and reachable
4. AI-generated content suggestions (quiz questions, explanations, course content) must be presented as drafts for instructor review — not published as final content

**What this prohibits:**
- AI responses that present as authoritative answers without a "review with your teacher" path
- Interfaces where AI is the default respondent and the human teacher is the secondary option
- AI-generated course content published without an instructor approval gate

**What this requires:**
- All AI-facing interaction surfaces to display: AI-generated indicator, guidance level, and path to human review
- Instructor override available on all AI output surfaces
- AI assist to default to suggestion mode — not advisory or instructional mode — unless explicitly configured

---

## PART V — CONTENT & SECURITY BEHAVIOR

---

### §9 — Content Protection Default-On for Paid Content

*Market grounding: Research §10 (Gap 5 — no strong anti-piracy system), §6 (piracy of recorded lectures — top pain point for academies), §14.2 (anti-piracy video player as Must-Build), §5.2 (content screen-recording is common)*

Content protection (session-token-gated delivery, watermarking, playback controls) must be **enabled by default for all content flagged as paid or premium**. This is a platform enforcement, not a configuration option.

**What this prohibits:**
- Paid content delivery without a valid session token, even if the operator has not explicitly configured protection settings
- Making content protection an opt-in setting for paid content
- Delivering paid content via a generic CDN URL that bypasses the media security layer

**What this requires:**
- All content with `content_tier = "paid"` to pass through the media security gate before delivery
- Session tokens to have short TTLs and be non-transferable
- Playback to stop if the session token is revoked mid-session
- Watermarking configuration absence must not disable the session gate — they are independent protections

---

## PART VI — TRUST, RELIABILITY & RESILIENCE

---

### §10 — Trust & Reliability Behavior

#### 10.1 Failure Resilience

The system must gracefully handle failures, retry operations automatically, and sync when connectivity is restored. Failures must never result in silent data loss.

#### 10.2 Offline Behavior: Proactive, Not Reactive

*Market grounding: Research §10 (Gap 6 — no offline-first LMS), §14.2 (offline video mode as Must-Build), §5.5 (universities — unreliable internet in remote areas), §20 (Offline LMS in a Box strategy)*

The platform must not wait for a user to go offline before enabling offline access. Offline readiness must be proactive:

1. Critical learning content (current course materials, upcoming assessments) must be pre-cached on device while the user is connected
2. Sync status must be communicated to the user at all times (synced / syncing / offline — X items pending)
3. When connectivity is detected, sync must begin automatically without user action
4. Conflict resolution must be automatic for non-critical data; for critical data (exam submissions, fee payments), conflicts must be surfaced with a clear resolution choice

**What this prohibits:**
- Offline mode that only works if the user manually downloads content before losing connectivity
- Silent sync failures — any failed sync must notify the user with a recovery path
- Exam sessions that cannot be submitted offline (answers must be queued and submitted on reconnect)

**What this requires:**
- Predictive pre-cache based on the learner's current learning path
- Sync status visible as a persistent, unobtrusive indicator in the mobile interface
- Operators to see which of their learners are currently operating in offline mode

#### 10.3 High-Stakes Session Behavior: Exam Sessions Are Inviolable

*Market grounding: Research §9 (performance frustration — "site crashed during my mock test" as top recurring complaint), §7 (zero tolerance for technical glitches during high-stakes exams), §5.2 (coaching academies — server crashes during mock tests as existential pain)*

During an active exam or high-stakes assessment session, the platform must operate in stability-prioritized mode. No operation may interrupt or degrade an active exam session:

1. No background software updates during an active exam session
2. No capability gate interruptions during an active exam session — if a tenant's plan lapses mid-exam, the session continues; enforcement applies after the session ends
3. No automatic sync operations that compete with exam session bandwidth on the client device
4. Exam session state must be checkpointed server-side at regular intervals so a connection drop does not result in answer loss

**What this prohibits:**
- Forced session re-authentication during an active exam
- Upgrade prompts or capability gates inside an active exam flow
- Losing submitted answers due to a mid-session network interruption

**What this requires:**
- Answers saved to server on every question submission — not only at final submit
- Graceful reconnection: if a learner drops and reconnects, the session resumes from the last checkpointed state
- High-concurrency readiness: exam engine must handle the full expected concurrent load for the tenant's largest batch

#### 10.4 No Error State Without a Resolution Path

*Market grounding: Research §7 (users avoid complex setup), §6 (low technical literacy among operators), §5.4 (low teacher tech-literacy in schools)*

Every error, failure, or blocked state must include:

1. A plain-language description of what went wrong (no error codes, no stack trace language)
2. A specific resolution step the user can take immediately
3. A fallback path if the self-resolution step is not available (retry, undo, contact support)

**What this prohibits:**
- Displaying HTTP error codes or system exception messages to non-technical users
- Showing "Something went wrong. Please try again." without indicating what failed and what resolves it
- Blocking a workflow with an error that has no user-visible resolution path
- Silent failures where a user's action appears to succeed but has not

**What this requires:**
- All user-facing error states to be mapped to plain-language resolution templates before release
- Every form validation error to indicate specifically which field is wrong and what the correct input is
- System-level failures (payment gateway down, sync failure) to present a fallback path without technical terminology

---

## PART VII — UX, SIMPLICITY & INSIGHT

---

### §11 — Economic Behavior

#### 11.1 Revenue Awareness

The system must surface revenue insights — not just revenue data. Highlights include risks (unpaid fees, at-risk revenue, churn signals) and opportunities (recovery, re-engagement).

#### 11.2 Actionable Economics

The system must convert revenue insights into proposed actions, not just reports.

Example: "10% of revenue is at risk — send reminders?" not "Outstanding fees: PKR 45,000."

---

### §12 — Onboarding Behavior

#### 12.1 Instant Start

New users and new tenants must experience a meaningful outcome (first course published, first student enrolled, first reminder sent) within the first session — without manual setup. Onboarding must not defer value until full configuration is complete.

#### 12.2 Progressive Disclosure

Complexity must be revealed gradually. Advanced configuration options exist but must be in a secondary layer — not visible in the primary workflow. Operators who want to customize can find it; operators who don't must not be confronted with options they don't need.

---

### §13 — Simplicity Enforcement

#### 13.1 No Overload

The system must avoid unnecessary features and excessive configuration. Every new capability must have a sensible default configuration that works for the majority of tenants without any manual setup. A capability that requires 10 configuration steps before it is usable violates this rule.

#### 13.2 Smart Defaults

The system must pre-fill configurations, auto-select optimal paths, and reuse established patterns. A new operator who has never used the platform must be able to complete a meaningful operational workflow (enroll a student, send a reminder, view attendance) within their first session without reading documentation.

---

### §14 — Data & Insight Behavior

#### 14.1 Insights Over Reports

The system must provide insights, not raw data. Every data surface must answer "what should I do next?" — not just "here is what happened." A table showing data without a suggested action or outcome framing is an incomplete output.

#### 14.2 Comparative Context

The system must benchmark performance and provide relative insights — not just absolute numbers. "Attendance is 72%" is less useful than "Attendance is 72% — down 8% from last week, your lowest-engaged batch is Batch B."

---

### §15 — User Psychology Alignment

#### 15.1 Reduce Cognitive Load

The system must never present more information than the user needs to take the next action. Dashboards, reports, and lists must be filtered to relevance by default — raw unfiltered views require explicit user opt-in. When multiple actions are possible, the system must rank and present the most important first.

#### 15.2 Build Trust Through Consistency

The same action must produce the same result regardless of channel, device, or interface. System messages must use consistent, plain language — no technical codes surfaced to non-technical users. If the system takes an automated action on behalf of the user, it must notify the user and allow reversal.

#### 15.3 Provide Quick Wins Early

New users must experience a meaningful outcome within their first session without manual setup. Onboarding flows must deliver visible value at each step — not defer value until full configuration is complete.

#### 15.4 Reinforce Value Continuously

The system must surface moments of value proactively: completion milestones, revenue collected, attendance improved, risk avoided. These signals must be delivered as operator nudges ("You collected 12 fees this week") — not buried in reports.

---

## PART VIII — GOVERNING PRINCIPLES

---

### §16 — Final Behavioral Principle

The system must:

- **THINK** for the user — detect what matters before the user has to look for it
- **ACT** with the user — enable action at every interaction point, not just information delivery
- **GUIDE** the user — at every step, the next action must be obvious

The system must NOT:

- Wait for user input before surfacing what is important
- Require user interpretation of raw system output
- Show data without a suggested action
- Require a user to navigate to find out what to do next
- Block a user with an error code without telling them what to do
- Automate a task as opt-in when it is universally beneficial

---

## FINAL STATEMENT

> *"A great platform is not one that provides features. It is one that reduces effort, automates operations, and continuously guides users toward better outcomes."*

> *"Build a platform that allows institutions to run learning, operations, communication, and revenue — in one system, without complexity."*
