# L0 ROUTE–SCREEN–WORKFLOW MATRIX

Status: L0 FROZEN
Date: 2026-06-24
Phase: Phase 3.5 — L0 Frontend Authority Input Freeze
Owner: AI
Derived from: L0_FRONTEND_AUTHORITY_INPUT_FREEZE.md, FRONTEND_ROUTE_CATALOG.md, FRONTEND_SCREEN_CATALOG.md, FRONTEND_WORKFLOW_TO_SCREEN_MAP.md

---

## Purpose

This matrix is the single cross-reference for implementation and design. For every route, it states: which screen it renders, which workflow it supports, which permission gates it, which role typically accesses it, and which APIs it consumes. No new routes, screens, or workflows may be added without updating all upstream authority documents.

---

## Column Definitions

| Column | Definition |
|---|---|
| Route | Exact URL path as defined in FRONTEND_ROUTE_CATALOG.md |
| Screen ID | Screen catalog ID from FRONTEND_SCREEN_CATALOG.md |
| Workflow | Workflow(s) from FRONTEND_WORKFLOW_TO_SCREEN_MAP.md |
| Permission Key | Permission checked via POST /api/v1/rbac/authorize |
| Role Hint | Typical role — for reference only; authorization is permission-based |
| Primary API | Key API call(s) for the route |
| State | ACTIVE (build now) / STUB (blocked by FGAP) |

---

## Public Routes (No Auth)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/login` | SCR-001 | WF-001 (entry), FSC-001 | None | All | GET /api/v2/auth/tenant?domain=, POST /api/v2/auth/sessions/login | ACTIVE |
| `/signup` | — | WF-001 step 1 | None | New operator | POST /api/v1/tenants | ACTIVE |
| `/forgot-password` | SCR-002 | — | None | All | POST /api/v2/auth/password/forgot | ACTIVE |
| `/reset-password` | SCR-003 | — | None (token) | All | POST /api/v2/auth/password/reset | ACTIVE |
| `/sso/callback` | — | — | None | All | POST /api/v2/auth/sso/callback | ACTIVE |

---

## Admin Routes

### Dashboard

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/dashboard` | SCR-004, DASH-001 | WF-001 (post-onboard), WF-008 | `analytics.view` | Admin | GET /api/v1/tenants/:id/lifecycle, GET /api/v1/enrollments (agg), revenue-service (TBD) | ACTIVE |

### Organization & Tenancy

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/tenants` | — | — | `tenant.view_all` | Platform Admin | GET /api/v1/tenants | ACTIVE |
| `/admin/tenants/:tenant_id` | — | — | `tenant.view` | Admin | GET /api/v1/tenants/:id | ACTIVE |
| `/admin/tenants/:tenant_id/config` | — | WF-009 | `tenant.update` | Admin | PATCH /api/v1/tenants/:id/configuration | ACTIVE |
| `/admin/tenants/:tenant_id/lifecycle` | — | — | `tenant.manage_lifecycle` | Admin | POST /api/v1/tenants/:id/lifecycle/suspend | ACTIVE |
| `/admin/organizations` | — | — | `org.view` | Admin | org-service (TBD) | ACTIVE |
| `/admin/organizations/:id` | — | — | `org.view` | Admin | org-service (TBD) | ACTIVE |
| `/admin/departments` | — | — | `department.view` | Admin | department-service (TBD) | ACTIVE |
| `/admin/departments/:id` | — | — | `department.view` | Admin | department-service (TBD) | ACTIVE |
| `/admin/institutions` | — | — | `institution.view` | Admin | institution-service (TBD) | ACTIVE |
| `/admin/groups` | — | — | `group.view` | Admin | group-service (TBD) | ACTIVE |
| `/admin/cohorts` | — | — | `cohort.view` | Admin | cohort-service (TBD) | ACTIVE |

