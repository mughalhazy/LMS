# FRONTEND NAVIGATION MODEL

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- FEATURE_SCOPE.md §1.1–§1.10
- USER_ROLES_AND_PERMISSIONS.md (scope types, role model)
- POST_COLLAPSE_FRONTEND_READINESS.md (confirmed nav items)
- FRONTEND_IMPACT_ANALYSIS.md (Phase 2.95)
- AI_OPERATING_CONTEXT.md (PDC-012: permission-based nav confirmed)

---

## Navigation Principles

1. **Permission-based only.** Nav items are rendered based on `POST /api/v1/rbac/authorize` results. No role_key hardcoding.
2. **Tenant-scoped.** All nav and data is isolated by `tenant_id`.
3. **Role-derived experience.** The server-side RBAC assignment determines what a user sees — the frontend only reflects it.
4. **No parent/guardian nav items** in initial build (FGAP-001).

---

## Top-Level Navigation Structure

### Public (Unauthenticated)

```
/login                     Login page
/forgot-password           Password reset initiation
/reset-password            Password reset confirmation
/sso/callback              SSO assertion callback
/signup                    Tenant registration (WF-001)
```

---

### Admin Navigation

Primary nav for users with ADMIN-scope role assignment (scope_type = TENANT or ORG_UNIT).

```
Dashboard
  /admin/dashboard          Tenant overview, enrollment stats, revenue summary

Organization & Tenancy
  /admin/tenants            Tenant list (platform admin only)
  /admin/tenants/:id        Tenant detail, config, lifecycle
  /admin/organizations      Org hierarchy
  /admin/organizations/:id  Org detail
  /admin/departments        Department management
  /admin/departments/:id
  /admin/institutions       Institution management (Pakistan multi-school)
  /admin/groups             Group management
  /admin/cohorts            Cohort management

People
  /admin/users              User management list
  /admin/users/new          Create user
  /admin/users/:id          User profile, role assignments
  /admin/users/:id/roles    User RBAC assignments

Access Control
  /admin/roles              Role management
  /admin/roles/new          Create role
  /admin/roles/:id          Role detail, permission bindings
  /admin/permissions        Permission catalog (read-only)
  /admin/policy-rules       Policy rules (SOD, explicit deny, time-window)
  /admin/audit-log          RBAC audit log (requires audit.view_tenant)

Academy Operations (Pakistan)
  /admin/branches           Branch management list
  /admin/branches/new       Create branch
  /admin/branches/:id       Branch detail
  /admin/batches            Batch management list
  /admin/batches/new        Create batch
  /admin/batches/:id        Batch detail, teacher assignment
  /admin/batches/:id/timetable    Timetable view/edit
  /admin/batches/:id/students     Student roster
  /admin/fee-structures     Fee structure management

Courses & Content
  /admin/courses            Course catalog management
  /admin/courses/new        Create course (AI-assisted optional)
  /admin/courses/:id        Course detail, publish/unpublish
  /admin/programs           Program/pathway management
  /admin/learning-paths     Learning path management
  /admin/content            Content library

Commerce & Billing
  /admin/billing            Invoices and billing overview
  /admin/billing/invoices   Invoice list
  /admin/billing/invoices/:id   Invoice detail
  /admin/subscriptions      Subscription management
  /admin/revenue            Revenue analytics
  /admin/reconciliation     [FGAP-005 — not built in initial sprint]

AI Services
  /admin/ai/course-generation   AI course generation tool
  /admin/ai/settings            AI service configuration

Analytics & Reporting
  /admin/analytics          Learning analytics dashboard
  /admin/analytics/reports  Report builder / saved reports
  /admin/analytics/skills   Skill analytics

Notifications
  /admin/notifications      Notification log / dispatch center

System
  /admin/integrations       Integration management (LTI, HRIS, webhooks)
  /admin/webhooks           Webhook configuration
  /admin/feature-flags      Feature flag management
  /admin/settings           Platform settings
  /admin/onboarding         Onboarding wizard (new tenant)
```

---

### Teacher Navigation

For users with TEACHER-scope role assignment.

