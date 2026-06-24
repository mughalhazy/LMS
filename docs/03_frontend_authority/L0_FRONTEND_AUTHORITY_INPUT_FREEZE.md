# L0 FRONTEND AUTHORITY INPUT FREEZE

Status: L0 FROZEN
Date: 2026-06-24
Phase: Phase 3.5 — L0 Frontend Authority Input Freeze
Owner: AI
Authority Sources: 13 documents (see Section 0)

---

## VERDICT: L0 FROZEN

All 6 frontend implementation gaps (FGAPs) are classified as non-blocking deferred features. No open ambiguity affects navigation, screens, permissions, workflows, or user journeys in the initial sprint. All 8 determinism certification domains pass.

**Initial sprint scope: Admin (all features) + Teacher (all features) + Learner (all features)**

No Claude Design or Claude Code agent may invent items not present in this document. This freeze is the contract between authority capture and design/implementation.

---

## Section 0: Source Documents

All inputs in this document are derived exclusively from:

| Doc | Location | Role in Freeze |
|---|---|---|
| FRONTEND_AUTHORITY_MASTER.md | docs/03_frontend_authority/ | Architecture constraints, service map |
| FRONTEND_ROUTE_CATALOG.md | docs/03_frontend_authority/ | All ~95 routes |
| FRONTEND_SCREEN_CATALOG.md | docs/03_frontend_authority/ | All 27 screens |
| FRONTEND_DASHBOARD_CATALOG.md | docs/03_frontend_authority/ | All 4 dashboards |
| FRONTEND_NAVIGATION_MODEL.md | docs/03_frontend_authority/ | Navigation structure per role |
| FRONTEND_ROLE_EXPERIENCE_MATRIX.md | docs/03_frontend_authority/ | Role × feature access |
| FRONTEND_PERMISSION_MATRIX.md | docs/03_frontend_authority/ | All permission keys |
| FRONTEND_WORKFLOW_TO_SCREEN_MAP.md | docs/03_frontend_authority/ | WF-001 through WF-010 |
| FRONTEND_API_DEPENDENCY_MAP.md | docs/03_frontend_authority/ | All screen-to-API mappings |
| FRONTEND_GAP_REGISTER.md | docs/03_frontend_authority/ | 6 FGAPs + BACKEND-TBD classification |
| PRODUCT_DECISION_REGISTER.md | docs/08_reports/ | PDC-001 through PDC-014 |
| POST_COLLAPSE_FRONTEND_READINESS.md | docs/08_reports/ | Gate assessment |
| DETERMINISM_CERTIFICATION_REPORT.md | docs/08_reports/ | 8-domain certification |

---

## Section 1: Frozen Roles

| Role | Sprint Status | RBAC Scope Types | Notes |
|---|---|---|---|
| Admin | BUILD NOW | TENANT, ORG_UNIT, BRANCH | Includes platform admin and tenant admin |
| Teacher | BUILD NOW | BRANCH, COHORT, COURSE | Scoped data served by server-side RBAC |
| Learner | BUILD NOW | COURSE, COHORT | Self-service + payment |
| Parent/Guardian | DEFERRED — FGAP-001 | TBD | parent-service does not exist; parent role undefined; sprint required |

Frontend must NOT hardcode scope-based data filtering. All data scoping is enforced server-side via RBAC.

**First-Login Routing (frozen):**

| Role | First Login Redirect | Condition |
|---|---|---|
| Admin (new tenant) | /admin/onboarding | New tenant — no prior config |
| Admin (existing) | /admin/dashboard | — |
| Teacher | /teacher/dashboard | — |
| Learner | /learner/dashboard | Show catalog if no enrollments |

---

## Section 2: Frozen Architecture Constraints

These constraints are non-negotiable. All screens, routes, and components must comply.

### 2.1 JWT Identity Model

| Claim | Value | Source |
|---|---|---|
| `access_token.sub` | session_id (NOT user_id) | auth-service login response |
| `user_id` | `response.user.user_id` | Login response body |
| `tenant_id` | `response.user.tenant_id` | Login response body |
| Roles | NOT in login response | Fetched via RBAC assignments API |

**Critical:** After login, store `user_id` and `tenant_id` from `response.user`. Do not use JWT sub as user_id.

### 2.2 Required Headers

Every authenticated API request requires:
```
Authorization: Bearer <access_token>
X-Tenant-Id: <tenant_id>
Content-Type: application/json
```

### 2.3 Permission-Based Navigation

All route guards and UI element visibility use `POST /api/v1/rbac/authorize`. No hardcoded role_key string comparisons anywhere in the frontend. Authority: PDC-012 (RESOLVED).

### 2.4 API Version Exceptions

- All services: `/api/v1/`
- auth-service: `/api/v2/auth/`
- session-service: `/api/v2/sessions/`
These two exceptions are intentional and documented (OA-009).

