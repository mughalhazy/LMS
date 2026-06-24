# FRONTEND GAP REGISTER

Status: Active
Date: 2026-06-23
Phase: Post-OWNER-REQUIRED ITEM COMPRESSION
Owner: AI

---

## Purpose

Frontend-centric view of all feature gaps that affect what can be built in Frontend Authority Capture and subsequent frontend sprints. Derived from FEATURE_GAP_REGISTER.md (the canonical gap register) and updated after OWNER-REQUIRED ITEM COMPRESSION to reflect the full deterministic picture.

For backend-only gaps (services with missing HTTP endpoints but no frontend component), see BACKEND_GAP_REGISTER.md.

---

## How to Read This Register

- **Gaps** are planned features with confirmed product intent — they are NOT discarded or out of scope.
- A gap means: backend and/or frontend sprint required before this feature can be built.
- Frontend Authority Capture proceeds by documenting what currently exists in frontend/. Gap items indicate what will be absent from that documentation.
- Gaps do not block Frontend Authority Capture — they are documented within it as "planned but absent."

---

## FGAP-001: Parent/Guardian Portal

| Field | Value |
|---|---|
| **Gap ID** | FGAP-001 |
| **Source** | PDC-009 — AI_OPERATING_CONTEXT.md (TBD marker for parent role) |
| **Sprint type** | Product + Backend + Frontend |
| **What exists** | Parent/guardian user role is documented in AI_OPERATING_CONTEXT with a TBD marker. No backend service, no schema, no API contract. No frontend screens. |
| **What is missing** | Parent user model, parent-child linking logic, parent API endpoints, parent frontend screens (child progress view, child attendance, fee status, child timetable) |
| **Frontend screens blocked** | Parent dashboard, child progress monitor, fee status view, child timetable view |
| **API blocked** | Parent-specific routes on enrollment-service, progress-service, attendance (academy-commerce), fee/billing |
| **Navigation blocked** | Parent nav section (build now: admin/teacher/learner confirmed) |
| **Prerequisites** | Product sprint to define parent-child data model and permission scope; backend sprint for APIs; then frontend sprint |
| **Compression update** | No change from Phase 2.95. FGAP-001 was not an OWNER-REQUIRED item. |

---

## FGAP-002: Adaptive Learning Engine

| Field | Value |
|---|---|
| **Gap ID** | FGAP-002 |
| **Source** | PDC-006 — docs/designs/adaptive-learning-engine.md |
| **Sprint type** | Backend + Frontend |
| **What exists** | Design document (docs/designs/adaptive-learning-engine.md). No service in manifest. |
| **What is missing** | adaptive-learning-service backend implementation; frontend adaptive content path UI |
| **Frontend screens blocked** | Adaptive content path view within course (learner); adaptive pacing indicators |
| **Navigation blocked** | None (adaptive content is a sub-view within existing course screen) |
| **Compression update** | No change. FGAP-002 confirmed as gap not exclusion. |

---

## FGAP-003: AI Copilot Overlay

| Field | Value |
|---|---|
| **Gap ID** | FGAP-003 |
| **Source** | PDC-007 — docs/designs/ai-learning-copilot.md |
| **Sprint type** | Design + Frontend (possible coordinator service) |
| **What exists** | Design doc for a full-screen AI copilot overlay. ai-tutor-service, recommendation-service, course-generation-service are all in manifest and confirmed buildable now. |
| **What is missing** | The broader "copilot" overlay UI that surfaces AI assistance across all screens simultaneously |
| **Frontend screens blocked** | No new screen — copilot is an overlay on existing screens |
| **Compression update** | SAFE-DEFAULT applied (ITEM-07): build confirmed AI services now; copilot overlay is this gap. OC-004 closed. |

---

## FGAP-004: Learner Risk Insights Dashboard

| Field | Value |
|---|---|
| **Gap ID** | FGAP-004 |
| **Source** | PDC-008 — docs/designs/learner-risk-insights-design.md |
| **Sprint type** | Backend + Frontend |
| **What exists** | Design document. No risk insights service in manifest. |
| **What is missing** | Risk insights service (or extension to learning-analytics-service); risk score calculation logic; admin/teacher risk insights dashboard screen |
| **Frontend screens blocked** | Risk insights dashboard widget (admin), at-risk learner list (teacher) |
| **Navigation blocked** | None (risk insights is a dashboard widget, not a nav item) |
| **Compression update** | No change. FGAP-004 confirmed as gap. |

---

## FGAP-005: Reconciliation Admin Screen

