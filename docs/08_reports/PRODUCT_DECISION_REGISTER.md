# PRODUCT DECISION REGISTER

Status: Active
Date: 2026-06-23
Phase: Phase 2.95 — Residual Decision Collapse
Owner: AI

---

## Purpose

Canonical register of all product scope, architectural, and UX decisions collapsed during Phase 2.95. Each decision includes source, evidence, options analyzed, recommended path, classification, and frontend impact.

---

## Classification Key

| Class | Meaning |
|---|---|
| RESOLVED | Repository evidence supports a clear answer. No sprint required. |
| OWNER_CONFIRMATION_ONLY | Recommended path exists. Implementation proceeds unless explicitly rejected. |
| IMPLEMENTATION_GAP | Feature is intended for the platform. No current implementation. Sprint required before frontend can build this feature. Documented — not thrown away. |

---

## PDC-001: CheckoutService Persistence

| Field | Value |
|---|---|
| **ID** | PDC-001 |
| **Source** | AI_OPERATING_CONTEXT D-001; TBD-001 |
| **Domain** | Commerce |
| **Question** | Should checkout-service receive SQLite persistence before frontend begins? |
| **Evidence** | `backend/services/checkout-service/` — `InMemoryCheckoutStore` confirmed; no `store_db.py`. TBD-001 resolved D-001: "No. checkout-service has no store_db.py." |
| **Option A** | Add `store_db.py` to checkout-service now (same pattern as 16 SQLite services). |
| **Option B** | Keep in-memory for development phase; add persistence in a backend sprint. |
| **Recommended Option** | **B — Keep in-memory.** |
| **Why** | Frontend checkout flow is contract-identical whether persistence is in-memory or SQLite. Adding SQLite now is a backend sprint item with no frontend dependency. |
| **Risks** | Checkout data (sessions, orders) lost on service restart in development. Must be resolved before production. |
| **Frontend impact** | None. Checkout screens, payment confirmation flow, and order status display are unchanged. |
| **Classification** | OWNER_CONFIRMATION_ONLY |

---

## PDC-002: Cloud Deployment Target

| Field | Value |
|---|---|
| **ID** | PDC-002 |
| **Source** | AI_OPERATING_CONTEXT D-003 |
| **Domain** | Infrastructure |
| **Question** | Which cloud platform and CI/CD pipeline targets this project? |
| **Evidence** | `infrastructure/deployment/docker-compose.yml` confirmed. `deploy-backend.yml` confirmed. No cloud provider SDK found. `common.env` contains placeholder credentials. |
| **Recommended Option** | **Docker Compose for local dev. Cloud target deferred to DevOps sprint.** |
| **Frontend impact** | Zero. Next.js 16 deploys identically to any cloud provider. |
| **Classification** | OWNER_CONFIRMATION_ONLY |

---

## PDC-003: File-Storage Service HTTP Layer

| Field | Value |
|---|---|
| **ID** | PDC-003 |
| **Source** | AI_OPERATING_CONTEXT D-004a; FEATURE_SCOPE §1.3 |
| **Domain** | Content |
| **Question** | Which HTTP service exposes the binary file upload endpoint? |
| **Evidence** | `services/file-storage/service.py` — active domain library (MO-023, Phase B). Not in `service-manifest.json`. `backend/services/content-service/` and `backend/services/media-service/` are in manifest. |
| **Recommended Option** | **Content-service owns content metadata. Binary upload target confirmed in content sprint. Frontend upload form uses stub until then.** |
| **Frontend impact** | Content upload form renders. Binary upload API endpoint is a stub pending content sprint. |
| **Classification** | OWNER_CONFIRMATION_ONLY |

---

## PDC-004: Interaction-Service Existence

| Field | Value |
|---|---|
| **ID** | PDC-004 |
| **Source** | AI_OPERATING_CONTEXT D-004b |
| **Domain** | Social/Community |
| **Question** | Does services/interaction-service exist and is it in scope? |
| **Evidence** | No `interaction-service` directory found anywhere. Not in service-manifest.json. No mention in any authority document, spec, or design doc. Zero product intent signals. |
| **Recommended Option** | **Not in scope. Does not exist. No design intent found.** |
| **Frontend impact** | None. |
| **Classification** | RESOLVED |

---

## PDC-005: Commerce Reconciliation Admin Screen

| Field | Value |
|---|---|
| **ID** | PDC-005 |
| **Source** | AI_OPERATING_CONTEXT D-005; `services/commerce/service.py` |
| **Domain** | Commerce |
| **Question** | Is a payment reconciliation admin screen in scope for the frontend? |
| **Evidence** | `services/commerce/service.py:218–281` — `apply_reconciliation()`, `schedule_reconciliation_job()` confirmed. `integrations/payments/reconciliation.py` — PaymentReconciliationEngine confirmed. No HTTP endpoint for reconciliation found in any service. Backend logic exists; HTTP layer does not. |
| **Recommended Option** | **IMPLEMENTATION GAP — reconciliation admin screen is intended but has no HTTP endpoint yet. Sprint required to: (1) expose reconciliation HTTP endpoint in checkout-service or a new admin-service, (2) build reconciliation audit screen in frontend.** |
| **Why** | Backend domain logic is implemented (reconciliation.py, configure_reconciliation). Intent is clear. The HTTP API and frontend screen are the missing layers. |
| **Frontend impact** | Gap in admin dashboard. Reconciliation audit screen exists in product intent but cannot be built until HTTP endpoint is added. |
| **Classification** | IMPLEMENTATION_GAP |

