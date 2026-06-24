# OUT-OF-SCOPE REGISTER — PROJECT MEMORY LAYER

Status: Active
Date: 2026-06-24
Phase: Project Memory Layer (post Phase 3.25)
Owner: Shared

---

## Purpose

Contains every feature, module, or capability that is intentionally deferred, excluded from the current phase, or scheduled for a future sprint. These are NOT abandoned — they are tracked so that scope discipline is maintained and features are not lost.

Classification rule: OUT-OF-SCOPE only if intentionally deferred, confirmed future phase, regional expansion, optional capability, or formal launch exclusion.

---

## IMPORTANT DISTINCTION

Items in this register fall into two categories:

**PLANNED-DEFERRED:** Feature IS intended for the platform. Implementation sprint is planned but not yet scheduled. Not excluded permanently. These items should be picked up in dedicated sprints.

**FORMALLY-EXCLUDED:** Feature is explicitly out of scope for the platform or current generation. No sprint planned.

---

## PM-OS-001: Parent/Guardian Portal (FGAP-001)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-001 |
| **Original ID** | FGAP-001 / PDC-009 |
| **Title** | Parent/Guardian Portal — monitor student progress, attendance, fees |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — no service, no workflow, no design doc |
| **Original Source** | AI_OPERATING_CONTEXT QUICK_REFERENCE — "Parents — monitor student progress" |
| **Evidence Source** | Zero implementation: no parent-service, no parent role_key in rbac-service, no parent workflow in PRODUCT_WORKFLOWS.md. No parent-facing screens in FRONTEND_SCREEN_CATALOG.md (SCR-001 through SCR-027). |
| **Resolution Source** | Phase 2.95 PDC-009 → FGAP-001 |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Parent portal is a documented product intent with zero current implementation. Full sprint required: parent user type, authentication, workflows, and screens. |
| **Detailed Explanation** | Product vision includes parents/guardians monitoring their children's learning progress, fee payment status, attendance, and upcoming sessions. None of this exists in the current codebase. It requires: (1) parent user type in rbac-service; (2) parent-child relationship in user-service or a dedicated parent-service; (3) parent-facing workflows in PRODUCT_WORKFLOWS; (4) new screens (parent dashboard, child progress view, fee status, attendance view); (5) parent authentication flow. This is a substantial sprint covering product design, backend, and frontend. |
| **Affected Components** | rbac-service (parent role), user-service (parent-child relationship), potentially a new parent-service |
| **Affected Routes** | /parent/* (entire parent navigation tree — to be defined) |
| **Affected APIs** | New parent-facing endpoints across multiple services |
| **Affected Workflows** | New WF-011 or similar (parent monitoring workflow) |
| **Affected Roles** | NEW ROLE: parent/guardian |
| **Owner Required** | YES — before parent portal sprint (scope confirmation) |
| **External Dependency** | NO |
| **Future Impact** | HIGH — major user role missing from initial platform |
| **Reopen Criteria** | Owner schedules parent portal sprint |
| **Sprint Dependencies** | Parent role definition → parent-child relationship data model → API design → backend implementation → frontend screens |
| **Related Documents** | docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-001 |
| **Related Register Entries** | PM-AC-043 (AI_OPERATING_CONTEXT parent TBD → updated to FGAP-001) |

---

## PM-OS-002: Adaptive Learning Engine (FGAP-002)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-002 |
| **Original ID** | FGAP-002 / PDC-006 |
| **Title** | Adaptive Learning Engine — personalized content progression |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — design doc exists; no service in manifest |
| **Original Source** | FEATURE_SCOPE §3 — "Out of Scope (Current Phase) — Adaptive learning engine (design only)" |
| **Evidence Source** | docs/designs/adaptive-learning-engine.md — design document exists. No adaptive-learning-service in service-manifest.json. No adaptive content path in any workflow. |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Design exists. "Current Phase" means current build sprint, not permanent exclusion. Adaptive learning sprint required: adaptive-learning-service + content path API + learner state machine. |
| **Detailed Explanation** | Adaptive learning adjusts content progression based on learner performance — slower learners get more practice, faster learners get advanced content. The design doc describes the algorithm and integration points. Neither the service nor the API exists. Standard linear content delivery is in scope now. Adaptive paths are deferred. |
| **Affected Components** | New: adaptive-learning-service (to be created and registered) |
| **Affected Routes** | Adaptive content path screens (new, to be defined in adaptive sprint) |
| **Affected APIs** | New adaptive content API |
| **Affected Workflows** | Augments WF-003 (learning path) and WF-004 (learning completion) |
| **Affected Roles** | Learner (personalized path), Teacher (adaptive settings) |
| **Owner Required** | NO — design exists; sprint is autonomous |
| **External Dependency** | NO |
| **Future Impact** | HIGH — key LMS differentiator |
| **Reopen Criteria** | Owner schedules adaptive learning sprint |
| **Sprint Dependencies** | adaptive-learning-service built → registered in manifest → API contract defined → frontend adaptive path screens |
| **Related Documents** | docs/designs/adaptive-learning-engine.md; docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-002 |
| **Related Register Entries** | None |

---

## PM-OS-003: AI Learning Copilot Overlay (FGAP-003)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-003 |
| **Original ID** | FGAP-003 / PDC-007 |
| **Title** | AI Learning Copilot — persistent cross-screen AI overlay |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — confirmed AI services in scope; overlay is the gap |
| **Original Source** | docs/designs/ai-learning-copilot.md; FEATURE_SCOPE §1.10 and §2 |
| **Evidence Source** | ai-tutor-service, recommendation-service, skill-inference-service, course-generation-service — all confirmed in manifest. docs/designs/ai-learning-copilot.md — describes full copilot overlay (persistent cross-screen AI assistant). Overlay architecture not implemented. |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Initial sprint builds per-lesson AI tutor panel and recommendations widget (confirmed services). Full copilot overlay (persistent, cross-screen, context-aware AI assistant) deferred to AI copilot sprint. |
| **Detailed Explanation** | The AI copilot design describes a floating AI assistant that follows the learner across all screens, maintaining context (current lesson, quiz state, learning goals). This requires: (1) copilot overlay UI component; (2) cross-screen context collection and passing; (3) possibly a copilot-coordinator-service managing conversation state; (4) conversation history persistence. None of this exists. The per-lesson AiTutorPanel (SCR-018) is in scope and buildable from ai-tutor-service. |
| **Affected Components** | AiTutorPanel (lesson-level, in scope); CopilotOverlay (new, deferred) |
| **Affected Routes** | All learner routes (copilot overlay is cross-screen) |
| **Affected APIs** | ai-tutor-service + potentially new copilot-coordinator API |
| **Affected Workflows** | All learner workflows (copilot is persistent) |
| **Affected Roles** | Learner |
| **Owner Required** | NO — design exists; sprint is autonomous |
| **External Dependency** | YES — LLM API (Claude API) credentials for AI responses |
| **Future Impact** | HIGH — major UX differentiator for the platform |
| **Reopen Criteria** | Owner schedules AI copilot sprint |
| **Sprint Dependencies** | Copilot scope defined → context-passing API designed → conversation storage confirmed → backend copilot coordinator → frontend overlay component |
| **Related Documents** | docs/designs/ai-learning-copilot.md; docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-003 |
| **Related Register Entries** | PM-SD-004 (AI tutor scope — confirmed services in scope) |

---

## PM-OS-004: Learner Risk Insights (FGAP-004)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-004 |
| **Original ID** | FGAP-004 / PDC-008 |
| **Title** | Learner Risk Insights — at-risk learner early warning system |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — design doc exists; no risk scoring service in manifest |
| **Original Source** | FEATURE_SCOPE §2; docs/designs/learner-risk-insights-design.md |
| **Evidence Source** | docs/designs/learner-risk-insights-design.md — design document exists. skill-analytics-service and learning-analytics-service in manifest (general analytics, not risk-specific). No risk scoring model or API. |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Learner risk insights (at-risk early warning based on engagement/progress signals) requires a backend risk scoring service and a dashboard panel for teachers/admins. Both deferred. |
| **Detailed Explanation** | The risk insights design describes an early warning system: learners who fall behind attendance, stop submitting assignments, or have low assessment scores are flagged as at-risk. Teachers and admins see a risk panel on their dashboards for intervention. Implementation requires: (1) risk scoring service or extension to learning-analytics-service; (2) risk threshold configuration; (3) risk alert delivery via notifications; (4) frontend risk insights panel in teacher/admin dashboards. |
| **Affected Components** | New risk scoring service or learning-analytics-service extension |
| **Affected Routes** | Risk insights panel in /teacher/batches/:id/dashboard, /admin/analytics |
| **Affected APIs** | GET /api/v1/risk-insights/learners?batch_id=&threshold= (new) |
| **Affected Workflows** | Risk detection + notification flow |
| **Affected Roles** | Teacher (risk panel), Admin (risk overview) |
| **Owner Required** | NO — design exists; sprint is autonomous |
| **External Dependency** | NO |
| **Future Impact** | HIGH — teacher retention tool; key for Pakistan educational outcomes focus |
| **Reopen Criteria** | Owner schedules risk insights sprint |
| **Sprint Dependencies** | Risk service built → registered → API defined → teacher/admin dashboard panel |
| **Related Documents** | docs/designs/learner-risk-insights-design.md; docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-004 |
| **Related Register Entries** | None |

---

## PM-OS-005: Reconciliation Admin Screen (FGAP-005)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-005 |
| **Original ID** | FGAP-005 / PDC-005 |
| **Title** | Reconciliation Admin Screen — payment audit and dispute management |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — backend domain exists; HTTP endpoint missing; admin screen missing |
| **Original Source** | services/commerce/service.py; integrations/payments/reconciliation.py |
| **Evidence Source** | PaymentReconciliationEngine.run_reconciliation_pass() confirmed active (PM-AC-042). apply_reconciliation(), schedule_reconciliation_job() confirmed in services/commerce/service.py. No HTTP endpoint exposing reconciliation state. No admin screen for reconciliation audit. |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Reconciliation domain logic is complete. Missing: HTTP endpoint + admin frontend screen. Sprint required: expose reconciliation via HTTP in checkout-service or admin-service; build reconciliation audit screen in admin dashboard. |
| **Detailed Explanation** | The reconciliation backend is fully functional — JazzCash webhook triggers PaymentReconciliationEngine, which updates Order status from PAID to RECONCILED. What's missing is an HTTP-accessible view of reconciliation state for admins. Without this, admins cannot see which payments are reconciled vs unreconciled vs disputed. The fix is: (1) add GET /api/v1/admin/reconciliation/report endpoint; (2) build admin screen showing reconciliation audit table. |
| **Affected Components** | checkout-service or new admin-service (HTTP endpoint); admin frontend (reconciliation screen) |
| **Affected Routes** | /admin/finance/reconciliation (new screen) |
| **Affected APIs** | GET /api/v1/admin/reconciliation/report (to be added) |
| **Affected Workflows** | WF-005 (post-payment reconciliation audit) |
| **Affected Roles** | Admin (finance) |
| **Owner Required** | NO — scope is clear; sprint is autonomous |
| **External Dependency** | NO |
| **Future Impact** | MEDIUM — finance admin needs this; initial launch can proceed without it |
| **Reopen Criteria** | Finance admin sprint begins |
| **Sprint Dependencies** | HTTP endpoint added to checkout-service → admin frontend screen built |
| **Related Documents** | integrations/payments/reconciliation.py; services/commerce/service.py; docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-005 |
| **Related Register Entries** | PM-AC-042 (reconciliation confirmed from code); PM-AC-016 (dual reconciliation paths AUTO-CLOSED) |

---

## PM-OS-006: PWA Offline Frontend (FGAP-006)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-006 |
| **Original ID** | FGAP-006 / PDC-010 |
| **Title** | PWA Offline Frontend — service worker, offline caching, sync queue |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | DEFERRED — backend offline-sync-service exists; frontend PWA layer missing |
| **Original Source** | FEATURE_SCOPE §1.4; PRODUCT_WORKFLOWS WF for offline sync |
| **Evidence Source** | backend/services/offline-sync-service/ — in manifest. services/offline-sync/ — domain layer. Frontend is standard Next.js without service worker registration. |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Backend offline sync capability exists. Frontend PWA layer (service worker, offline cache, sync queue UI) requires a dedicated PWA sprint. Not in initial build. |
| **Detailed Explanation** | offline-sync-service manages sync state between offline-capable clients and the backend. The frontend needs: (1) Next.js service worker registration; (2) offline cache manifest (content, lesson data, assessment); (3) learner progress sync queue (pending submissions); (4) sync status indicator UI; (5) reconnect-triggered sync flow. This is a significant frontend-only sprint. Initial build is a standard connected Next.js app. |
| **Affected Components** | Next.js service worker (new); offline-sync-service (existing) |
| **Affected Routes** | All learner routes (offline cache) |
| **Affected APIs** | offline-sync-service HTTP endpoints (sync state management) |
| **Affected Workflows** | WF-004 (offline progress submissions) |
| **Affected Roles** | Learner |
| **Owner Required** | NO — scope is clear; sprint is autonomous |
| **External Dependency** | NO |
| **Future Impact** | HIGH — Pakistan-first: intermittent connectivity makes offline capability important |
| **Reopen Criteria** | PWA sprint begins |
| **Sprint Dependencies** | offline-sync-service HTTP API confirmed → Next.js PWA plugin/worker → cache strategy → sync UI |
| **Related Documents** | docs/08_reports/FEATURE_GAP_REGISTER.md FGAP-006; backend/services/offline-sync-service/ |
| **Related Register Entries** | None |

---

## PM-OS-007: Urdu Language Internationalization (MO-041)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-007 |
| **Original ID** | MO-041 |
| **Title** | Urdu i18n — right-to-left UI and Urdu content support |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | FORMALLY DEFERRED — FEATURE_SCOPE §3 |
| **Original Source** | FEATURE_SCOPE §3 (Out of Scope — Current Phase) |
| **Evidence Source** | FEATURE_SCOPE §3 explicitly defers MO-041 |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Urdu language support (RTL layout, Urdu content metadata, Urdu UI strings) deferred to a regional sprint. Current build is English-only. |
| **Detailed Explanation** | Urdu is Pakistan's national language. For Pakistan-first LMS, Urdu support is strategically important but technically complex (RTL layout, bidirectional text, Urdu font rendering in PDFs/certificates). Deferred to allow initial launch with English, then localized for regional expansion. |
| **Affected Components** | All frontend components (RTL CSS); notification-service (Urdu templates); certificate-service (Urdu fonts) |
| **Affected Routes** | All routes (UI-wide) |
| **Affected APIs** | content metadata (Urdu title/description fields) |
| **Affected Workflows** | All (UI language affects all) |
| **Affected Roles** | All |
| **Owner Required** | YES — Urdu content translation and RTL design approval |
| **External Dependency** | NO (implementation only) |
| **Future Impact** | HIGH — major market adoption for non-English Pakistan users |
| **Reopen Criteria** | Regional sprint scheduled |
| **Related Documents** | docs/00_authority/FEATURE_SCOPE.md §3 |
| **Related Register Entries** | None |

---

## PM-OS-008: Vocational Training Module (MO-042)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-008 |
| **Original ID** | MO-042 |
| **Title** | Vocational Training Module — trade and skills certification |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | FORMALLY DEFERRED — FEATURE_SCOPE §3 |
| **Original Source** | FEATURE_SCOPE §3 |
| **Evidence Source** | FEATURE_SCOPE §3 explicitly defers MO-042 |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Vocational/trade training content types (practical assessments, workshops, trade certifications) deferred to vocational sprint. Standard academic LMS in initial build. |
| **Detailed Explanation** | Vocational training has different content types (practical assessments, workshop attendance, trade-specific grading) and certifications (NAVTTC-recognized certificates vs. academic certificates). Deferred so initial build can focus on academic LMS workflows. |
| **Affected Components** | assessment-service (practical assessments), certificate-service (vocational certs) |
| **Affected Routes** | Vocational course types, workshop management |
| **Affected APIs** | Vocational-specific endpoints |
| **Affected Workflows** | Vocational learning workflows |
| **Affected Roles** | Vocational learner, trade instructor |
| **Owner Required** | YES — vocational content type definitions |
| **External Dependency** | YES — NAVTTC certification integration |
| **Future Impact** | MEDIUM — additional market segment |
| **Reopen Criteria** | Vocational sprint scheduled |
| **Related Documents** | docs/00_authority/FEATURE_SCOPE.md §3 |
| **Related Register Entries** | None |

---

## PM-OS-009: Teacher Marketplace (MO-043)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-009 |
| **Original ID** | MO-043 |
| **Title** | Teacher Marketplace — independent teacher course sales |
| **Classification** | OUT-OF-SCOPE (PLANNED-DEFERRED) |
| **Current Status** | FORMALLY DEFERRED — FEATURE_SCOPE §3 |
| **Original Source** | FEATURE_SCOPE §3 |
| **Evidence Source** | FEATURE_SCOPE §3 explicitly defers MO-043 |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | Teacher marketplace (Udemy-style independent teacher course listing and revenue sharing) deferred to marketplace sprint. Current model is institutional (tenant = school/institution). |
| **Detailed Explanation** | A marketplace model would allow individual teachers to register, create courses, and sell to learners directly (with platform revenue share). This is a fundamentally different tenant model (B2C vs B2B2C). The current multi-tenant model is B2B: institutions (tenants) manage their teachers and learners. Marketplace is a future platform expansion that would require a seller onboarding flow, payout management, and a public course catalog. |
| **Affected Components** | New: marketplace-service, payout-service; changes to: tenant model, course visibility model |
| **Affected Routes** | /marketplace/* (entire marketplace navigation tree) |
| **Affected APIs** | Course listing public API, payout API |
| **Affected Workflows** | Teacher registration, course publishing, revenue share |
| **Affected Roles** | New: independent teacher, marketplace admin |
| **Owner Required** | YES — marketplace model defines revenue sharing and terms of service |
| **External Dependency** | YES — teacher payout (bank transfer, EasyPaisa sender) |
| **Future Impact** | HIGH — significant platform expansion |
| **Reopen Criteria** | Marketplace sprint scheduled |
| **Related Documents** | docs/00_authority/FEATURE_SCOPE.md §3 |
| **Related Register Entries** | PM-ED-001 (JazzCash/EasyPaisa — needed for teacher payouts) |

---

## PM-OS-010: Offline Box Hardware Product (MO-044)

| Field | Value |
|---|---|
| **Item ID** | PM-OS-010 |
| **Original ID** | MO-044 |
| **Title** | Offline Box — standalone hardware device for offline learning |
| **Classification** | OUT-OF-SCOPE (FORMALLY-EXCLUDED) |
| **Current Status** | PERMANENTLY EXCLUDED from software platform |
| **Original Source** | FEATURE_SCOPE §3 — explicitly excluded (not deferred) |
| **Evidence Source** | FEATURE_SCOPE §3 — MO-044 listed under permanent exclusions, not "current phase" deferrals |
| **Classification Date** | 2026-06-23 |
| **Decision Summary** | The offline hardware box (an appliance for schools with no internet) is excluded from this software platform. It is a separate hardware product initiative, not a software feature. |
| **Detailed Explanation** | MO-044 refers to a physical device (Raspberry Pi-class offline server) that could serve LMS content to classrooms without internet. This is a hardware product with its own manufacturing, distribution, and support logistics. It is NOT a software feature of this LMS. The PWA offline capability (FGAP-006) handles software-side offline; the hardware box is a distinct product track. FEATURE_SCOPE excludes it permanently for this software repository. |
| **Affected Components** | None (hardware product, not in this repository) |
| **Affected Routes** | None |
| **Affected APIs** | None |
| **Affected Workflows** | None |
| **Affected Roles** | None |
| **Owner Required** | N/A — excluded, not deferred |
| **External Dependency** | N/A |
| **Future Impact** | NONE for this repository |
| **Reopen Criteria** | NEVER for this repository — hardware product requires separate initiative |
| **Related Documents** | docs/00_authority/FEATURE_SCOPE.md §3 |
| **Related Register Entries** | PM-OS-006 (PWA offline — the software-side offline feature that IS in scope) |

---

## Gap Sprint Priority Queue

For planning purposes — suggested sprint order for PLANNED-DEFERRED items:

| Priority | PM ID | Feature | Sprint Type | Estimated Complexity |
|---|---|---|---|---|
| P1 (finance) | PM-OS-005 | Reconciliation admin screen | Backend HTTP + frontend screen | Small |
| P2 (PWA) | PM-OS-006 | PWA offline frontend | Frontend only | Medium |
| P3 (AI) | PM-OS-003 | AI copilot overlay | Design + frontend + possibly backend | Large |
| P4 (risk) | PM-OS-004 | Learner risk insights | Backend service + frontend panel | Medium |
| P5 (adaptive) | PM-OS-002 | Adaptive learning engine | Backend service + frontend paths | Large |
| P6 (parent) | PM-OS-001 | Parent/guardian portal | Product + backend + frontend | X-Large |
| P7 (i18n) | PM-OS-007 | Urdu i18n | Frontend-heavy + translation | Medium |
| P8 (vocational) | PM-OS-008 | Vocational training | Backend + frontend | Large |
| P9 (marketplace) | PM-OS-009 | Teacher marketplace | Architecture + backend + frontend | X-Large |
| P10 (excl.) | PM-OS-010 | Offline box hardware | N/A — excluded | — |
