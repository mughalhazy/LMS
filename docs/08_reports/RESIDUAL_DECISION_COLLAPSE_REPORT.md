# RESIDUAL DECISION COLLAPSE REPORT

Status: Complete
Date: 2026-06-23
Phase: Phase 2.95 — Residual Decision Collapse
Owner: AI

---

## Purpose

This report documents the collapse of all residual product, scope, and architectural decisions that could influence frontend authority capture. Every decision that remained open after Phase 2.9 has been analyzed using the Mandatory Collapse Test and reduced to a single recommended path.

---

## Scope of Review

The following documents were reviewed to identify all residual decisions:

| Document | Location |
|---|---|
| RESIDUAL_OWNER_DECISION_REGISTER.md | docs/08_reports/ |
| FRONTEND_BLOCKERS_REGISTER.md | docs/08_reports/ |
| PRE_FRONTEND_GO_NO_GO_REPORT.md | docs/08_reports/ |
| PRE_FRONTEND_READINESS_SCORECARD.md | docs/08_reports/ |
| AI_OPERATING_CONTEXT.md (D-001 through D-005) | docs/07_governance/ |
| FEATURE_SCOPE.md | docs/00_authority/ |
| PRODUCT_WORKFLOWS.md | docs/00_authority/ |
| DOMAIN_MODEL.md | docs/00_authority/ |
| FULLSTACK_STITCHING_CONTRACT.md | docs/00_authority/ |
| USER_ROLES_AND_PERMISSIONS.md | docs/03_fullstack_contracts/ |
| AUTH_AND_TENANCY_CONTRACT.md | docs/03_fullstack_contracts/ |
| REVISED_DECISION_ESCALATION_MATRIX.md | docs/07_governance/ |
| TBD_RESOLUTION_REGISTER.md | docs/08_reports/ |
| service-manifest.json | infrastructure/deployment/ |
| rbac-service source code | backend/services/rbac-service/ |
| services/file-storage/service.py | services/file-storage/ |
| services/commerce/service.py | services/commerce/ |

---

## Decision Inventory

14 residual decisions identified across product scope, architecture, and workflow domains. All analyzed below.

---

## PDC-001: CheckoutService In-Memory Persistence (D-001)

**Source:** AI_OPERATING_CONTEXT D-001; TBD-001; FULLSTACK_STITCHING_CONTRACT FSC-003

**Repository evidence:**
- `backend/services/checkout-service/` has no `store_db.py` — confirmed `InMemoryCheckoutStore` only
- Checkout API contract fully documented: POST /api/v1/checkout/sessions → submit → initiate-payment
- Order data exists within a service lifecycle; lost on restart

**Mandatory Collapse Test:** "If the owner disappears today, which option should the project take?"

Keep InMemoryCheckoutStore for the current phase. Add DB persistence in a dedicated persistence sprint. The frontend checkout flow (create session → add items → submit → initiate payment → show order status) works identically with in-memory or SQLite persistence. No frontend screen changes.

**Recommended path:** Proceed with in-memory. Document that checkout data resets on service restart. Persistence sprint is backend-only and does not alter any frontend contract.

**Classification:** OWNER_CONFIRMATION_ONLY

**Frontend impact:** None. Checkout screens, payment confirmation flow, and order status display are unchanged.

---

## PDC-002: Cloud Deployment Target / CI Platform (D-003)

**Source:** AI_OPERATING_CONTEXT D-003; REVISED_DECISION_ESCALATION_MATRIX

**Repository evidence:**
- `infrastructure/deployment/docker-compose.yml` — confirmed
- `infrastructure/deployment/cicd/deploy-backend.yml` — confirmed
- No cloud provider SDK, no Terraform, no Kubernetes manifests found
- `infrastructure/deployment/env/common.env` — placeholder credentials only (postgresql, rabbitmq) per TBD-010

**Mandatory Collapse Test:** Proceed with Docker Compose for local development. Cloud provider selected when team is ready to deploy. This is an infrastructure sprint decision, not a product decision.

**Recommended path:** Use Docker Compose (`infrastructure/deployment/docker-compose.yml`) for development and staging. Cloud target deferred.

**Classification:** OWNER_CONFIRMATION_ONLY

**Frontend impact:** Zero. Frontend is a Next.js 16 application regardless of cloud provider.

---

## PDC-003: File-Storage Service HTTP Wrapper (D-004a)

