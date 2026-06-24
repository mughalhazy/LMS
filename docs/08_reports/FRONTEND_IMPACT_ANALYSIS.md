# FRONTEND IMPACT ANALYSIS

Status: Complete
Date: 2026-06-23
Phase: Phase 2.95 — Residual Decision Collapse
Owner: AI

---

## Purpose

For each residual decision collapsed in Phase 2.95, this document identifies the concrete impact on navigation, menus, screens, dashboards, permissions, workflows, forms, components, user journeys, and role experiences.

---

## Scope Established by Phase 2.95

Three frontend user roles have confirmed implementation and can be built now. Parent/guardian is an implementation gap — intended but not yet built.

| Role | Description | Status | Authority |
|---|---|---|---|
| Admin | Tenant admin / platform operator | Build now | FEATURE_SCOPE §1.1, §1.2 |
| Teacher | Instructor managing classes and content | Build now | FEATURE_SCOPE §1.3, §1.7 |
| Learner | Student consuming content, paying fees | Build now | FEATURE_SCOPE §1.4, §1.5, §1.6 |
| Parent/Guardian | Monitor child progress, fee status, attendance | **IMPLEMENTATION GAP** (FGAP-001) — parent portal sprint required | AI_OPERATING_CONTEXT |

---

## Navigation Impact

### What Is Confirmed In Scope

| Role | Top-Level Navigation |
|---|---|
| Admin | Tenants · Organizations · Branches · Users · Roles · Reports · Config · Billing · Academy Ops |
| Teacher | Courses · Batches · Timetable · Attendance · Grades · Notifications |
| Learner | My Courses · Assessments · Progress · Certificates · Payments · Notifications |

### Navigation Gaps (Intended — Sprint Required)

| Item | Gap ID | Sprint Required |
|---|---|---|
| Parent portal nav | FGAP-001 | Parent portal sprint |
| Adaptive content path | FGAP-002 | Adaptive learning sprint |
| AI copilot overlay | FGAP-003 | AI copilot sprint |
| Risk insights dashboard | FGAP-004 | Risk insights sprint |
| Reconciliation admin | FGAP-005 | Commerce admin sprint |
| Offline/sync status | FGAP-006 | PWA sprint |

### Not in Navigation (Genuinely Out of Scope)

| Item | Reason |
|---|---|
| Interaction/discussion | No design, no product intent found anywhere (PDC-004) |
| Offline box hardware | Formally deferred MO-044 |
| Urdu i18n | Formally deferred MO-041 |

---

## Screen-by-Screen Impact

### PDC-001 (Checkout Persistence) — Impact on Screens

| Screen | Impact |
|---|---|
| Checkout flow (create session → add items → submit) | None — API contract unchanged |
| Order confirmation screen | None — `GET /api/v1/checkout/orders/{order_id}` unchanged |
| Payment history screen | Data resets on service restart in dev — document this in dev notes only |

**Net screen impact: Zero.**

---

### PDC-003 (File-Storage HTTP Layer) — Impact on Screens

| Screen | Impact |
|---|---|
| Course content creation (admin/teacher) | Content metadata form: use content-service API (confirmed in manifest). Binary upload mechanism (endpoint) TBD — placeholder component acceptable. |
| SCORM upload screen | Targets lms-scorm-store via content-service or media-service; exact endpoint TBD |
| Video upload screen | Same as above; targets lms-video-store |

**Net screen impact:** "Upload content" screen exists in scope. Binary upload API endpoint confirmed as TBD pending content sprint. Screen can render with a stub upload action.

---

### PDC-007 (AI Copilot vs Tutor) — Impact on Screens

| Screen | Impact |
|---|---|
| Learner course view | AI tutor panel/chat widget in scope (ai-tutor-service confirmed). Panel scope: text-based tutor interaction per lesson. |
| Learner dashboard | Recommendations component (recommendation-service confirmed). |
| Admin course builder | AI course generation option (course-generation-service confirmed). |
| Learner dashboard | No full-screen "copilot" overlay. |

**Net screen impact:** Three AI-related UI components confirmed in scope. Broader copilot vision deferred to separate sprint.

