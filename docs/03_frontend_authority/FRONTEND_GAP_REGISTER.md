# FRONTEND GAP REGISTER

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- FRONTEND_GAP_REGISTER.md (docs/08_reports/) — full backend gap register
- Phase 2.95 Decision Collapse output (FGAP series)
- FEATURE_SCOPE.md §3 (out-of-scope items)
- OWNER-REQUIRED ITEM COMPRESSION outputs (SAFE-DEFAULT and FGAP confirmations)

---

## Gap Classification

| Class | Definition |
|---|---|
| FGAP | Frontend Gap — feature backed by confirmed services, deferred from initial sprint |
| BACKEND-TBD | Backend API not yet specified; frontend screen exists, endpoint is TBD |
| OUT-OF-SCOPE | Formally excluded from product scope (not a gap — a boundary) |

---

## FGAP Series — Deferred Frontend Features

### FGAP-001: Parent/Guardian Portal

| Field | Value |
|---|---|
| **Status** | Deferred — not in initial sprint |
| **Backend services** | None yet — parent-service does not exist in service catalog |
| **What is missing** | Parent login flow, parent dashboard, child progress view, timetable view, fee view |
| **What exists** | Nothing — no routes, no screens, no backend service |
| **Blocking condition** | Backend parent-service must exist; parent role must be defined in RBAC |
| **Screen impact** | Approximately 6 screens: ParentLogin, ParentDashboard, ChildProgress, ChildAttendance, ChildFees, ChildTimetable |
| **Sprint type** | Full new portal sprint |
| **Frontend workaround** | None. Route /parent/* returns 404 until sprint ships. |

---

### FGAP-002: Adaptive Learning Path

| Field | Value |
|---|---|
| **Status** | Deferred — design-only, no implementation |
| **Backend services** | adaptive-learning-service (referenced in FEATURE_SCOPE.md as design-only, MO-042) |
| **What is missing** | Adaptive content sequencing UI, learning path recommendation per learner |
| **What exists** | Static learning path view (course structure in fixed order) |
| **Blocking condition** | adaptive-learning-service must implement content sequencing API |
| **Screen impact** | Adaptive path view on learner dashboard (widget), adaptive lesson order in course player |
| **Sprint type** | Widget + player modification (additive) |
| **Frontend workaround** | Show static lesson order; no adaptive path indicator in initial build. |

---

### FGAP-003: AI Copilot Overlay

| Field | Value |
|---|---|
| **Status** | Deferred — design-only, not in initial sprint |
| **Backend services** | ai-copilot-service (referenced but design-only in FEATURE_SCOPE.md MO-043) |
| **What is missing** | Floating AI copilot accessible from any screen; context-aware suggestions |
| **What exists** | AiTutorPanel (lesson-level text chat in course player) — confirmed and in scope |
| **Blocking condition** | ai-copilot-service must expose multi-context API; distinct from ai-tutor-service |
| **Screen impact** | Global overlay component (additive to all screens); does not affect existing screens |
| **Sprint type** | Global overlay + multi-context API sprint |
| **Frontend workaround** | No copilot icon. AiTutorPanel in course player is the complete AI feature in initial build. |

---

### FGAP-004: Risk Insights Dashboard

| Field | Value |
|---|---|
| **Status** | Deferred |
| **Backend services** | risk-scoring-service (referenced in FEATURE_SCOPE.md §1.9 but not fully specified) |
| **What is missing** | At-risk learner list widget (admin/teacher dashboards); individual risk score display |
| **What exists** | General analytics dashboard without risk dimension |
| **Blocking condition** | risk-scoring-service API must be specified; risk scoring algorithm must be defined |
| **Screen impact** | Widget on DASH-001 (admin), widget on DASH-002 (teacher); no new standalone screen |
| **Sprint type** | Widget addition sprint |
| **Frontend workaround** | Dashboard renders without risk widget. No placeholder shown. |

---

### FGAP-005: Reconciliation Admin Screen

| Field | Value |
|---|---|
| **Status** | Deferred (SAFE-DEFAULT: reconciliation.py confirmed active but screen not built) |
| **Backend services** | reconciliation-service (reconciliation.py confirmed active) |
| **What is missing** | Admin screen to view reconciliation run results, discrepancies, manual resolution |
| **What exists** | reconciliation.py runs server-side; no frontend consumer |
| **Blocking condition** | reconciliation-service must expose a query API for reconciliation results |
| **Screen impact** | 1 new admin screen: /admin/reconciliation |
| **Sprint type** | Single screen sprint |
| **Frontend workaround** | Route /admin/reconciliation returns 404. No nav item in sidebar. |
| **Placeholder** | Admin settings page can include a "Reconciliation: manual check only" note during gap period |

---

### FGAP-006: PWA Offline Mode

| Field | Value |
|---|---|
| **Status** | Deferred |
| **Backend services** | N/A — frontend-only implementation requirement |
| **What is missing** | Service worker; offline content caching; offline lesson player; sync-on-reconnect for progress |
| **What exists** | Online-only web application |
| **Blocking condition** | PWA manifest + service worker implementation; offline progress queue mechanism |
| **Screen impact** | All learner screens need offline variants; progress sync mechanism needed |
| **Sprint type** | Full PWA sprint (cross-cutting) |
| **Frontend workaround** | Online-only. No "Download for offline" button. No offline indicator. |

---

## BACKEND-TBD Items

These are screens fully within scope for the initial sprint but whose API endpoints require service-level inspection before implementation. These are NOT gaps — they are pending API discovery tasks for the implementation sprint.

| Screen | Service | What is TBD |
|---|---|---|
| User list / detail | user-service | GET /users, GET /users/:id, PATCH /users/:id |
| Course list / detail | course-service | GET /courses, GET /courses/:id, PATCH |
| Lesson management | lesson-service | GET /lessons, POST, PATCH |
| Content upload (metadata) | content-service | POST /content |
| Content upload (binary) | media-service | POST /media |
| Assessment management | assessment-service | GET /assessments, POST |
| Assessment grading | attempt-service | GET /attempts, PATCH (grade) |
| Certificate view | certificate-service | GET /certificates/:id |
| Notifications | notification-service | GET /notifications |
| AI tutor chat | ai-tutor-service | POST /ai-tutor |
| Recommendations | recommendation-service | GET /recommendations |
| Academy operations | academy-commerce-service | Full CRUD: branches, batches, timetable, attendance, fees |
| Revenue analytics | revenue-service | GET /revenue |
| Billing / invoices | invoice-billing-service | GET /invoices |
| Feature flags | feature-flag-service | GET /feature-flags, PATCH |
| Learning analytics | learning-analytics-service | GET /analytics/learning |
| Skill analytics | skill-analytics-service | GET /analytics/skills |
| LTI config | lti-service | GET/POST /lti |

---

## OUT-OF-SCOPE Items (not gaps — formal boundaries)

| Item | Authority | Why excluded |
|---|---|---|
| MO-041 through MO-044 | FEATURE_SCOPE.md §3 | Formally out of scope — no UI required |
| Global education model (non-PK) | FEATURE_SCOPE.md §3 | Pakistan-first; multi-market is future phase |
| Adaptive learning full implementation | FEATURE_SCOPE.md §3 | Design-only; tracked as FGAP-002 |
| Real-time collaboration tools | Not in FEATURE_SCOPE.md | Not in scope |
| Video conferencing integration | Not in FEATURE_SCOPE.md | Not in scope |

---

## Gap Summary

| Category | Count |
|---|---|
| FGAP (deferred features) | 6 |
| BACKEND-TBD (API discovery pending) | 18 services |
| OUT-OF-SCOPE (formal exclusions) | 6 items |
| Screens blocked by FGAPs | ~6 (parent portal) |
| Widgets blocked by FGAPs | ~4 (risk, copilot, adaptive, reconciliation) |

**All 6 FGAPs are non-blocking for initial frontend sprint.** Initial build covers: admin/teacher/learner roles, all confirmed API endpoints, all 10 product workflows (with backend-only steps noted), and all confirmed in-scope features.