---

## PDC-006: Adaptive Learning Engine

| Field | Value |
|---|---|
| **ID** | PDC-006 |
| **Source** | FEATURE_SCOPE §2 and §3 |
| **Domain** | Learning |
| **Question** | Is adaptive learning in scope? |
| **Evidence** | `docs/designs/adaptive-learning-engine.md` — design document exists. No service in manifest. No backend implementation. FEATURE_SCOPE §3 states "Out of Scope (Current Phase) — Adaptive learning engine (design only)." |
| **Recommended Option** | **IMPLEMENTATION GAP — design exists, implementation deferred to a future phase. Not excluded permanently; deferred by FEATURE_SCOPE §3 "current phase" language.** |
| **Why** | "Current Phase" means the current build sprint, not permanent exclusion. Design doc confirms product intent. |
| **Frontend impact** | Gap in learner experience. Adaptive content path screens cannot be built until the service is implemented. |
| **Classification** | IMPLEMENTATION_GAP |

---

## PDC-007: AI Learning Copilot Scope

| Field | Value |
|---|---|
| **ID** | PDC-007 |
| **Source** | FEATURE_SCOPE §1.10 and §2 |
| **Domain** | AI |
| **Question** | What is the scope of AI features — confirmed services or full copilot vision? |
| **Evidence** | Confirmed in manifest: `ai-tutor-service`, `recommendation-service`, `skill-inference-service`, `course-generation-service`. `docs/designs/ai-learning-copilot.md` — design doc only for broader copilot overlay. |
| **Recommended Option** | **Confirmed services (ai-tutor, recommendations, course generation) are in scope now. Full AI copilot overlay is an IMPLEMENTATION GAP — design doc exists, broader scope not yet implemented.** |
| **Frontend impact** | AI tutor chat panel, recommendations widget, course generation UI: build now. Full copilot overlay: implementation gap requiring sprint. |
| **Classification** | OWNER_CONFIRMATION_ONLY (for confirmed services) + IMPLEMENTATION_GAP (for copilot overlay) |

---

## PDC-008: Learner Risk Insights

| Field | Value |
|---|---|
| **ID** | PDC-008 |
| **Source** | FEATURE_SCOPE §2 |
| **Domain** | Analytics |
| **Question** | Is learner risk insights in scope for the current frontend phase? |
| **Evidence** | `docs/designs/learner-risk-insights-design.md` — design document exists. No service in manifest. `backend/services/skill-analytics-service/` and `backend/services/learning-analytics-service/` cover general analytics but not the specific risk model. |
| **Recommended Option** | **IMPLEMENTATION GAP — design exists, no service built. Sprint required for learner risk service + frontend risk insights dashboard panel.** |
| **Frontend impact** | Gap in admin and teacher dashboards. Risk insights panel exists in product design but cannot be built until service is implemented. |
| **Classification** | IMPLEMENTATION_GAP |

---

## PDC-009: Parent/Guardian User Role

| Field | Value |
|---|---|
| **ID** | PDC-009 |
| **Source** | AI_OPERATING_CONTEXT QUICK_REFERENCE |
| **Domain** | Identity / UX |
| **Question** | Is a parent/guardian user role in scope? |
| **Evidence** | AI_OPERATING_CONTEXT explicitly lists: "Parents — monitor student progress (TBD — REQUIRES VERIFICATION)." Zero implementation: no parent-service, no parent role_key in rbac-service, no parent workflow in PRODUCT_WORKFLOWS. Design intent is documented (monitoring student progress); implementation is absent. |
| **Recommended Option** | **IMPLEMENTATION GAP — parent portal is a documented product intent with zero implementation. Sprint required for: parent user type, parent-facing workflows (view child progress, fee status, attendance), parent authentication flow.** |
| **Why** | "TBD — REQUIRES VERIFICATION" in AI_OPERATING_CONTEXT is a product gap marker, not a product exclusion. The feature is intended; it simply has no implementation yet. |
| **Frontend impact** | Gap in navigation and user journeys. Parent portal (progress monitoring, fee status, attendance view) exists in product intent but cannot be built until parent service + workflows are implemented. |
| **Classification** | IMPLEMENTATION_GAP |

---

## PDC-010: Offline Sync / PWA Architecture