### 2.5 Pagination Shape

All list endpoints return:
```json
{ "items": [...], "page": 1, "page_size": 20, "total": 0 }
```
`total` is always 0 until count sprint. Frontend must show items from `items` array; must not display "0 results" when `items` is non-empty.

### 2.6 Token Refresh Pattern

On 401 from any API:
1. POST /api/v2/auth/tokens/refresh with refresh_token
2. If 200 → store new access_token; retry original request
3. If 401 on refresh → clear session; redirect to /login

---

## Section 3: Frozen Auth / Session Flow

```
Step 1: GET  /api/v2/auth/tenant?domain=<email>       ← tenant discovery (pre-submit)
Step 2: POST /api/v2/auth/sessions/login              ← { access_token, refresh_token, session_id, user: { user_id, tenant_id } }
Step 3: Store access_token, user_id, tenant_id, session_id
Step 4: GET  /api/v1/rbac/assignments?subject_id=<user_id>&tenant_id=<tenant_id>  ← load roles
Step 5: GET  /api/v1/rbac/subjects/user/{user_id}/effective-permissions?tenant_id=  ← prefetch for nav
Step 6: POST /api/v2/auth/tokens/refresh              ← on 401
Step 7: POST /api/v2/auth/sessions/logout             ← on logout
```

Exempt paths (no auth headers):
```
/health
/metrics
/.well-known/jwks.json
/api/v2/auth/sessions/login
/api/v2/auth/password/forgot
/api/v2/auth/tenant
```

---

## Section 4: Frozen Public Routes (5)

| Route | Permission | Primary API | Blocking Condition |
|---|---|---|---|
| `/login` | None (public) | POST /api/v2/auth/sessions/login, GET /api/v2/auth/tenant?domain= | Already authenticated → redirect to role dashboard |
| `/signup` | None (public) | POST /api/v1/tenants (+ Idempotency-Key) | Already authenticated → redirect |
| `/forgot-password` | None (public) | POST /api/v2/auth/password/forgot | — |
| `/reset-password` | None (token-auth) | POST /api/v2/auth/password/reset | Token expired → error state |
| `/sso/callback` | None (public) | POST /api/v2/auth/sso/callback | Provider error → error state |

---

## Section 5: Frozen Admin Routes (~46)

### 5.1 Dashboard

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/dashboard` | `analytics.view` | enrollment-service, revenue-service (TBD), learning-analytics-service (TBD) |

### 5.2 Organization & Tenancy

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/tenants` | `tenant.view_all` | GET /api/v1/tenants |
| `/admin/tenants/:tenant_id` | `tenant.view` | GET /api/v1/tenants/:id |
| `/admin/tenants/:tenant_id/config` | `tenant.update` | PATCH /api/v1/tenants/:id/configuration |
| `/admin/tenants/:tenant_id/lifecycle` | `tenant.manage_lifecycle` | POST /api/v1/tenants/:id/lifecycle/suspend etc |
| `/admin/organizations` | `org.view` | org-service (TBD) |
| `/admin/organizations/:id` | `org.view` | org-service (TBD) |
| `/admin/departments` | `department.view` | department-service (TBD) |
| `/admin/departments/:id` | `department.view` | department-service (TBD) |
| `/admin/institutions` | `institution.view` | institution-service (TBD) |
| `/admin/groups` | `group.view` | group-service (TBD) |
| `/admin/cohorts` | `cohort.view` | cohort-service (TBD) |

### 5.3 People

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/users` | `user.view` | user-service GET /api/v1/users (TBD) |
| `/admin/users/new` | `user.create` | user-service POST /api/v1/users (TBD) |
| `/admin/users/:user_id` | `user.view` | user-service GET /:id (TBD) |
| `/admin/users/:user_id/roles` | `user.view`, `permission.assign` | GET /api/v1/rbac/assignments, POST /api/v1/rbac/assignments |
| `/admin/users/:user_id/reset-password` | `user.manage_credentials` | POST /api/v2/admin/users/:id/reset-password |

### 5.4 Access Control

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/roles` | `role.view` | GET /api/v1/rbac/roles |
| `/admin/roles/new` | `role.create` | POST /api/v1/rbac/roles |
| `/admin/roles/:role_id` | `role.view` | GET /api/v1/rbac/roles/:id, GET /api/v1/rbac/permissions |
| `/admin/roles/:role_id/edit` | `role.update` | PATCH /api/v1/rbac/roles/:id, PUT /api/v1/rbac/roles/:id/permissions |
| `/admin/permissions` | `permission.view` | GET /api/v1/rbac/permissions |
| `/admin/policy-rules` | `role.manage_policy` | GET /api/v1/rbac/policy-rules |
| `/admin/policy-rules/new` | `role.manage_policy` | POST /api/v1/rbac/policy-rules |
| `/admin/audit-log` | `audit.view_tenant` | GET /api/v1/rbac/audit-log |