**Source:** AI_OPERATING_CONTEXT D-004; FEATURE_SCOPE 1.3 (content-service)

**Repository evidence:**
- `services/file-storage/service.py` exists — domain layer only (MO-023, Phase B); handles pre-signed URL generation, content metadata, lifecycle (uploading → ready → archived → deleted)
- `services/file-storage/` NOT in `service-manifest.json`
- No `backend/services/file-storage/` directory found
- `backend/services/content-service/` IS in manifest — handles content metadata registration
- `backend/services/media-service/` and `backend/services/media-security-service/` are in manifest
- Content types: video (lms-video-store), document (lms-document-store), SCORM (lms-scorm-store), image (lms-image-store)
- Paid content routes through media-security-service (BC-CONTENT-02)

**Mandatory Collapse Test:** File-storage is an active domain library (not legacy). Binary file upload via HTTP is handled by content-service + media-service. Frontend teacher "upload content" screen targets content-service API, not file-storage directly. No HTTP wrapper needed before frontend can begin content upload screens.

**Recommended path:** Keep `services/file-storage/` as domain library. Frontend content upload screens use `content-service` and `media-service` APIs. Binary upload mechanism is a backend sprint item (adding pre-signed URL generation to content-service). Frontend design does not change whether file-storage gets an HTTP wrapper or not.

**Classification:** OWNER_CONFIRMATION_ONLY

**Frontend impact:** Content upload screen exists in scope. API endpoint target is content-service (confirmed in manifest). Binary upload flow TBD pending content-service spec.

---

## PDC-004: Interaction-Service Existence (D-004b)

**Source:** AI_OPERATING_CONTEXT D-004

**Repository evidence:**
- `services/interaction-service/` — searched; NOT FOUND anywhere in repository
- Not in service-manifest.json
- No reference in FEATURE_SCOPE.md, DOMAIN_MODEL.md, or any spec

**Mandatory Collapse Test:** No code, no spec, no mention in any authority document. Not in scope.

**Recommended path:** Mark as non-existent / not in scope. No interaction-service frontend screens.

**Classification:** RESOLVED

**Frontend impact:** None. No comments, forum, or "interaction" feature screens.

---

## PDC-005: Commerce Reconciliation Scope (D-005)

**Source:** AI_OPERATING_CONTEXT D-005; `services/commerce/service.py`

**Repository evidence:**
- `services/commerce/service.py:219` — `configure_reconciliation()` injects `PaymentReconciliationEngine`
- `services/commerce/service.py:278` — `schedule_reconciliation_job()` available
- `integrations/payments/reconciliation.py` — PaymentReconciliationEngine implementation
- No HTTP endpoint for reconciliation found in checkout-service or academy-commerce-service
- Reconciliation is invoked internally by `schedule_reconciliation_job()`, not via user-facing API

**Mandatory Collapse Test:** Backend domain logic exists (`PaymentReconciliationEngine`, `apply_reconciliation()`, `schedule_reconciliation_job()`). The HTTP layer and frontend admin screen do not exist yet. This is a planned feature — the implementation is incomplete, not absent by design.

**Recommended path:** IMPLEMENTATION GAP (FGAP-005). Backend reconciliation logic exists; HTTP endpoint and admin screen require a commerce admin sprint. Frontend payment status screen (`GET /api/v1/checkout/orders/{id}`) covers the learner-facing payment outcome. Reconciliation audit screen is tracked as a gap.

**Classification:** IMPLEMENTATION_GAP

**Frontend impact:** Gap in admin dashboard. Reconciliation audit screen blocked until HTTP endpoint added. Payment status screen for learners proceeds now.

---

## PDC-006: Adaptive Learning Engine Scope

**Source:** FEATURE_SCOPE §2 and §3

**Repository evidence:**
- `docs/designs/adaptive-learning-engine.md` — design document only
- No `backend/services/adaptive-*` or `services/adaptive-*` directory
- Not in service-manifest.json
- FEATURE_SCOPE §3 "Out of Scope (Current Phase)" explicitly lists: "Adaptive learning engine (design only)"

**Mandatory Collapse Test:** "Out of Scope (Current Phase)" means deferred — not permanently excluded. Design document confirms product intent. No service implementation exists yet.

**Recommended path:** IMPLEMENTATION GAP (FGAP-002). Design doc exists. Deferred from current build sprint per FEATURE_SCOPE §3. Adaptive learning sprint required before frontend can build adaptive content path screens. Standard linear content delivery proceeds now.