### People

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/users` | SCR-005 | — | `user.view` | Admin | user-service GET (TBD) | ACTIVE |
| `/admin/users/new` | — | — | `user.create` | Admin | user-service POST (TBD) | ACTIVE |
| `/admin/users/:user_id` | SCR-006 | — | `user.view` | Admin | user-service GET /:id (TBD), GET /api/v1/rbac/assignments | ACTIVE |
| `/admin/users/:user_id/roles` | SCR-006 (tab) | — | `user.view`, `permission.assign` | Admin | GET /api/v1/rbac/assignments, POST /api/v1/rbac/assignments | ACTIVE |
| `/admin/users/:user_id/reset-password` | SCR-006 (action) | — | `user.manage_credentials` | Admin | POST /api/v2/admin/users/:id/reset-password | ACTIVE |

### Access Control

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/roles` | SCR-007 | — | `role.view` | Admin | GET /api/v1/rbac/roles | ACTIVE |
| `/admin/roles/new` | — | — | `role.create` | Admin | POST /api/v1/rbac/roles | ACTIVE |
| `/admin/roles/:role_id` | SCR-008 | — | `role.view` | Admin | GET /api/v1/rbac/roles/:id, GET /api/v1/rbac/permissions | ACTIVE |
| `/admin/roles/:role_id/edit` | SCR-008 (edit) | — | `role.update` | Admin | PATCH /api/v1/rbac/roles/:id, PUT /api/v1/rbac/roles/:id/permissions | ACTIVE |
| `/admin/permissions` | — | — | `permission.view` | Admin | GET /api/v1/rbac/permissions | ACTIVE |
| `/admin/policy-rules` | SCR-027 | — | `role.manage_policy` | Admin | GET /api/v1/rbac/policy-rules | ACTIVE |
| `/admin/policy-rules/new` | SCR-027 (create) | — | `role.manage_policy` | Admin | POST /api/v1/rbac/policy-rules | ACTIVE |
| `/admin/audit-log` | SCR-009 | — | `audit.view_tenant` | Admin | GET /api/v1/rbac/audit-log | ACTIVE |

### Academy Operations (Pakistan)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/branches` | SCR-010 | WF-002 step 1 | `branch.view` | Admin | academy-commerce-service GET (TBD) | ACTIVE |
| `/admin/branches/new` | SCR-010 (create) | WF-002 step 1 | `branch.create` | Admin | academy-commerce-service POST (TBD) | ACTIVE |
| `/admin/branches/:branch_id` | SCR-010 (detail) | WF-002 step 1 | `branch.view` | Admin | academy-commerce-service GET (TBD) | ACTIVE |
| `/admin/batches` | SCR-011 | WF-002 step 2 | `batch.view` | Admin | academy-commerce-service GET (TBD) | ACTIVE |
| `/admin/batches/new` | SCR-011 (create) | WF-002 step 2 | `batch.create` | Admin | academy-commerce-service POST (TBD) | ACTIVE |
| `/admin/batches/:batch_id` | SCR-011 | WF-002 steps 2–5 | `batch.view` | Admin | academy-commerce-service (TBD) | ACTIVE |
| `/admin/batches/:batch_id/timetable` | SCR-012 | WF-002 step 4, WF-006 step 1 | `timetable.manage` | Admin | academy-commerce-service (TBD) | ACTIVE |
| `/admin/batches/:batch_id/students` | SCR-011 (tab) | WF-002 step 3 | `enrollment.view` | Admin | GET /api/v1/enrollments?cohort_id= | ACTIVE |
| `/admin/fee-structures` | — | WF-002 step 5, WF-006 | `fee.manage` | Admin | academy-commerce-service (TBD) | ACTIVE |