### 5.5 Academy Operations (Pakistan)

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/branches` | `branch.view` | academy-commerce-service (TBD) |
| `/admin/branches/new` | `branch.create` | academy-commerce-service POST (TBD) |
| `/admin/branches/:branch_id` | `branch.view` | academy-commerce-service GET (TBD) |
| `/admin/batches` | `batch.view` | academy-commerce-service (TBD) |
| `/admin/batches/new` | `batch.create` | academy-commerce-service POST (TBD) |
| `/admin/batches/:batch_id` | `batch.view` | academy-commerce-service (TBD) |
| `/admin/batches/:batch_id/timetable` | `timetable.manage` | academy-commerce-service (TBD) |
| `/admin/batches/:batch_id/students` | `enrollment.view` | GET /api/v1/enrollments?cohort_id= |
| `/admin/fee-structures` | `fee.manage` | academy-commerce-service (TBD) |

### 5.6 Courses & Content

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/courses` | `course.view` | course-service GET (TBD) |
| `/admin/courses/new` | `course.create` | course-service POST (TBD), course-generation-service |
| `/admin/courses/:course_id` | `course.view` | course-service GET (TBD) |
| `/admin/courses/:course_id/publish` | `course.publish` | course-service PATCH (TBD) |
| `/admin/programs` | `program.view` | program-service (TBD) |
| `/admin/learning-paths` | `learning_path.view` | learning-path-service (TBD) |
| `/admin/content` | `content.view` | content-service (TBD), media-service |
| `/admin/ai/course-generation` | `course.create`, `ai.use` | course-generation-service (TBD) |
| `/admin/ai/settings` | `ai.configure` | ai-tutor-service config (TBD) |

### 5.7 Commerce & Billing

| Route | Permission Key | Primary API | Note |
|---|---|---|---|
| `/admin/billing` | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/billing/invoices` | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/billing/invoices/:id` | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/subscriptions` | `subscription.view` | subscription-service (TBD) | — |
| `/admin/revenue` | `analytics.view_revenue` | revenue-service (TBD) | — |
| `/admin/reconciliation` | `reconciliation.view` | **FGAP-005** | Route returns 503/stub; no nav item |

### 5.8 Analytics

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/analytics` | `analytics.view` | learning-analytics-service (TBD) |
| `/admin/analytics/reports` | `report.view` | reporting-service (TBD) |
| `/admin/analytics/skills` | `analytics.view` | skill-analytics-service (TBD) |

### 5.9 System

| Route | Permission Key | Primary API |
|---|---|---|
| `/admin/integrations` | `integration.manage` | lti-service, hris-sync-service (TBD) |
| `/admin/webhooks` | `webhook.manage` | webhook-service (TBD) |
| `/admin/feature-flags` | `feature_flag.manage` | feature-flag-service (TBD) |
| `/admin/notifications` | `notification.manage` | notification-service (TBD) |
| `/admin/settings` | `settings.manage` | PATCH /api/v1/tenants/:id/configuration |
| `/admin/onboarding` | `tenant.configure` | onboarding-service (TBD), tenant-service |

---

## Section 6: Frozen Teacher Routes (18)

| Route | Permission Key | Primary API |
|---|---|---|
| `/teacher/dashboard` | `course.view`, `batch.view` | academy-commerce-service (TBD), assessment-service (TBD) |
| `/teacher/courses` | `course.view` | course-service (TBD) |
| `/teacher/courses/:id` | `course.view` | course-service GET (TBD) |
| `/teacher/courses/:id/lessons` | `lesson.view` | lesson-service (TBD) |
| `/teacher/courses/:id/lessons/new` | `lesson.create` | lesson-service POST (TBD) |
| `/teacher/courses/:id/lessons/:lid` | `lesson.update` | lesson-service PATCH (TBD) |
| `/teacher/courses/:id/content` | `content.upload` | content-service POST (TBD), media-service POST (TBD) |
| `/teacher/courses/:id/students` | `enrollment.view` | GET /api/v1/enrollments?course_id= |
| `/teacher/batches` | `batch.view` | academy-commerce-service (TBD) |
| `/teacher/batches/:id` | `batch.view` | academy-commerce-service (TBD) |
| `/teacher/batches/:id/timetable` | `timetable.view` | academy-commerce-service (TBD) |
| `/teacher/batches/:id/attendance` | `attendance.mark` | academy-commerce-service (TBD) |
| `/teacher/batches/:id/grades` | `assessment.grade` | assessment-service (TBD) |
| `/teacher/assessments` | `assessment.view` | assessment-service GET (TBD) |
| `/teacher/assessments/new` | `assessment.create` | assessment-service POST (TBD) |
| `/teacher/assessments/:id` | `assessment.view` | assessment-service GET (TBD) |
| `/teacher/assessments/:id/grade` | `assessment.grade` | attempt-service (TBD) |
| `/teacher/notifications` | `notification.view` | notification-service (TBD) |