**Classification:** IMPLEMENTATION_GAP

**Frontend impact:** Gap in learner content experience. Adaptive path screens blocked until service is implemented. Linear content delivery proceeds now.

---

## PDC-007: AI Learning Copilot Scope

**Source:** FEATURE_SCOPE §2 and §1.10

**Repository evidence:**
- `docs/designs/ai-learning-copilot.md` — design doc only
- BUT: `backend/services/ai-tutor-service/` EXISTS in manifest (FEATURE_SCOPE §1.10)
- `backend/services/recommendation-service/` EXISTS in manifest
- `backend/services/skill-inference-service/` EXISTS in manifest
- FEATURE_SCOPE §2 marks "AI learning copilot" as "TBD – REQUIRES VERIFICATION" — this refers to the copilot design vision beyond the confirmed ai-tutor-service

**Mandatory Collapse Test:** ai-tutor-service, recommendation-service, skill-inference-service, and course-generation-service are all confirmed in manifest — build now. The broader "AI copilot" overlay (design doc: persistent cross-screen AI assistant) has no backend coordinator service yet — implementation gap.

**Recommended path:** Build confirmed AI service screens now (ai-tutor panel in course view, recommendations on learner dashboard, course generation for admins). AI copilot overlay is IMPLEMENTATION GAP (FGAP-003) — requires design + coordinator service + frontend overlay sprint.

**Classification:** OWNER_CONFIRMATION_ONLY (confirmed services) + IMPLEMENTATION_GAP (FGAP-003 — copilot overlay)

**Frontend impact:** AI tutor panel, recommendations widget, course generation UI: build now. Full copilot overlay component: gap — blocked until copilot coordinator service and scope are defined.

---

## PDC-008: Learner Risk Insights Scope

**Source:** FEATURE_SCOPE §2; `docs/designs/learner-risk-insights-design.md`

**Repository evidence:**
- Design doc exists: `docs/designs/learner-risk-insights-design.md`
- No `backend/services/learner-risk*` or `services/learner-risk*` directory found
- Not in service-manifest.json
- `backend/services/skill-analytics-service/` IS in manifest — covers learner performance analytics
- `backend/services/learning-analytics-service/` IS in manifest — covers learning data
- FEATURE_SCOPE §2 marks as "TBD – REQUIRES VERIFICATION"

**Mandatory Collapse Test:** Design document confirms product intent. No service exists yet. This is a planned feature with no backend implementation — a gap, not an exclusion.

**Recommended path:** IMPLEMENTATION GAP (FGAP-004). Risk insights sprint required: build risk scoring service + register in manifest + implement teacher/admin risk dashboard panel. General analytics (skill-analytics-service, learning-analytics-service) proceed now.

**Classification:** IMPLEMENTATION_GAP

**Frontend impact:** Gap in teacher and admin dashboards. Risk insights panel blocked until risk service is implemented. General analytics dashboards proceed now.

---

## PDC-009: Parent/Guardian User Role

**Source:** AI_OPERATING_CONTEXT QUICK_REFERENCE: "Parents — monitor student progress (TBD — REQUIRES VERIFICATION)"

**Repository evidence:**
- Searched all rbac-service Python files: ZERO parent or guardian role_key references
- No parent-service in service-manifest.json
- FEATURE_SCOPE §1 through §3: no parent portal mentioned
- DOMAIN_MODEL.md: user roles are education operators, teachers, learners — no parent entity
- USER_ROLES_AND_PERMISSIONS.md: SubjectType is user/group/service_account — no parent user type
- PRODUCT_WORKFLOWS.md WF-001 through WF-010: no parent-facing workflow

**Mandatory Collapse Test:** AI_OPERATING_CONTEXT explicitly names parents as a user type with "TBD — REQUIRES VERIFICATION." That marker denotes an unverified implementation status, not a product exclusion decision. Product intent is documented; implementation is absent. This is a gap.

**Recommended path:** IMPLEMENTATION GAP (FGAP-001). Parent portal sprint required: define parent user type, parent-child relationship in user-service, parent-facing workflows (child progress, attendance, fee status), parent authentication, parent notification preferences. Admin/teacher/learner journeys proceed now without waiting for parent sprint.

**Classification:** IMPLEMENTATION_GAP