### Courses & Content (Admin)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/courses` | SCR-013 | — | `course.view` | Admin | course-service GET (TBD) | ACTIVE |
| `/admin/courses/new` | SCR-013 (create) | — | `course.create` | Admin | course-service POST (TBD), course-generation-service | ACTIVE |
| `/admin/courses/:course_id` | SCR-014 | — | `course.view` | Admin | course-service GET (TBD), enrollment-service | ACTIVE |
| `/admin/courses/:course_id/publish` | SCR-014 (action) | — | `course.publish` | Admin | course-service PATCH (TBD) | ACTIVE |
| `/admin/programs` | — | — | `program.view` | Admin | program-service (TBD) | ACTIVE |
| `/admin/learning-paths` | — | — | `learning_path.view` | Admin | learning-path-service (TBD) | ACTIVE |
| `/admin/content` | — | — | `content.view` | Admin | content-service (TBD), media-service | ACTIVE |
| `/admin/ai/course-generation` | — | — | `course.create`, `ai.use` | Admin | course-generation-service (TBD) | ACTIVE |
| `/admin/ai/settings` | — | — | `ai.configure` | Admin | ai-tutor-service config (TBD) | ACTIVE |

### Commerce & Billing (Admin)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/billing` | — | WF-006 | `billing.view` | Admin | invoice-billing-service (TBD) | ACTIVE |
| `/admin/billing/invoices` | — | WF-006 | `billing.view` | Admin | invoice-billing-service (TBD) | ACTIVE |
| `/admin/billing/invoices/:id` | — | WF-006 | `billing.view` | Admin | invoice-billing-service (TBD) | ACTIVE |
| `/admin/subscriptions` | — | — | `subscription.view` | Admin | subscription-service (TBD) | ACTIVE |
| `/admin/revenue` | — | WF-008 | `analytics.view_revenue` | Admin | revenue-service (TBD) | ACTIVE |
| `/admin/reconciliation` | — | — | `reconciliation.view` | Admin | **FGAP-005** | STUB — 503 |

### Analytics (Admin)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/analytics` | DASH-004 | — | `analytics.view` | Admin | learning-analytics-service (TBD), skill-analytics-service (TBD) | ACTIVE |
| `/admin/analytics/reports` | — | — | `report.view` | Admin | reporting-service (TBD) | ACTIVE |
| `/admin/analytics/skills` | — | — | `analytics.view` | Admin | skill-analytics-service (TBD) | ACTIVE |

### System (Admin)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/admin/integrations` | — | WF-010 | `integration.manage` | Admin | lti-service, hris-sync-service (TBD) | ACTIVE |
| `/admin/webhooks` | — | — | `webhook.manage` | Admin | webhook-service (TBD) | ACTIVE |
| `/admin/feature-flags` | — | WF-009 | `feature_flag.manage` | Admin | feature-flag-service (TBD) | ACTIVE |
| `/admin/notifications` | SCR-025 | WF-007 | `notification.manage` | Admin | notification-service (TBD) | ACTIVE |
| `/admin/settings` | — | WF-009 | `settings.manage` | Admin | PATCH /api/v1/tenants/:id/configuration | ACTIVE |
| `/admin/onboarding` | SCR-026 | WF-001 post-signup | `tenant.configure` | Admin (new) | onboarding-service (TBD), tenant-service | ACTIVE |

---

