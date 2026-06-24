# FEATURE GAP REGISTER

Status: Active
Date: 2026-06-23
Phase: Phase 2.95 — Residual Decision Collapse
Owner: Shared

---

## Purpose

Canonical register of platform features that are **intended** but have no current implementation. These are not excluded features — they are planned features requiring a sprint before the frontend can build them.

An implementation gap means:
- Product intent is documented (design doc, authority doc mention, or AI_OPERATING_CONTEXT reference)
- No service or HTTP endpoint exists yet
- Frontend screens for the feature cannot be built until the gap is closed
- Gap is tracked here so it is not lost

---

## FGAP-001: Parent/Guardian Portal

| Field | Value |
|---|---|
| **ID** | FGAP-001 |
| **Source** | PDC-009; AI_OPERATING_CONTEXT QUICK_REFERENCE |
| **Product intent** | "Parents — monitor student progress" (AI_OPERATING_CONTEXT) |
| **What exists** | Nothing. No service, no role_key, no workflow, no design doc. |
| **What is missing** | Parent user type + authentication flow; parent-facing workflows (view child progress, attendance, fee status, upcoming sessions); parent notification preferences; parent portal navigation and screens. |
| **Frontend screens blocked** | Parent dashboard, child progress view, attendance view, fee status view, parent notification settings |
| **Sprint type** | Product + backend + frontend sprint |
| **Sprint dependencies** | rbac-service parent role_key defined; user-service parent-child relationship; enrollment-service parent access to child enrollment; progress-service parent read access; possibly a parent-service or parent-portal-service |
| **Blocking frontend now?** | No — admin, teacher, learner journeys proceed without parent portal |

---

## FGAP-002: Adaptive Learning Engine

| Field | Value |
|---|---|
| **ID** | FGAP-002 |
| **Source** | PDC-006; FEATURE_SCOPE §2; `docs/designs/adaptive-learning-engine.md` |
| **Product intent** | Design doc exists. FEATURE_SCOPE §3 defers to "current phase" — not permanent exclusion. |
| **What exists** | `docs/designs/adaptive-learning-engine.md` — design only. |
| **What is missing** | adaptive-learning-service (no service in manifest); adaptive content path API; learner state machine for adaptive progression; integration with progress-service and recommendation-service. |
| **Frontend screens blocked** | Adaptive content path screen; adaptive recommendation panel in learner course view |
| **Sprint type** | Backend + frontend sprint |
| **Sprint dependencies** | adaptive-learning-service built and registered in manifest; API contract defined |
| **Blocking frontend now?** | No — standard linear content delivery proceeds |

---

## FGAP-003: AI Learning Copilot Overlay

| Field | Value |
|---|---|
| **ID** | FGAP-003 |
| **Source** | PDC-007; FEATURE_SCOPE §2; `docs/designs/ai-learning-copilot.md` |
| **Product intent** | Design doc describes a full copilot overlay — persistent AI assistant across the learner experience. |
| **What exists** | `ai-tutor-service`, `recommendation-service`, `skill-inference-service`, `course-generation-service` — all in manifest. The per-lesson AI tutor panel IS buildable now from ai-tutor-service. The copilot overlay (persistent cross-screen AI) is the gap. |
| **What is missing** | Copilot overlay UI architecture (floating panel, context-aware responses across screens); service integration that passes learner context (current course, lesson, assessment state) to a copilot coordinator; conversation history persistence. |
| **Frontend screens blocked** | Persistent copilot overlay component; cross-screen AI context panel |
| **Sprint type** | Design + frontend + (possibly) backend copilot coordinator service sprint |
| **Sprint dependencies** | Copilot scope defined; context-passing API designed; conversation storage confirmed |
| **Blocking frontend now?** | No — ai-tutor-service panel in course view proceeds; copilot overlay is additive |

---

## FGAP-004: Learner Risk Insights

| Field | Value |
|---|---|
| **ID** | FGAP-004 |
| **Source** | PDC-008; FEATURE_SCOPE §2; `docs/designs/learner-risk-insights-design.md` |
| **Product intent** | Design doc exists. Early-warning system for at-risk learners based on engagement and progress signals. |
| **What exists** | `docs/designs/learner-risk-insights-design.md` — design only. `skill-analytics-service` and `learning-analytics-service` in manifest cover general analytics but not the risk model. |
| **What is missing** | Learner risk scoring service (no service in manifest); risk threshold configuration; risk alert delivery; teacher/admin dashboard panel for at-risk learner list. |
| **Frontend screens blocked** | Risk insights dashboard panel (teacher/admin); at-risk learner list; intervention action panel |
| **Sprint type** | Backend (risk service) + frontend (dashboard panel) sprint |
| **Sprint dependencies** | Risk scoring service built and registered; API returns learner risk score and flags |
| **Blocking frontend now?** | No — analytics dashboards using skill-analytics-service and learning-analytics-service proceed |