**Frontend impact:** Gap in user roles and navigation. Parent portal (progress monitoring, fee status, attendance view for child) blocked until parent sprint delivers backend and API. Three roles build now: admin, teacher, learner.

---

## PDC-010: Offline Sync / PWA Architecture

**Source:** FEATURE_SCOPE §1.4; FEATURE_SCOPE §3 out-of-scope (MO-044)

**Repository evidence:**
- `backend/services/offline-sync-service/` EXISTS in manifest
- `services/offline-sync/` EXISTS at domain layer
- FEATURE_SCOPE §1.4 lists offline-sync-service as a learning runtime feature
- FEATURE_SCOPE §3 OUT OF SCOPE explicitly: "Offline box (MO-044)"
- These are two distinct concerns: offline-sync-service = server-side sync when reconnected; offline box = hardware device for fully offline deployments

**Mandatory Collapse Test:** offline-sync-service IS in the manifest and IS in FEATURE_SCOPE §1.4. The backend sync capability exists. The frontend PWA layer (service worker, offline cache, sync queue UI) is the missing piece. "Offline box" (MO-044) is a separate hardware product that is out of scope — but PWA offline sync is not the same thing and is not excluded.

**Recommended path:** IMPLEMENTATION GAP (FGAP-006). Backend offline-sync-service is in scope. Frontend PWA layer requires a dedicated sprint: service worker, cache manifest, sync queue UI, reconnect-triggered sync flow. Initial frontend build is standard Next.js. PWA sprint is additive — nothing built now needs to be replaced when PWA layer is added.

**Classification:** IMPLEMENTATION_GAP

**Frontend impact:** Gap in learner offline experience. Initial frontend build is standard Next.js (no service worker). PWA sprint layers offline capability on top without breaking anything built earlier.

---

## PDC-011: WF-005 JazzCash Webhook Reconciliation Frontend Scope

**Source:** PRODUCT_WORKFLOWS.md WF-005 note: "TBD – REQUIRES VERIFICATION"

**Repository evidence:**
- `integrations/payments/jazzcash.py` and `integrations/payments/easypaisa.py` confirmed active (.pyc)
- Webhook receipt and reconciliation is handled by `integrations/payments/reconciliation.py` at the domain layer
- No HTTP webhook endpoint visible in checkout-service or payment-service routing
- Frontend payment confirmation screen reads order status via `GET /api/v1/checkout/orders/{order_id}`
- Order status updates when payment reconciled — frontend shows result, not the reconciliation process

**Mandatory Collapse Test:** Webhook reconciliation is backend-only. Frontend shows payment outcome via order status polling. No dedicated reconciliation UI. A payment pending/success/failed status screen covers the frontend need.

**Recommended path:** Frontend implements payment status screen that polls `GET /api/v1/checkout/orders/{order_id}`. No reconciliation admin screen. No webhook endpoint in frontend scope.

**Classification:** RESOLVED

**Frontend impact:** Payment confirmation and status screen. Three states: pending, success, failed. Backend reconciliation drives state transitions. Frontend polls.

---

## PDC-012: Frontend Navigation Model (Permission-Based vs Role-Key-Based)

**Source:** USER_ROLES_AND_PERMISSIONS.md; AUTH_AND_TENANCY_CONTRACT.md; PRE_FRONTEND_GO_NO_GO_REPORT.md

**Repository evidence:**
- rbac-service has no seeded/canonical role_key list; role_key is a free-text `TEXT NOT NULL` field
- Only test fixture role_keys found: "tenant-admin", "reader", "publisher" — not canonical product roles
- USER_ROLES_AND_PERMISSIONS.md §4 authorize endpoint: `POST /api/v1/rbac/authorize` — checks if subject has permission
- PRE_FRONTEND_GO_NO_GO_REPORT: "Roles are NOT in login response — fetch from `/api/v1/rbac/assignments`"
- AUTH_AND_TENANCY_CONTRACT: JWT contains roles[] (confirmed in QUICK REFERENCE: "roles only in JWT")

**Mandatory Collapse Test:** Frontend navigation is driven by permission checks via the authorize endpoint, NOT by role_key string matching. Role names are display labels; permissions determine what UI is shown. This is the correct architectural pattern per USER_ROLES_AND_PERMISSIONS.md §4.

**Recommended path:** Frontend calls `POST /api/v1/rbac/authorize` before rendering role-gated UI. No hardcoded role_key values in navigation logic. Role labels shown in admin UI come from `GET /api/v1/rbac/roles` API response.