## Teacher Routes

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/teacher/dashboard` | SCR-022, DASH-002 | — | `course.view`, `batch.view` | Teacher | academy-commerce-service (TBD), assessment-service (TBD) | ACTIVE |
| `/teacher/courses` | SCR-014 (teacher view) | — | `course.view` | Teacher | course-service GET (TBD) | ACTIVE |
| `/teacher/courses/:id` | SCR-014 | — | `course.view` | Teacher | course-service GET (TBD) | ACTIVE |
| `/teacher/courses/:id/lessons` | — | — | `lesson.view` | Teacher | lesson-service GET (TBD) | ACTIVE |
| `/teacher/courses/:id/lessons/new` | — | — | `lesson.create` | Teacher | lesson-service POST (TBD) | ACTIVE |
| `/teacher/courses/:id/lessons/:lid` | — | — | `lesson.update` | Teacher | lesson-service PATCH (TBD) | ACTIVE |
| `/teacher/courses/:id/content` | SCR-015 | — | `content.upload` | Teacher | content-service POST (TBD), media-service POST (TBD) | ACTIVE (upload stub) |
| `/teacher/courses/:id/students` | — | WF-003 | `enrollment.view` | Teacher | GET /api/v1/enrollments?course_id= | ACTIVE |
| `/teacher/batches` | SCR-011 (teacher view) | — | `batch.view` | Teacher | academy-commerce-service GET (TBD) | ACTIVE |
| `/teacher/batches/:id` | SCR-011 (teacher view) | — | `batch.view` | Teacher | academy-commerce-service GET (TBD) | ACTIVE |
| `/teacher/batches/:id/timetable` | SCR-012 (view) | WF-006 step 1 | `timetable.view` | Teacher | academy-commerce-service GET (TBD) | ACTIVE |
| `/teacher/batches/:id/attendance` | SCR-023 | WF-002 | `attendance.mark` | Teacher | academy-commerce-service POST (TBD) | ACTIVE |
| `/teacher/batches/:id/grades` | — | — | `assessment.grade` | Teacher | assessment-service (TBD) | ACTIVE |
| `/teacher/assessments` | — | — | `assessment.view` | Teacher | assessment-service GET (TBD) | ACTIVE |
| `/teacher/assessments/new` | — | — | `assessment.create` | Teacher | assessment-service POST (TBD) | ACTIVE |
| `/teacher/assessments/:id` | — | — | `assessment.view` | Teacher | assessment-service GET (TBD) | ACTIVE |
| `/teacher/assessments/:id/grade` | SCR-024 | — | `assessment.grade` | Teacher | attempt-service GET (TBD), attempt-service PATCH (TBD) | ACTIVE |
| `/teacher/notifications` | SCR-025 | WF-007 | `notification.view` | Teacher | notification-service GET (TBD) | ACTIVE |

---

## Learner Routes

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/learner/dashboard` | SCR-016, DASH-003 | WF-004 start | `course.view`, `progress.view` | Learner | GET /api/v1/enrollments?learner_id=, GET /api/v1/progress/learners/:id, recommendation-service (TBD) | ACTIVE |
| `/learner/courses` | SCR-017 | WF-003 | `course.view` | Learner | course-service GET (TBD), GET /api/v1/enrollments?learner_id= | ACTIVE |
| `/learner/courses/:id` | SCR-017 (detail) | WF-003 steps 3–5 | `course.view` | Learner | course-service GET, enrollment-service | ACTIVE |
| `/learner/courses/:id/learn` | SCR-018 | WF-004 steps 1–2 | `course.view`, `progress.update` | Learner | lesson-service (TBD), progress-service | ACTIVE |
| `/learner/courses/:id/learn/:lid` | SCR-018 (lesson) | WF-004 steps 1–3 | `lesson.view`, `progress.update` | Learner | lesson-service GET (TBD), content-service GET (TBD), POST /api/v1/progress/lessons/:id/upsert, ai-tutor-service (TBD) | ACTIVE |
| `/learner/courses/:id/assessments` | SCR-020 (list) | WF-004 step 4 | `attempt.view` | Learner | assessment-service (TBD), attempt-service (TBD) | ACTIVE |
| `/learner/progress` | — | WF-004 | `progress.view` | Learner | GET /api/v1/progress/learners/:id | ACTIVE |
| `/learner/learning-paths` | — | — | `learning_path.view` | Learner | learning-path-service (TBD) | ACTIVE |
| `/learner/programs` | — | — | `program.view` | Learner | program-service (TBD) | ACTIVE |
| `/learner/assessments` | — | WF-004 step 4 | `attempt.view` | Learner | assessment-service (TBD) | ACTIVE |
| `/learner/assessments/:id` | SCR-020 | WF-004 steps 4–6 | `attempt.create` | Learner | assessment-service GET (TBD), attempt-service POST (TBD) | ACTIVE |
| `/learner/certificates` | — | WF-004 step 7 | `certificate.view` | Learner | certificate-service GET (TBD) | ACTIVE |
| `/learner/certificates/:id` | SCR-021 | WF-004 step 7 | `certificate.view` | Learner | certificate-service GET /:id (TBD) | ACTIVE |
| `/learner/badges` | — | WF-004 step 8 | `badge.view` | Learner | badge-service GET (TBD) | ACTIVE |
| `/learner/payments` | — | WF-006 | `payment.view` | Learner | GET /api/v1/checkout/orders (TBD filter) | ACTIVE |
| `/learner/checkout` | SCR-019 | WF-005, WF-003 Path B | `checkout.create` | Learner | POST /api/v1/checkout/sessions, /items, /submit, /initiate-payment | ACTIVE |
| `/learner/orders/:id` | SCR-019 (order status) | WF-005 steps 5–6 | `payment.view` | Learner | GET /api/v1/checkout/orders/:id | ACTIVE |
| `/learner/notifications` | SCR-025 | WF-007 | `notification.view` | Learner | notification-service GET (TBD) | ACTIVE |