---

## Section 7: Frozen Learner Routes (22)

| Route | Permission Key | Primary API | Blocking |
|---|---|---|---|
| `/learner/dashboard` | `course.view`, `progress.view` | enrollment-service, progress-service, recommendation-service (TBD) | — |
| `/learner/courses` | `course.view` | course-service GET (TBD), enrollment-service | — |
| `/learner/courses/:id` | `course.view` | course-service GET, enrollment-service | — |
| `/learner/courses/:id/learn` | `course.view`, `progress.update` | lesson-service, progress-service | Must be enrolled |
| `/learner/courses/:id/learn/:lid` | `lesson.view`, `progress.update` | lesson-service, content-service, POST /api/v1/progress/lessons/:id/upsert, ai-tutor-service | Must be enrolled |
| `/learner/courses/:id/assessments` | `attempt.view` | assessment-service, attempt-service (TBD) | — |
| `/learner/progress` | `progress.view` | GET /api/v1/progress/learners/:id | — |
| `/learner/learning-paths` | `learning_path.view` | learning-path-service (TBD) | — |
| `/learner/programs` | `program.view` | program-service (TBD) | — |
| `/learner/assessments` | `attempt.view` | assessment-service, attempt-service (TBD) | — |
| `/learner/assessments/:id` | `attempt.create` | attempt-service POST (TBD) | — |
| `/learner/certificates` | `certificate.view` | certificate-service (TBD) | — |
| `/learner/certificates/:id` | `certificate.view` | certificate-service GET (TBD) | — |
| `/learner/badges` | `badge.view` | badge-service (TBD) | — |
| `/learner/payments` | `payment.view` | GET /api/v1/checkout/orders (TBD filter) | — |
| `/learner/checkout` | `checkout.create` | POST /api/v1/checkout/sessions, /items, /submit, /initiate-payment | — |
| `/learner/orders/:id` | `payment.view` | GET /api/v1/checkout/orders/:id | — |
| `/learner/notifications` | `notification.view` | notification-service (TBD) | — |

---

## Section 8: Frozen Shared Routes (4)

| Route | Auth Required | Notes |
|---|---|---|
| `/profile` | Yes | POST /api/v2/auth/password/forgot for password change |
| `/403` | No | Shown on `"decision": "deny"` from authorize endpoint |
| `/404` | No | — |
| `/500` | No | — |

---

## Section 9: Frozen Screens (27)

| Screen ID | Name | Route | Primary Role | Workflow |
|---|---|---|---|---|
| SCR-001 | Login Screen | /login | All | WF-001, FSC-001 |
| SCR-002 | Forgot Password | /forgot-password | All | — |
| SCR-003 | Reset Password | /reset-password | All | — |
| SCR-004 | Admin Dashboard | /admin/dashboard | Admin | WF-001, WF-008 |
| SCR-005 | User Management | /admin/users | Admin | — |
| SCR-006 | User Detail | /admin/users/:user_id | Admin | — |
| SCR-007 | Role Management | /admin/roles | Admin | — |
| SCR-008 | Role Detail | /admin/roles/:role_id | Admin | — |
| SCR-009 | RBAC Audit Log | /admin/audit-log | Admin | — |
| SCR-010 | Branch Management | /admin/branches | Admin | WF-002 step 1 |
| SCR-011 | Batch Management | /admin/batches/:id | Admin | WF-002 steps 2–5 |
| SCR-012 | Timetable | /admin/batches/:id/timetable, /teacher/batches/:id/timetable | Admin, Teacher | WF-002 step 4, WF-006 step 1 |
| SCR-013 | Course Management (Admin) | /admin/courses | Admin | — |
| SCR-014 | Course Detail (Admin/Teacher) | /admin/courses/:id, /teacher/courses/:id | Admin, Teacher | — |
| SCR-015 | Content Upload | /teacher/courses/:id/content | Teacher, Admin | — |
| SCR-016 | Learner Dashboard | /learner/dashboard | Learner | WF-004 start |
| SCR-017 | Course Catalog (Learner) | /learner/courses | Learner | WF-003 |
| SCR-018 | Course Player | /learner/courses/:id/learn/:lid | Learner | WF-004 steps 1–2 |
| SCR-019 | Checkout Flow | /learner/checkout | Learner | WF-005 |
| SCR-020 | Assessment Player | /learner/assessments/:id | Learner | WF-004 steps 3–5 |
| SCR-021 | Certificate Screen | /learner/certificates/:id | Learner | WF-004 step 7 |
| SCR-022 | Teacher Dashboard | /teacher/dashboard | Teacher | — |
| SCR-023 | Attendance Marking | /teacher/batches/:id/attendance | Teacher | WF-002 |
| SCR-024 | Assessment Grading | /teacher/assessments/:id/grade | Teacher | — |
| SCR-025 | Notification Center | /notifications, /admin/notifications | All | WF-007 |
| SCR-026 | Tenant Onboarding Wizard | /admin/onboarding | Admin | WF-001 post-signup |
| SCR-027 | Policy Rules Screen | /admin/policy-rules | Admin | — |