---

## FGAP-005: Reconciliation Admin Screen

| Field | Value |
|---|---|
| **ID** | FGAP-005 |
| **Source** | PDC-005; `services/commerce/service.py` |
| **Product intent** | Payment reconciliation is implemented in `integrations/payments/reconciliation.py` and wired into `services/commerce/service.py`. An admin audit screen for reconciled vs unreconciled payments is implied. |
| **What exists** | `PaymentReconciliationEngine` in `integrations/payments/reconciliation.py`. `schedule_reconciliation_job()`, `apply_reconciliation()`, `configure_reconciliation()` in `services/commerce/service.py`. No HTTP endpoint. |
| **What is missing** | HTTP endpoint exposing reconciliation state (e.g., `GET /api/v1/admin/reconciliation/report`); admin frontend screen showing reconciliation audit (matched / unmatched / disputed payments). |
| **Frontend screens blocked** | Reconciliation audit screen in admin dashboard; payment dispute panel |
| **Sprint type** | Backend (HTTP endpoint) + frontend (admin screen) sprint |
| **Sprint dependencies** | Reconciliation HTTP endpoint added to checkout-service or a new admin/finance-service |
| **Blocking frontend now?** | No — payment status is visible via `GET /api/v1/checkout/orders/{id}`; reconciliation audit is an additive admin view |

---

## FGAP-006: PWA Offline Frontend

| Field | Value |
|---|---|
| **ID** | FGAP-006 |
| **Source** | PDC-010; FEATURE_SCOPE §1.4 |
| **Product intent** | `offline-sync-service` is in the service manifest and `services/offline-sync/` exists — backend sync capability is in scope. The frontend PWA layer (service worker, offline caching, sync queue UI) is the gap. |
| **What exists** | `backend/services/offline-sync-service/` — in manifest. `services/offline-sync/` — domain layer. Backend sync state management. |
| **What is missing** | Next.js service worker registration; offline cache manifest (assets, API responses); learner progress sync queue in frontend; sync status indicator UI; reconnect-triggered sync flow. |
| **Frontend screens blocked** | Offline mode indicator; sync status component; offline content cache management |
| **Sprint type** | Frontend PWA sprint |
| **Sprint dependencies** | offline-sync-service HTTP API confirmed (sync state endpoint); Next.js PWA plugin or custom service worker |
| **Blocking frontend now?** | No — standard Next.js online experience proceeds; PWA layer is additive |

---

## Gap Summary

| ID | Feature | Backend Gap? | Frontend Gap? | Sprint Type |
|---|---|---|---|---|
| FGAP-001 | Parent portal | Yes (no service) | Yes (no screens) | Product + backend + frontend |
| FGAP-002 | Adaptive learning | Yes (no service) | Yes (no screens) | Backend + frontend |
| FGAP-003 | AI copilot overlay | Partial (copilot coordinator) | Yes (no overlay UI) | Design + frontend |
| FGAP-004 | Learner risk insights | Yes (no service) | Yes (no panel) | Backend + frontend |
| FGAP-005 | Reconciliation admin | Yes (no HTTP endpoint) | Yes (no screen) | Backend + frontend |
| FGAP-006 | PWA offline frontend | No (backend exists) | Yes (no PWA layer) | Frontend only |

---

## What Is NOT a Gap (Genuinely Out of Scope)

| Feature | Reason | Source |
|---|---|---|
| Urdu i18n | Formally deferred (MO-041) | FEATURE_SCOPE §3 |
| Vocational training | Formally deferred (MO-042) | FEATURE_SCOPE §3 |
| Teacher marketplace | Formally deferred (MO-043) | FEATURE_SCOPE §3 |
| Offline box (hardware) | Formally deferred (MO-044) | FEATURE_SCOPE §3 |
| Global education model | Design only, no product intent for current phase | FEATURE_SCOPE §3 |
| Interaction/discussion service | No design, no mention in any authority doc | PDC-004 |