---

## Shared Routes (All Authenticated Roles)

| Route | Screen ID | Workflow | Permission | Role Hint | Primary API | State |
|---|---|---|---|---|---|---|
| `/profile` | — | — | Authenticated | All | user-service GET/PATCH (TBD) | ACTIVE |
| `/notifications` | SCR-025 | WF-007 | `notification.view` | All | notification-service GET (TBD) | ACTIVE |
| `/403` | — | — | None | — | — | ACTIVE |
| `/404` | — | — | None | — | — | ACTIVE |
| `/500` | — | — | None | — | — | ACTIVE |

---

## Workflow Summary

| Workflow | Screens | Routes | Role | API Path |
|---|---|---|---|---|
| WF-001: Tenant Onboarding | SCR-001 (login), SCR-026 (wizard) | /signup, /admin/onboarding | Admin | POST /api/v1/tenants, onboarding-service (TBD) |
| WF-002: Academy Setup | SCR-010, SCR-011, SCR-012 | /admin/branches/new, /admin/batches/new, /admin/batches/:id, /admin/fee-structures | Admin | academy-commerce-service (TBD) |
| WF-003: Student Enrollment | SCR-017, SCR-019 | /learner/courses/:id, /learner/checkout, /learner/orders/:id | Learner | POST /api/v1/enrollments, POST /api/v1/checkout/sessions |
| WF-004: Learning & Completion | SCR-018, SCR-020, SCR-021 | /learner/courses/:id/learn/:lid, /learner/assessments/:id, /learner/certificates/:id | Learner | progress-service, attempt-service, certificate-service |
| WF-005: Commerce Checkout | SCR-019 | /learner/checkout, /learner/orders/:id | Learner | POST /api/v1/checkout/* → GET /api/v1/checkout/orders/:id |
| WF-006: Fee Tracking | — | /admin/billing, /admin/revenue | Admin | invoice-billing-service (TBD), revenue-service (TBD) |
| WF-007: Notification Dispatch | SCR-025 | /notifications, /admin/notifications | All | notification-service GET (TBD) |
| WF-008: Revenue Anomaly | DASH-001, SCR-004 | /admin/dashboard, /admin/revenue | Admin | revenue-service (TBD) |
| WF-009: Config & Entitlement | — | /admin/settings, /admin/feature-flags | Admin | PATCH /api/v1/tenants/:id/configuration, feature-flag-service |
| WF-010: LTI Integration | SCR-018 (SCORM) | /lti/launch (TBD), /learner/courses/:id/learn/:lid | Admin (config), Learner (consume) | lti-service (TBD), scorm-service |

---

## STUB Routes (FGAP-blocked)

| Route | Blocked By | Behavior |
|---|---|---|
| `/parent/*` | FGAP-001 | 404 — no parent routes in initial build |
| `/admin/reconciliation` | FGAP-005 | 503 stub or "Coming soon" — no nav item |

---

## Route Count Summary

| Scope | Count | Status |
|---|---|---|
| Public | 5 | ACTIVE |
| Admin | ~46 | ACTIVE (1 stub: /admin/reconciliation) |
| Teacher | 18 | ACTIVE |
| Learner | 22 | ACTIVE |
| Shared | 4 | ACTIVE |
| **Total** | **~95** | **All accounted for** |
| Parent portal | 0 | DEFERRED — FGAP-001 |