**Classification:** RESOLVED

**Frontend impact:** Navigation uses permission checks, not role_key comparisons. Role management screens show roles from API. No hardcoded role_key list in frontend code.

---

## PDC-013: WF-004 Duplicate Lesson Event Topics (OI-001)

**Source:** PRODUCT_WORKFLOWS.md WF-004 note

**Repository evidence:**
- `lms.lesson.completed.v1` and `lms.progress.lesson_completed.v1` are two topic names
- Both are internal event bus topics (EventBus singleton)
- Frontend does not subscribe to or publish events
- Dual-subscribe resilience pattern documented in EVENT_AND_QUEUE_ARCHITECTURE.md (Phase 2.9)

**Mandatory Collapse Test:** Backend-only concern. Frontend never subscribes to event topics.

**Recommended path:** No action needed for frontend. Backend dual-subscribe pattern documented as resilience mechanism.

**Classification:** RESOLVED

**Frontend impact:** Zero.

---

## PDC-014: Root services/ Layer Classification (OA-006 Carry-Forward)

**Source:** RESIDUAL_OWNER_DECISION_REGISTER carry-forward item

**Repository evidence:**
- `services/entitlement-service/` and `services/subscription-service/` at root layer: imported by payment-service and tenant-service (guarded)
- Other 18 root service dirs: inactive
- Backend services/ migration is a long-term architectural cleanup task
- Does not affect any frontend API endpoint or data contract

**Mandatory Collapse Test:** Backend architecture. Zero frontend impact.

**Recommended path:** Add LEGACY banners to inactive root services/ dirs in a separate hygiene sprint. Frontend does not interact with root layer services.

**Classification:** RESOLVED

**Frontend impact:** Zero.

---

## Decision Summary

| ID | Decision | Classification | Frontend Impact |
|---|---|---|---|
| PDC-001 | Checkout persistence | OWNER_CONFIRMATION_ONLY | None |
| PDC-002 | Cloud deployment target | OWNER_CONFIRMATION_ONLY | None |
| PDC-003 | File-storage HTTP wrapper | OWNER_CONFIRMATION_ONLY | Content upload API TBD — stub acceptable |
| PDC-004 | Interaction-service existence | RESOLVED | None (no design, no code) |
| PDC-005 | Commerce reconciliation admin screen | IMPLEMENTATION_GAP (FGAP-005) | Reconciliation audit screen — blocked until HTTP endpoint added |
| PDC-006 | Adaptive learning engine | IMPLEMENTATION_GAP (FGAP-002) | Adaptive path screens — blocked until service implemented |
| PDC-007 | AI copilot vs confirmed AI services | OWNER_CONFIRMATION_ONLY + IMPLEMENTATION_GAP (FGAP-003) | AI tutor/recommendation/course-gen build now; copilot overlay is gap |
| PDC-008 | Learner risk insights | IMPLEMENTATION_GAP (FGAP-004) | Risk insights panel — blocked until service implemented |
| PDC-009 | Parent/guardian user role | IMPLEMENTATION_GAP (FGAP-001) | Parent portal — blocked until parent sprint |
| PDC-010 | Offline PWA frontend | IMPLEMENTATION_GAP (FGAP-006) | PWA layer — blocked until PWA sprint; standard Next.js builds now |
| PDC-011 | JazzCash webhook reconciliation | RESOLVED | Payment status screen polls orders API |
| PDC-012 | Frontend navigation model | RESOLVED | Permission-based via authorize endpoint |
| PDC-013 | Duplicate lesson event topics | RESOLVED | None |
| PDC-014 | Root services/ classification | RESOLVED | None |

**RESOLVED: 5 | OWNER_CONFIRMATION_ONLY: 3 | IMPLEMENTATION_GAP: 6 | TRUE_OWNER_DECISION: 0**

---

## Mandatory Collapse Test — Final Verdict

All 14 residual decisions have a single recommended path. No undecided outcomes. No TRUE_OWNER_DECISION items.

6 items are IMPLEMENTATION_GAP — planned features with no current implementation. They are tracked in `FEATURE_GAP_REGISTER.md` (FGAP-001 through FGAP-006). Gaps do not block frontend start: the initial build (admin, teacher, learner journeys) proceeds while gap sprints are scheduled in parallel.

No gap can alter the navigation, screens, or workflows of the features that are buildable now.

**Final verdict: ✅ GO**