---

### PDC-010 (Offline PWA) — Impact on Frontend Architecture

| Concern | Impact |
|---|---|
| PWA manifest | Not required |
| Service worker | Not required |
| Offline caching strategy | Not required |
| Sync queue UI | Not required |
| Optional sync status indicator | May be added later if offline-sync-service exposes sync state API |

**Net architecture impact:** Standard Next.js web application. No progressive web app infrastructure.

---

### PDC-011 (JazzCash Webhook) — Impact on Screens

| Screen | Impact |
|---|---|
| Payment initiation (submit checkout) | `POST /api/v1/checkout/orders/{order_id}/initiate-payment` |
| Payment status / confirmation | Poll `GET /api/v1/checkout/orders/{order_id}` for status transitions |
| Payment result page | Three states: pending (spinner), success (confirmation), failed (retry option) |

**Net screen impact:** Payment status polling pattern confirmed. Three-state payment result screen.

---

### PDC-012 (Navigation Model) — Impact on Routing

| Concern | Impact |
|---|---|
| Route guards | Use `POST /api/v1/rbac/authorize` — check permission before rendering |
| Role-based nav items | Driven by permission results, not role_key string comparisons |
| Admin role management screen | Display roles from `GET /api/v1/rbac/roles`; no hardcoded role list |
| Permission denied page | 403 from authorize endpoint → redirect to permission denied screen |

**Net routing impact:** All route guards call authorize endpoint. No hardcoded role_key in Next.js middleware or route protection logic.

---

## Dashboard Composition

### Admin Dashboard

| Widget | Source Service | Status |
|---|---|---|
| Tenant overview | tenant-service | Confirmed in scope |
| Branch summary | academy-commerce-service | Confirmed in scope |
| Revenue summary | revenue-service | Confirmed in scope |
| Enrollment stats | enrollment-service | Confirmed in scope |
| Notification dispatch status | notification-service | Confirmed in scope |
| Learner analytics | learning-analytics-service | Confirmed in scope |
| Reconciliation audit | None | Excluded (PDC-005) |
| Risk insights | None | Excluded (PDC-008) |

### Teacher Dashboard

| Widget | Source Service | Status |
|---|---|---|
| My batches / timetable | academy-commerce-service | Confirmed in scope |
| Attendance summary | academy-commerce-service | Confirmed in scope |
| Assessment results | assessment-service | Confirmed in scope |
| Content upload status | content-service / media-service | In scope; upload API TBD |

### Learner Dashboard

| Widget | Source Service | Status |
|---|---|---|
| Enrolled courses | enrollment-service | Confirmed in scope |
| Progress summary | progress-service | Confirmed in scope |
| Upcoming assessments | assessment-service | Confirmed in scope |
| Recommendations | recommendation-service | Confirmed in scope (PDC-007) |
| AI tutor access | ai-tutor-service | Confirmed in scope (PDC-007) |
| Certificates | certificate-service | Confirmed in scope |
| Payment history | checkout-service | Confirmed in scope (data resets in dev per PDC-001) |

---

## Form Impact

### Forms NOT Changed by Collapsed Decisions

- Login form
- Course creation form
- Lesson editor
- Enrollment form
- Assessment creation form
- JazzCash checkout form
- Notification preference form
- Branch/batch management forms

### Forms Affected by Collapsed Decisions

| Form | Effect |
|---|---|
| Content upload form (binary) | Upload action target TBD pending content sprint (PDC-003); form renders with stub |
| Role assignment form | Role list populated from `GET /api/v1/rbac/roles` API, not hardcoded (PDC-012) |
| AI tutor chat input | Scope: per-lesson tutor chat; not full copilot (PDC-007) |

---

## Permission Impact

### Authorize Endpoint Usage (PDC-012)

All role-gated UI elements must call:

```
POST /api/v1/rbac/authorize
{
  "subject_type": "user",
  "subject_id": "<user_id>",
  "permission_id": "<permission_key>",
  "scope_type": "<scope_type>",
  "scope_id": "<scope_id>",
  "tenant_id": "<tenant_id>"
}
```