---

## Section 10: Frozen Dashboards (4)

| Dashboard ID | Name | Route | Role | Gap Widgets Excluded |
|---|---|---|---|---|
| DASH-001 | Admin Dashboard | /admin/dashboard | Admin | FGAP-004 (risk), FGAP-005 (reconciliation) |
| DASH-002 | Teacher Dashboard | /teacher/dashboard | Teacher | FGAP-004 (at-risk learners) |
| DASH-003 | Learner Dashboard | /learner/dashboard | Learner | FGAP-002 (adaptive), FGAP-006 (offline) |
| DASH-004 | Analytics Dashboard | /admin/analytics | Admin | — |

---

## Section 11: Frozen Workflows (WF-001 through WF-010)

| Workflow | Name | Frontend Role | Screens Involved |
|---|---|---|---|
| WF-001 | Tenant Onboarding | Signup form + wizard | /signup, /admin/onboarding |
| WF-002 | Academy Setup (Pakistan) | Admin builds structure | /admin/branches/new, /admin/batches/new, /admin/batches/:id, /admin/fee-structures |
| WF-003 | Student Enrollment | Path A: self-enroll; Path B: batch + payment | /learner/courses/:id, /learner/checkout, /learner/orders/:id |
| WF-004 | Learning and Completion | Lesson → assessment → certificate | /learner/courses/:id/learn/:lid, /learner/assessments/:id, /learner/certificates/:id |
| WF-005 | Commerce Checkout (JazzCash/EasyPaisa) | Create session → pay → poll | /learner/checkout, /learner/orders/:id |
| WF-006 | Fee Tracking and Ledger | Admin views invoices, learner pays | /admin/billing, /admin/billing/invoices/:id, /admin/revenue |
| WF-007 | Notification Dispatch | Frontend is consumer only | /notifications, /admin/notifications |
| WF-008 | Revenue Anomaly Detection | Admin drills into signal | /admin/dashboard, /admin/revenue |
| WF-009 | Config and Entitlement Resolution | Feature flags, settings | /admin/feature-flags, /admin/settings |
| WF-010 | LTI Integration | LTI launch → SCORM player | /lti/launch (TBD), /learner/courses/:id/learn/:lid |

---

## Section 12: Frozen Permission Keys

### Identity & Access
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `user.create` | "Invite user" button on /admin/users | low |
| `user.view` | User list and profile | low |
| `user.update` | Edit user form | low |
| `user.delete` | Deactivate user | moderate |
| `user.manage_credentials` | Admin password reset | high |
| `session.view` | Session metadata | moderate |
| `session.revoke` | Revoke session | high |

### RBAC
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `role.view` | Role list and detail | low |
| `role.create` | "Create role" button | moderate |
| `role.update` | Edit role form | moderate |
| `role.delete` | Delete role (system roles locked) | high |
| `permission.view` | Permission catalog | low |
| `permission.assign` | Add permission/assign role | moderate |
| `role.manage_policy` | Policy rules page | high |
| `audit.view_tenant` | Audit log page | moderate |

### Tenancy
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `tenant.view` | Tenant detail | low |
| `tenant.view_all` | Platform tenant list | high |
| `tenant.update` | Edit tenant config | moderate |
| `tenant.configure` | Tenant settings | moderate |
| `tenant.manage_lifecycle` | Suspend/archive buttons | critical |
| `org.view` | Org hierarchy | low |
| `org.manage` | Create/edit orgs | moderate |

### Academy Operations (Pakistan)
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `branch.view` | Branch list and detail | low |
| `branch.create` | "Add branch" | moderate |
| `branch.update` | Edit branch | moderate |
| `batch.view` | Batch list and detail | low |
| `batch.create` | "Add batch" | moderate |
| `batch.update` | Edit batch | moderate |
| `timetable.view` | Timetable view | low |
| `timetable.manage` | Add/remove timetable slots | moderate |
| `attendance.mark` | Attendance roster | low |
| `attendance.view` | Attendance reports | low |
| `fee.manage` | Fee structure config | moderate |

### Learning & Content
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `course.view` | Course list and catalog (all roles) | low |
| `course.create` | "Create course" | moderate |
| `course.update` | Course edit form | moderate |
| `course.publish` | Publish/Unpublish | moderate |
| `course.delete` | Delete course | high |
| `lesson.view` | Lesson list and player | low |
| `lesson.create` | "Add lesson" | moderate |
| `lesson.update` | Lesson editor | moderate |
| `content.view` | Content library | low |
| `content.upload` | File upload button | moderate |
| `content.delete` | Delete content | moderate |
| `program.view` | Program management | low |
| `program.manage` | Create/edit programs | moderate |
| `learning_path.view` | Learning path page | low |