| Field | Value |
|---|---|
| **ID** | PDC-010 |
| **Source** | FEATURE_SCOPE §1.4 and §3 |
| **Domain** | Learning Runtime / Frontend Architecture |
| **Question** | Must the frontend be a PWA with offline capability? |
| **Evidence** | `backend/services/offline-sync-service/` and `services/offline-sync/` — backend implementation exists. FEATURE_SCOPE §1.4 lists offline-sync-service as in-scope. FEATURE_SCOPE §3 excludes "Offline box (MO-044)" — the dedicated hardware deployment, not the sync feature itself. |
| **Recommended Option** | **IMPLEMENTATION GAP — offline-sync-service backend is in scope. PWA frontend (service worker, offline caching, sync queue UI) is an implementation gap requiring a frontend PWA sprint.** |
| **Why** | The backend sync capability exists. The frontend PWA layer does not. They are separate work items. "Offline box" hardware product is excluded; PWA sync capability is not. |
| **Frontend impact** | Gap in learner offline experience. Initial frontend build is standard Next.js. PWA sprint adds service worker, cache manifest, and sync status UI on top. |
| **Classification** | IMPLEMENTATION_GAP |

---

## PDC-011: JazzCash Webhook Reconciliation Frontend

| Field | Value |
|---|---|
| **ID** | PDC-011 |
| **Source** | PRODUCT_WORKFLOWS WF-005 |
| **Domain** | Commerce |
| **Question** | Does JazzCash webhook reconciliation require dedicated frontend screens? |
| **Evidence** | Reconciliation is backend domain logic. Frontend payment experience: submit → poll order status → show result. |
| **Recommended Option** | **Payment status screen polls `GET /api/v1/checkout/orders/{order_id}`. Reconciliation is transparent to frontend.** |
| **Frontend impact** | Payment status screen: three states (pending / success / failed). |
| **Classification** | RESOLVED |

---

## PDC-012: Frontend Navigation Model

| Field | Value |
|---|---|
| **ID** | PDC-012 |
| **Source** | USER_ROLES_AND_PERMISSIONS.md; PRE_FRONTEND_GO_NO_GO_REPORT |
| **Domain** | Navigation / RBAC |
| **Question** | Role-key-based navigation or permission-check-based navigation? |
| **Evidence** | `POST /api/v1/rbac/authorize` is the documented mechanism for UI gating per USER_ROLES_AND_PERMISSIONS.md §4. Role_key is a free-text field with no canonical system values seeded. |
| **Recommended Option** | **Permission-based navigation via `POST /api/v1/rbac/authorize`. No hardcoded role_key values in frontend routing.** |
| **Frontend impact** | All route guards call authorize endpoint. Role management screen pulls role list from API. |
| **Classification** | RESOLVED |

---

## PDC-013: Duplicate Lesson Event Topics (WF-004 OI-001)

| Field | Value |
|---|---|
| **ID** | PDC-013 |
| **Source** | PRODUCT_WORKFLOWS WF-004 |
| **Domain** | Events |
| **Question** | Do duplicate lesson event topic names require frontend handling? |
| **Evidence** | Frontend never subscribes to or publishes events. Both are internal EventBus topics. |
| **Recommended Option** | **No frontend action.** |
| **Frontend impact** | Zero. |
| **Classification** | RESOLVED |

---

## PDC-014: Root services/ Layer Classification

| Field | Value |
|---|---|
| **ID** | PDC-014 |
| **Source** | RESIDUAL_OWNER_DECISION_REGISTER carry-forward; OA-006 |
| **Domain** | Architecture |
| **Question** | Does root services/ layer classification affect frontend development? |
| **Evidence** | entitlement-service and subscription-service at root layer are guarded imports. Backend architecture only. |
| **Recommended Option** | **Backend architecture sprint. No frontend action.** |
| **Frontend impact** | Zero. |
| **Classification** | RESOLVED |

---

## Summary Table

| ID | Decision | Classification | Frontend Sprint Required? |
|---|---|---|---|
| PDC-001 | Checkout persistence | OWNER_CONFIRMATION_ONLY | No |
| PDC-002 | Cloud deployment target | OWNER_CONFIRMATION_ONLY | No |
| PDC-003 | File-storage HTTP layer | OWNER_CONFIRMATION_ONLY | No (stub until sprint) |
| PDC-004 | Interaction-service | RESOLVED | No (not in scope) |
| PDC-005 | Reconciliation admin screen | IMPLEMENTATION_GAP | Yes — commerce admin sprint |
| PDC-006 | Adaptive learning engine | IMPLEMENTATION_GAP | Yes — adaptive learning sprint |
| PDC-007 | AI copilot overlay | OWNER_CONFIRMATION_ONLY + IMPLEMENTATION_GAP | Yes — AI copilot sprint (confirmed services buildable now) |
| PDC-008 | Learner risk insights | IMPLEMENTATION_GAP | Yes — risk insights sprint |
| PDC-009 | Parent/guardian portal | IMPLEMENTATION_GAP | Yes — parent portal sprint |
| PDC-010 | Offline PWA frontend | IMPLEMENTATION_GAP | Yes — PWA sprint |
| PDC-011 | JazzCash webhook reconciliation | RESOLVED | No |
| PDC-012 | Frontend navigation model | RESOLVED | No |
| PDC-013 | Duplicate lesson event topics | RESOLVED | No |
| PDC-014 | Root services/ classification | RESOLVED | No |

**RESOLVED: 5 | OWNER_CONFIRMATION_ONLY: 3 | IMPLEMENTATION_GAP: 6 | TRUE_OWNER_DECISION: 0**