```
Dashboard
  /teacher/dashboard        My classes, attendance summary, assessment results

Courses & Content
  /teacher/courses          My assigned courses
  /teacher/courses/:id      Course detail
  /teacher/courses/:id/lessons        Lesson list
  /teacher/courses/:id/lessons/new    Create lesson
  /teacher/courses/:id/lessons/:lid   Lesson editor
  /teacher/courses/:id/content        Content upload and management
  /teacher/courses/:id/students       Enrolled students

Academy (Pakistan)
  /teacher/batches          My batches
  /teacher/batches/:id      Batch detail
  /teacher/batches/:id/timetable      Timetable view
  /teacher/batches/:id/attendance     Attendance marking
  /teacher/batches/:id/grades         Grade entry

Assessments
  /teacher/assessments      Assessment list (created by me)
  /teacher/assessments/new  Create assessment
  /teacher/assessments/:id  Assessment detail, submissions
  /teacher/assessments/:id/grade      Grade submissions

Communications
  /teacher/notifications    My notification inbox

Profile
  /profile                  My profile and settings
```

---

### Learner Navigation

For users with LEARNER-scope role assignment.

```
Dashboard
  /learner/dashboard        My enrolled courses, progress, AI recommendations

Courses
  /learner/courses          Course catalog (browse + enrolled)
  /learner/courses/:id      Course overview + enroll action
  /learner/courses/:id/learn      Course player (lessons + AI tutor panel)
  /learner/courses/:id/learn/:lid  Lesson view (content + SCORM + AI tutor)
  /learner/courses/:id/assessments   My assessments for this course

Learning
  /learner/progress         My overall progress summary
  /learner/learning-paths   My learning path assignments
  /learner/programs         My enrolled programs

Assessment
  /learner/assessments      My upcoming and completed assessments
  /learner/assessments/:id  Assessment player (quiz/exam)

Achievements
  /learner/certificates     My certificates
  /learner/certificates/:id Certificate view / download
  /learner/badges           My earned badges

Commerce
  /learner/payments         Payment history
  /learner/checkout         Checkout flow (session → items → submit → payment → confirmation)
  /learner/orders/:id       Order detail and status

AI Tutor
  (embedded panel on /learner/courses/:id/learn — not a standalone top-level route)

Communications
  /learner/notifications    My notification inbox

Profile
  /profile                  My profile and settings
```

---

## Shared Routes (All Authenticated Roles)

```
/profile               User profile: name, email, avatar, password change
/notifications         Notification center (shared across roles)
/403                   Access denied page
/404                   Not found page
/500                   Server error page
```

---

## Navigation Guard Rules

All authenticated routes require:

1. Valid `access_token` in session storage (or HTTP-only cookie)
2. `X-Tenant-Id` header resolvable from stored `tenant_id`
3. For permission-gated sub-routes: `POST /api/v1/rbac/authorize` must return `"decision": "allow"`

### Authorization Check Pattern

```
Before rendering any gated UI element:
POST /api/v1/rbac/authorize
{
  "subject_type": "user",
  "subject_id": "<user_id from login response.user.user_id>",
  "permission_key": "<required permission>",
  "resource_type": "<resource>",
  "resource_id": "<id or '*'>"
}
→ If "decision": "deny" → redirect to /403
→ If 401 → attempt token refresh, then retry
```

### Token Refresh Pattern

```
On 401 from any API:
1. POST /api/v2/auth/tokens/refresh with refresh_token
2. If 200 → store new access_token, retry original request
3. If 401 on refresh → clear session, redirect to /login
```

---

## Nav Items Excluded (Out of Scope)

| Item | Reason |
|---|---|
| Parent portal nav | FGAP-001 — parent sprint required |
| Adaptive learning path | FGAP-002 — backend + frontend sprint |
| AI copilot overlay | FGAP-003 — design + frontend sprint |
| Risk insights dashboard | FGAP-004 — backend + frontend sprint |
| Reconciliation admin | FGAP-005 — backend endpoint + frontend sprint |
| Offline mode / sync status | FGAP-006 — PWA sprint |
| Teacher marketplace | MO-043 — formally deferred |
| Urdu i18n toggle | MO-041 — formally deferred |
| Vocational training | MO-042 — formally deferred |
| Offline box | MO-044 — formally deferred |