### Enrollment & Progress
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `enrollment.view` | Enrollment list, student roster | low |
| `enrollment.create` | Admin enroll / learner self-enroll | low |
| `enrollment.update` | Enrollment status transitions | moderate |
| `progress.view` | Progress summary and bars | low |
| `progress.update` | Lesson complete action (learner) | low |

### Assessment & Certification
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `assessment.view` | Assessment list and detail | low |
| `assessment.create` | "Create assessment" | moderate |
| `assessment.update` | Edit assessment | moderate |
| `assessment.grade` | Grade submission form | moderate |
| `attempt.view` | Submission list, my history | low |
| `attempt.create` | "Start assessment" button | low |
| `certificate.view` | Certificate list and viewer | low |
| `certificate.issue` | Manual certificate issuance | moderate |
| `badge.view` | Badge list | low |
| `badge.issue` | Award badge | moderate |

### Commerce & Billing
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `checkout.create` | Checkout flow | low |
| `payment.view` | Payment history, order status | low |
| `payment.initiate` | "Pay now" button | moderate |
| `billing.view` | Invoice list and overview | low |
| `billing.manage` | Create invoices | moderate |
| `subscription.view` | Subscription list | low |
| `subscription.manage` | Create/cancel subscriptions | moderate |
| `analytics.view_revenue` | Revenue dashboard | moderate |
| `reconciliation.view` | Reconciliation admin — **FGAP-005** | moderate |

### Analytics
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `analytics.view` | Analytics dashboard and widgets | low |
| `report.view` | Report list and saved reports | low |
| `report.create` | Report builder | low |
| `skill_analytics.view` | Skill analytics page | low |

### AI
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `ai.use` | AI tutor panel, recommendations widget | low |
| `ai.configure` | AI settings page | moderate |
| `ai.generate_course` | AI course generation form | moderate |

### Notifications
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `notification.view` | Notification inbox | low |
| `notification.manage` | Notification dispatch center | moderate |
| `notification.send` | Manual trigger | moderate |

### Integrations
| Permission Key | UI Element | Risk Tier |
|---|---|---|
| `integration.manage` | Integration configuration | high |
| `webhook.manage` | Webhook configuration | high |
| `feature_flag.manage` | Feature flag toggle | critical |
| `lti.configure` | LTI setup | high |
| `hris.sync` | HRIS sync trigger | moderate |

---

## Section 13: Frozen APIs — Confirmed Endpoints

These API endpoints are confirmed by code inspection or contract authority (FSC-001 through FSC-009):

| Service | Confirmed Endpoint | Purpose |
|---|---|---|
| auth-service (8100) | GET /api/v2/auth/tenant?domain= | Tenant discovery |
| auth-service | POST /api/v2/auth/sessions/login | Session create |
| auth-service | POST /api/v2/auth/tokens/refresh | Token refresh |
| auth-service | POST /api/v2/auth/sessions/logout | Session end |
| auth-service | POST /api/v2/auth/password/forgot | Reset initiation |
| auth-service | POST /api/v2/auth/password/reset | Reset completion |
| auth-service | POST /api/v2/auth/sso/callback | SSO assertion |
| rbac-service (8108) | POST /api/v1/rbac/authorize | Permission check |
| rbac-service | GET /api/v1/rbac/assignments?subject_id=&tenant_id= | Role assignments |
| rbac-service | POST /api/v1/rbac/assignments | Add assignment |
| rbac-service | DELETE /api/v1/rbac/assignments/:id | Revoke assignment |
| rbac-service | GET /api/v1/rbac/roles | Role list |
| rbac-service | POST /api/v1/rbac/roles | Create role |
| rbac-service | GET /api/v1/rbac/roles/:id | Role detail |
| rbac-service | PATCH /api/v1/rbac/roles/:id | Edit role |
| rbac-service | PUT /api/v1/rbac/roles/:id/permissions | Update permissions |
| rbac-service | GET /api/v1/rbac/permissions | Permission catalog |
| rbac-service | GET /api/v1/rbac/audit-log | Audit log |
| rbac-service | GET /api/v1/rbac/policy-rules | Policy rules |
| rbac-service | POST /api/v1/rbac/policy-rules | Create rule |
| rbac-service | PATCH /api/v1/rbac/policy-rules/:id | Update rule |
| rbac-service | DELETE /api/v1/rbac/policy-rules/:id | Delete rule |
| rbac-service | GET /api/v1/rbac/subjects/user/{user_id}/effective-permissions | Prefetch permissions |
| tenant-service (8104) | GET /api/v1/tenants | Tenant list |
| tenant-service | POST /api/v1/tenants | Create tenant |
| tenant-service | GET /api/v1/tenants/:id | Tenant detail |
| tenant-service | GET /api/v1/tenants/:id/configuration | Config detail |
| tenant-service | PATCH /api/v1/tenants/:id/configuration | Config update |
| tenant-service | GET /api/v1/tenants/:id/lifecycle | Lifecycle status |
| enrollment-service (8130) | POST /api/v1/enrollments | Create enrollment |
| enrollment-service | GET /api/v1/enrollments?learner_id= | Learner enrollments |
| enrollment-service | GET /api/v1/enrollments?course_id= | Course enrollments |
| enrollment-service | GET /api/v1/enrollments?cohort_id= | Cohort enrollments |
| progress-service | POST /api/v1/progress/lessons/:id/upsert | Save progress |
| progress-service | POST /api/v1/progress/lessons/:id/complete | Mark lesson complete |
| progress-service | GET /api/v1/progress/learners/:id | Learner summary |
| checkout-service | POST /api/v1/checkout/sessions | Create session |
| checkout-service | POST /api/v1/checkout/sessions/:id/items | Add item |
| checkout-service | POST /api/v1/checkout/sessions/:id/submit | Submit session |
| checkout-service | POST /api/v1/checkout/orders/:id/initiate-payment | Initiate payment |
| checkout-service | GET /api/v1/checkout/orders/:id | Order status (PENDING/PAID/FAILED) |