| Field | Value |
|---|---|
| **Gap ID** | FGAP-005 |
| **Source** | PDC-005 — services/commerce/reconciliation.py |
| **Sprint type** | Backend (HTTP endpoint) + Frontend |
| **What exists** | services/commerce/reconciliation.py — complete domain-layer reconciliation algorithm. integrations/payments/reconciliation.py — JazzCash/EasyPaisa adapter-level reconciliation. |
| **What is missing** | HTTP endpoint exposing reconciliation results (add to checkout-service or create commerce-admin-service). Admin frontend screen to view reconciliation report, flag discrepancies, trigger manual reconciliation. |
| **Frontend screens blocked** | Reconciliation admin screen (admin role only) |
| **Compression update** | ITEM-05 AUTO-CLOSED (confirmed both reconciliation files are active; question resolved). FGAP-005 sprint dependency unchanged. |

---

## FGAP-006: PWA Offline Frontend

| Field | Value |
|---|---|
| **Gap ID** | FGAP-006 |
| **Source** | PDC-010 — offline-sync-service (backend exists) |
| **Sprint type** | Frontend only |
| **What exists** | offline-sync-service in service-manifest.json (backend confirmed). Docker Compose confirmed. Backend offline sync API (endpoints TBD in service inspection). |
| **What is missing** | PWA manifest, service worker, offline caching strategy, sync queue UI, offline state indicators in frontend |
| **Frontend screens blocked** | None for online users. Offline state variants of existing screens blocked. |
| **Architecture impact** | Standard Next.js web app is the current default (PDC-010 resolved). PWA layer is additive and does not break online screens. |
| **Compression update** | No change. FGAP-006 confirmed as gap; PDC-010 safe default is standard Next.js (non-PWA). |

---

## Gap Summary

| Gap | Sprint Type | Backend Missing | Frontend Missing | Blocks FE Auth Capture? |
|---|---|---|---|---|
| FGAP-001 Parent portal | Full stack | Yes (model + API) | Yes (all screens) | No (documented as absent) |
| FGAP-002 Adaptive learning | Backend + Frontend | Yes (service) | Yes (content path UI) | No |
| FGAP-003 AI copilot overlay | Frontend | No (confirmed services exist) | Yes (overlay UI) | No |
| FGAP-004 Learner risk insights | Backend + Frontend | Yes (service or extension) | Yes (dashboard widget) | No |
| FGAP-005 Reconciliation screen | Backend (HTTP) + Frontend | Yes (endpoint only) | Yes (admin screen) | No |
| FGAP-006 PWA offline | Frontend | No (offline-sync-service exists) | Yes (service worker + offline UI) | No |

**None of the 6 gaps block Frontend Authority Capture.** They are documented within it as planned-but-absent items.

---

## Features NOT Gaps (confirmed in scope, build now)

| Feature | Service(s) | Authority |
|---|---|---|
| Authentication + SSO | auth-service | FEATURE_SCOPE §1.1 |
| RBAC + permissions | rbac-service | FEATURE_SCOPE §1.1 |
| Multi-tenancy | tenant-service, org-service | FEATURE_SCOPE §1.2 |
| Course + lesson + content | course-service, lesson-service, content-service | FEATURE_SCOPE §1.3 |
| Enrollment + progress | enrollment-service, progress-service | FEATURE_SCOPE §1.4 |
| Assessment + certificates | assessment-service, certificate-service | FEATURE_SCOPE §1.5 |
| Commerce + payments | checkout-service, payment-service | FEATURE_SCOPE §1.6 |
| Academy ops (branches, batches) | academy-commerce-service | FEATURE_SCOPE §1.7 |
| Notifications (WhatsApp/SMS/Email) | notification-service | FEATURE_SCOPE §1.8 |
| Analytics + reporting | learning-analytics-service, revenue-service | FEATURE_SCOPE §1.9 |
| AI tutor + recommendations | ai-tutor-service, recommendation-service | PDC-007 |
| AI course generation | course-generation-service | PDC-007 |

---

## Out of Scope (genuinely excluded — not gaps)

| Item | Reason |
|---|---|
| Interaction / discussion features | No design, no product intent, no code (PDC-004 — does not exist) |
| Offline box hardware | Formally deferred — MO-044 (FEATURE_SCOPE §3) |
| Urdu i18n | Formally deferred — MO-041 |
| Teacher marketplace | Formally deferred — MO-043 |
| Vocational/trades specialization | Formally deferred — MO-042 |

---

## Related Documents

- FEATURE_GAP_REGISTER.md — canonical gap register (source of truth for sprints)
- OWNER_CONFIRMATION_REGISTER.md — 4 OC items (all non-blocking)
- POST_COLLAPSE_FRONTEND_READINESS.md — Frontend readiness gate (GO issued)
- FRONTEND_IMPACT_ANALYSIS.md — Screen/nav/journey impact analysis
- DETERMINISM_CERTIFICATION_REPORT.md — Determinism certification