Response: `{ "allowed": true/false, "decision_reason": "...", "audit_id": "..." }`

### Required Frontend Headers

| Header | Value | Required on |
|---|---|---|
| `Authorization` | `Bearer <access_token>` | All authenticated requests |
| `X-Tenant-Id` | `<tenant_id>` | All requests |

### JWT User Identifier

- `access_token.sub` = `session_id` (NOT user_id)
- `user_id` is in login response: `response.user.user_id`
- `tenant_id` is in login response: `response.user.tenant_id`
- Roles are NOT in login response — fetch from `GET /api/v1/rbac/assignments?subject_id=<user_id>&tenant_id=<tenant_id>`

---

## User Journey Impact

### Admin Journey — Unchanged by Collapsed Decisions

1. Login → Admin dashboard
2. Create/manage branches and batches
3. Assign teachers to batches
4. Manage timetables
5. View fee tracking and invoicing
6. View enrollment and analytics reports
7. Manage tenant configuration and capability gating
8. Manage users and RBAC roles

### Teacher Journey — Minor Change (PDC-003)

1. Login → Teacher dashboard
2. Manage batch content → Upload materials (binary upload TBD)
3. Mark attendance
4. Set and grade assessments
5. View student progress

### Learner Journey — Confirmed (PDC-007 AI tutor added)

1. Login → Learner dashboard
2. Browse/enroll in courses
3. View enrolled courses and progress
4. Complete lessons (with AI tutor panel available)
5. Take assessments
6. Pay fees via JazzCash/EasyPaisa checkout
7. Receive certificates on completion
8. Receive notifications (WhatsApp/SMS/Email/Push)

---

## Role Experience Matrix

| Feature | Admin | Teacher | Learner | Parent |
|---|---|---|---|---|
| Login | ✅ | ✅ | ✅ | GAP (FGAP-001) |
| Dashboard | Admin dash | Teacher dash | Learner dash | GAP |
| Course management | ✅ Create/edit | ✅ Manage content | ✅ View/enroll | GAP (read-only child view) |
| Timetable | ✅ Manage | ✅ View own | ✅ View own | GAP (child timetable) |
| Attendance | ✅ Reports | ✅ Mark | ✅ View own | GAP (child attendance) |
| Assessments | ✅ Create | ✅ Grade | ✅ Take | GAP (child results) |
| Payments | ✅ Admin view | N/A | ✅ Checkout | GAP (fee status for child) |
| AI tutor | Admin config | N/A | ✅ Chat panel | N/A |
| Analytics | ✅ Full | ✅ Class-level | ✅ Own progress | GAP (child progress summary) |
| Offline mode | N/A | N/A | GAP (FGAP-006 — PWA sprint) | N/A |
| Adaptive learning | N/A | N/A | GAP (FGAP-002 — adaptive sprint) | N/A |
| Risk insights | GAP (FGAP-004) | GAP (class-level) | N/A | N/A |
| AI copilot overlay | N/A | N/A | GAP (FGAP-003) | N/A |
| Reconciliation screen | GAP (FGAP-005) | N/A | N/A | N/A |

---

## Summary — Net Frontend Impact

| Category | Before Phase 2.95 | After Phase 2.95 |
|---|---|---|
| User roles confirmed for initial build | Ambiguous | 3: admin, teacher, learner |
| User roles as implementation gaps | Unknown | 1: parent/guardian (FGAP-001) |
| Navigation items (build now) | Partial | Fully defined for admin/teacher/learner |
| Navigation gaps (sprint required) | Unknown | 6 gaps documented (FGAP-001 through FGAP-006) |
| AI screens (build now) | Unclear | ai-tutor panel, recommendations, course generation |
| AI screens (sprint required) | Unknown | Copilot overlay (FGAP-003) |
| PWA required for initial build | Unknown | No — standard Next.js; PWA is FGAP-006 |
| Permission model | Role-key vs authorize unclear | Authorize endpoint confirmed |
| Binary upload target | Unknown | Stub pending content sprint |

**All frontend-impacting ambiguity is eliminated. Gaps are documented as planned work, not discarded.**