---

## Section 14: Frozen APIs — TBD Base Paths (Sprint-Discovery Required)

These services are confirmed in scope. Exact endpoints require code inspection in the API inspection sprint. Frontend may use confirmed base paths for stub implementations:

| Service | Port | Confirmed Base Path | TBD |
|---|---|---|---|
| user-service | TBD | /api/v1/users | GET list, GET /:id, POST, PATCH /:id |
| course-service | TBD | /api/v1/courses | GET list, GET /:id, POST, PATCH /:id |
| lesson-service | TBD | /api/v1/lessons | GET /:id, POST, PATCH /:id |
| content-service | TBD | /api/v1/content | POST (metadata), GET /:id |
| media-service | TBD | /api/v1/media | POST (binary upload) |
| assessment-service | TBD | /api/v1/assessments | GET /:id, GET list, POST |
| attempt-service | TBD | /api/v1/attempts | POST, GET /:id, PATCH (grade) |
| certificate-service | TBD | /api/v1/certificates | GET /:id |
| badge-service | TBD | /api/v1/badges | GET list |
| notification-service | TBD | /api/v1/notifications | GET list |
| ai-tutor-service | TBD | /api/v1/ai-tutor | POST chat |
| recommendation-service | TBD | /api/v1/recommendations | GET |
| academy-commerce-service | TBD | /api/v1/academy | Full CRUD: branches, batches, timetable, attendance, fees |
| revenue-service | TBD | /api/v1/revenue | GET summary, GET trend |
| invoice-billing-service | TBD | /api/v1/invoices | GET list, GET /:id |
| feature-flag-service | TBD | /api/v1/feature-flags | GET, PATCH |
| learning-analytics-service | TBD | /api/v1/analytics/learning | GET aggregates |
| skill-analytics-service | TBD | /api/v1/analytics/skills | GET |
| lti-service | TBD | /api/v1/lti | GET/POST config |

---

## Section 15: Frozen Screen States

Every screen must implement these standard states:

| State | When Required | Implementation |
|---|---|---|
| Loading | On initial data fetch | Skeleton UI (table rows, card placeholders) |
| Empty | When API returns empty items array | "No [resource] yet" message + CTA if applicable |
| Error | On API failure / 5xx | Per-widget error (dashboards); full-screen error (critical paths) |
| Unauthorized | On `"decision": "deny"` from authorize | Redirect to /403 |
| Success | On mutation success | Inline confirmation or redirect |

**Payment-specific states (checkout flow):**
- PENDING: spinner + "Payment processing…"
- PAID: success confirmation + enrollment trigger + redirect CTA
- FAILED: error message + retry CTA

---

## Section 16: Blocked Items (FGAP — Not in Initial Sprint)

| FGAP | Feature | What is Excluded | Workaround |
|---|---|---|---|
| FGAP-001 | Parent/Guardian Portal | All parent routes (/parent/*), parent dashboard, child progress view, child attendance, child fee view | Route /parent/* → 404. No parent nav item. |
| FGAP-002 | Adaptive Learning Path | Adaptive content sequencing widget on learner dashboard, adaptive lesson order in course player | Show static lesson order. No adaptive path indicator. |
| FGAP-003 | AI Copilot Overlay | Global floating AI copilot accessible from any screen | No copilot icon anywhere. AiTutorPanel in course player is the complete AI feature. |
| FGAP-004 | Risk Insights Dashboard | At-risk learner widget on DASH-001 and DASH-002 | Dashboards render without risk widget. No placeholder. |
| FGAP-005 | Reconciliation Admin Screen | /admin/reconciliation admin screen | Route returns 503/stub. No sidebar nav item. |
| FGAP-006 | PWA Offline Mode | Service worker, offline content cache, offline lesson player, sync-on-reconnect | Online-only build. No "Download for offline" button. No offline indicator. |

**Excluded nav items (do not add to any sidebar):**
- Parent portal navigation
- Adaptive learning path (standalone nav item)
- AI copilot overlay toggle
- Reconciliation admin (no sidebar link)
- Offline mode indicator / sync status
- Teacher marketplace (MO-043)
- Urdu i18n toggle (MO-041)
- Vocational training section (MO-042)
- Offline box management (MO-044)

---

## Section 17: Safe Defaults (Frontend-Relevant)

These safe defaults are in effect and affect frontend behavior:

| SD | Topic | Frontend Impact |
|---|---|---|
| OC-001 (PDC-001) | Checkout uses in-memory storage in dev | No frontend impact — checkout API contract unchanged |
| OC-003 (PDC-003) | Binary upload API is TBD | Content upload screen renders; upload action is stubbed; stub replaced in content sprint |
| OC-004 (PDC-007) | AI scope = ai-tutor + recommendations + course-generation; copilot is FGAP | AiTutorPanel on /learner/courses/:id/learn is in scope; global copilot is not |
| OC-005 (PDC-010) | Online-only Next.js in initial build | No service worker; no offline states |
| PDC-012 | Permission-based nav via authorize endpoint | All route guards call POST /api/v1/rbac/authorize; no role_key hardcoding |

---

## Section 18: Remaining Owner Confirmations (All Non-Blocking)

| Item | What is Needed | Blocking For |
|---|---|---|
| OR-001 (PM-OD-001) | JWT RS256 key pair generation | Production auth only; dev uses ephemeral key |
| OR-002 (PM-OD-002) | Owner approves capability-resolution.md update | Anchor doc only; no engineering impact |
| OR-003 (PM-OD-003) | Owner approves doc-precedence.md update | Anchor doc only; no engineering impact |

None of these block frontend implementation.

---

## Section 19: Commerce Context (Pakistan-First)

| Item | Value |
|---|---|
| Payment providers (initial build) | JazzCash (primary), EasyPaisa (secondary) |
| Currency | PKR |
| No international methods | Correct — not in current scope |
| Checkout idempotency | Client generates idempotency_key (UUID v4); passed in submit request |
| Payment status poll | GET /api/v1/checkout/orders/:id → PENDING / PAID / FAILED |
| Auto-enrollment | Order PAID → enrollment triggered server-side → redirect to course |

---

## Section 20: L0 GO/NO-GO Assessment

| Criterion | Status | Evidence |
|---|---|---|
| Any unresolved decision altering navigation? | PASS — No | POST_COLLAPSE_FRONTEND_READINESS.md gate assessment |
| Any unresolved decision altering menus? | PASS — No | POST_COLLAPSE_FRONTEND_READINESS.md |
| Any unresolved decision altering screens? | PASS — No | Binary upload stub is contained; PDC-003 |
| Any unresolved decision altering workflows? | PASS — No | POST_COLLAPSE_FRONTEND_READINESS.md |
| Any unresolved decision altering permissions? | PASS — No | FRONTEND_PERMISSION_MATRIX.md complete |
| Any unresolved decision altering user journeys? | PASS — No | All 3 role journeys determined |
| Any unresolved decision altering product scope? | PASS — No | DETERMINISM_CERTIFICATION_REPORT.md all domains DETERMINED |
| FGAP-001 blocking initial sprint? | PASS — Non-blocking | Parent portal deferred; Admin/Teacher/Learner complete |
| FGAP-002 blocking initial sprint? | PASS — Non-blocking | Additive widget only |
| FGAP-003 blocking initial sprint? | PASS — Non-blocking | Additive overlay; AiTutorPanel in scope |
| FGAP-004 blocking initial sprint? | PASS — Non-blocking | Additive widgets only |
| FGAP-005 blocking initial sprint? | PASS — Non-blocking | Placeholder route; no nav item |
| FGAP-006 blocking initial sprint? | PASS — Non-blocking | Additive PWA layer |
| BACKEND-TBD APIs blocking screen definition? | PASS — Non-blocking | Screens defined; stubs used until API sprint |
| Repository determinism certification? | PASS — FULLY DETERMINED | 8 domains all DETERMINED (DETERMINISM_CERTIFICATION_REPORT.md) |

---

## FINAL VERDICT

```
L0 FROZEN

Date: 2026-06-24
Phase: Phase 3.5
Scope: Admin + Teacher + Learner (initial sprint)

All inputs are locked. No invention permitted.
Design and implementation may begin.
```
