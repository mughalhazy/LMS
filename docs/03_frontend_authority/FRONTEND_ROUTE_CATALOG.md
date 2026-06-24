# FRONTEND ROUTE CATALOG

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- API_CONTRACT.md — all confirmed API endpoints
- USER_ROLES_AND_PERMISSIONS.md — role and scope model
- FEATURE_SCOPE.md — feature boundaries
- PRODUCT_WORKFLOWS.md — workflows driving screens
- FRONTEND_NAVIGATION_MODEL.md — navigation structure

---

## Legend

- **Permission Key**: the `permission_key` value sent to `POST /api/v1/rbac/authorize`
- **Role Hint**: which role typically holds this permission (hint only — permission-based authorization is canonical)
- **API**: primary backend API(s) consumed by the route
- **Blocking Condition**: conditions that redirect the user before rendering

---

## Public Routes

| Route | Purpose | Permission | API | Blocking Condition |
|---|---|---|---|---|
| `/login` | Email/password login form | None (public) | POST /api/v2/auth/sessions/login, GET /api/v2/auth/tenant?domain= | Already authenticated → redirect to role dashboard |
| `/signup` | New tenant registration | None (public) | POST /api/v1/tenants (+ Idempotency-Key) | Already authenticated → redirect |
| `/forgot-password` | Request password reset | None (public) | POST /api/v2/auth/password/forgot | — |
| `/reset-password` | Complete password reset | None (public) | POST /api/v2/auth/password/reset | Token expired → error state |
| `/sso/callback` | SSO assertion exchange | None (public) | POST /api/v2/auth/sso/callback | Provider error → error state |

---

## Admin Routes

All admin routes require authenticated user with an active admin-scope role assignment.

### Dashboard

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/dashboard` | Tenant overview: enrollments, revenue, users | `analytics.view` | GET /api/v1/progress (summary), revenue-service, enrollment-service | auth required |

---

### Organization & Tenancy

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/tenants` | Platform tenant list (platform admin only) | `tenant.view_all` | GET /api/v1/tenants | Platform-admin only |
| `/admin/tenants/:tenant_id` | Tenant detail, lifecycle, config | `tenant.view` | GET /api/v1/tenants/:id, GET /api/v1/tenants/:id/configuration | — |
| `/admin/tenants/:tenant_id/config` | Tenant configuration edit | `tenant.update` | PATCH /api/v1/tenants/:id/configuration | — |
| `/admin/tenants/:tenant_id/lifecycle` | Suspend/reactivate/archive | `tenant.manage_lifecycle` | POST /api/v1/tenants/:id/lifecycle/suspend etc | — |
| `/admin/organizations` | Organization hierarchy | `org.view` | org-service (TBD) | — |
| `/admin/organizations/:id` | Org unit detail | `org.view` | org-service (TBD) | — |
| `/admin/departments` | Department list | `department.view` | department-service (TBD) | — |
| `/admin/departments/:id` | Department detail | `department.view` | department-service (TBD) | — |
| `/admin/institutions` | Institution list | `institution.view` | institution-service (TBD) | — |
| `/admin/groups` | Group management | `group.view` | group-service (TBD) | — |
| `/admin/cohorts` | Cohort management | `cohort.view` | cohort-service (TBD) | — |

---

### People

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/users` | User list (filterable by role, status) | `user.view` | user-service GET /api/v1/users (TBD) | — |
| `/admin/users/new` | Create user | `user.create` | POST /api/v1/users (TBD) | — |
| `/admin/users/:user_id` | User profile, metadata | `user.view` | GET /api/v1/users/:id (TBD) | — |
| `/admin/users/:user_id/roles` | User role assignments | `user.view`, `permission.assign` | GET /api/v1/rbac/assignments?subject_id=, POST /api/v1/rbac/assignments | — |
| `/admin/users/:user_id/reset-password` | Admin password reset | `user.manage_credentials` | POST /api/v2/admin/users/:id/reset-password | — |

---

### Access Control

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/roles` | Role list | `role.view` | GET /api/v1/rbac/roles | — |
| `/admin/roles/new` | Create custom role | `role.create` | POST /api/v1/rbac/roles | — |
| `/admin/roles/:role_id` | Role detail, permission bindings | `role.view` | GET /api/v1/rbac/roles/:id, GET /api/v1/rbac/permissions | — |
| `/admin/roles/:role_id/edit` | Edit role | `role.update` | PATCH /api/v1/rbac/roles/:id, PUT /api/v1/rbac/roles/:id/permissions | — |
| `/admin/permissions` | Permission catalog (read-only) | `permission.view` | GET /api/v1/rbac/permissions | — |
| `/admin/policy-rules` | Policy rules list | `role.manage_policy` | GET /api/v1/rbac/policy-rules | — |
| `/admin/policy-rules/new` | Create policy rule | `role.manage_policy` | POST /api/v1/rbac/policy-rules | — |
| `/admin/audit-log` | RBAC authorization audit log | `audit.view_tenant` | GET /api/v1/rbac/audit-log | Deny if no audit permission |

---

### Academy Operations (Pakistan)

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/branches` | Branch list | `branch.view` | academy-commerce-service (TBD) | — |
| `/admin/branches/new` | Create branch | `branch.create` | academy-commerce-service POST (TBD) | — |
| `/admin/branches/:branch_id` | Branch detail, teachers | `branch.view` | academy-commerce-service GET (TBD) | — |
| `/admin/batches` | Batch list | `batch.view` | academy-commerce-service (TBD) | — |
| `/admin/batches/new` | Create batch, assign to branch | `batch.create` | academy-commerce-service POST (TBD) | — |
| `/admin/batches/:batch_id` | Batch detail | `batch.view` | academy-commerce-service (TBD) | — |
| `/admin/batches/:batch_id/timetable` | Timetable management | `timetable.manage` | academy-commerce-service (TBD) | — |
| `/admin/batches/:batch_id/students` | Student roster | `enrollment.view` | GET /api/v1/enrollments?cohort_id= | — |
| `/admin/fee-structures` | Fee structure config | `fee.manage` | academy-commerce-service (TBD) | — |

---

### Courses & Content

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/courses` | Course catalog management | `course.view` | course-service GET (TBD) | — |
| `/admin/courses/new` | Create course (+ AI option) | `course.create` | course-service POST (TBD), course-generation-service | — |
| `/admin/courses/:course_id` | Course detail, status | `course.view` | course-service GET (TBD) | — |
| `/admin/courses/:course_id/publish` | Publish/unpublish | `course.publish` | course-service PATCH (TBD) | — |
| `/admin/programs` | Program management | `program.view` | program-service (TBD) | — |
| `/admin/learning-paths` | Learning path management | `learning_path.view` | learning-path-service (TBD) | — |
| `/admin/content` | Content library | `content.view` | content-service (TBD), media-service | — |
| `/admin/ai/course-generation` | AI-assisted course creation | `course.create`, `ai.use` | course-generation-service (TBD) | — |
| `/admin/ai/settings` | AI service configuration | `ai.configure` | ai-tutor-service, recommendation-service config (TBD) | — |

---

### Commerce & Billing

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/billing` | Invoice and billing overview | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/billing/invoices` | Invoice list | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/billing/invoices/:id` | Invoice detail | `billing.view` | invoice-billing-service (TBD) | — |
| `/admin/subscriptions` | Subscription management | `subscription.view` | subscription-service (TBD) | — |
| `/admin/revenue` | Revenue analytics | `analytics.view_revenue` | revenue-service (TBD) | — |
| `/admin/reconciliation` | Reconciliation admin | `reconciliation.view` | **FGAP-005** — not built | 503 or stub state |

---

### Analytics

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/analytics` | Learning analytics dashboard | `analytics.view` | learning-analytics-service (TBD) | — |
| `/admin/analytics/reports` | Report list, report builder | `report.view` | reporting-service (TBD) | — |
| `/admin/analytics/skills` | Skill analytics | `analytics.view` | skill-analytics-service (TBD) | — |

---

### System

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/admin/integrations` | LTI, HRIS, webhook integration mgmt | `integration.manage` | lti-service, hris-sync-service, integration-service (TBD) | — |
| `/admin/webhooks` | Webhook configuration | `webhook.manage` | webhook-service (TBD) | — |
| `/admin/feature-flags` | Feature flag toggle | `feature_flag.manage` | feature-flag-service (TBD) | — |
| `/admin/notifications` | Notification dispatch center | `notification.manage` | notification-service (TBD) | — |
| `/admin/settings` | Platform settings | `settings.manage` | tenant-service PATCH /api/v1/tenants/:id/configuration | — |
| `/admin/onboarding` | Tenant onboarding wizard | `tenant.configure` | onboarding-service (TBD), tenant-service | — |

---

## Teacher Routes

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/teacher/dashboard` | My batches, attendance stats, upcoming assessments | `course.view`, `batch.view` | academy-commerce-service, assessment-service (TBD) | — |
| `/teacher/courses` | My assigned courses | `course.view` | course-service (TBD) | — |
| `/teacher/courses/:id` | Course overview | `course.view` | course-service GET (TBD) | — |
| `/teacher/courses/:id/lessons` | Lesson list | `lesson.view` | lesson-service (TBD) | — |
| `/teacher/courses/:id/lessons/new` | Create lesson | `lesson.create` | lesson-service POST (TBD) | — |
| `/teacher/courses/:id/lessons/:lid` | Lesson editor | `lesson.update` | lesson-service PATCH (TBD) | — |
| `/teacher/courses/:id/content` | Content upload and management | `content.upload` | content-service POST (TBD), media-service POST (TBD) | Binary upload stub until content sprint |
| `/teacher/courses/:id/students` | Enrolled student list | `enrollment.view` | GET /api/v1/enrollments?course_id= | — |
| `/teacher/batches` | My batches | `batch.view` | academy-commerce-service (TBD) | — |
| `/teacher/batches/:id` | Batch detail | `batch.view` | academy-commerce-service (TBD) | — |
| `/teacher/batches/:id/timetable` | Timetable view | `timetable.view` | academy-commerce-service (TBD) | — |
| `/teacher/batches/:id/attendance` | Mark attendance | `attendance.mark` | academy-commerce-service (TBD) | — |
| `/teacher/batches/:id/grades` | Enter grades | `assessment.grade` | assessment-service (TBD) | — |
| `/teacher/assessments` | My assessments | `assessment.view` | assessment-service GET (TBD) | — |
| `/teacher/assessments/new` | Create assessment | `assessment.create` | assessment-service POST (TBD) | — |
| `/teacher/assessments/:id` | Assessment detail, submissions | `assessment.view` | assessment-service GET (TBD) | — |
| `/teacher/assessments/:id/grade` | Grade submissions | `assessment.grade` | attempt-service (TBD) | — |
| `/teacher/notifications` | Notification inbox | `notification.view` | notification-service (TBD) | — |

---

## Learner Routes

| Route | Purpose | Permission Key | API | Blocking |
|---|---|---|---|---|
| `/learner/dashboard` | My courses, progress, recommendations | `course.view`, `progress.view` | enrollment-service, progress-service, recommendation-service (TBD) | — |
| `/learner/courses` | Course catalog (browse + enrolled) | `course.view` | course-service GET (TBD), enrollment-service | — |
| `/learner/courses/:id` | Course overview, enroll CTA | `course.view` | course-service GET, enrollment-service | — |
| `/learner/courses/:id/learn` | Course player | `course.view`, `progress.update` | lesson-service, progress-service, ai-tutor-service (TBD) | Must be enrolled |
| `/learner/courses/:id/learn/:lid` | Lesson player (video/SCORM/text + AI panel) | `lesson.view`, `progress.update` | lesson-service, content-service, POST /api/v1/progress/lessons/:id/upsert, ai-tutor-service | Must be enrolled |
| `/learner/courses/:id/assessments` | My assessments for this course | `attempt.view` | assessment-service, attempt-service (TBD) | — |
| `/learner/progress` | Overall progress summary | `progress.view` | GET /api/v1/progress/learners/:id | — |
| `/learner/learning-paths` | My learning paths | `learning_path.view` | learning-path-service (TBD) | — |
| `/learner/programs` | My programs | `program.view` | program-service (TBD) | — |
| `/learner/assessments` | All my assessments (upcoming + completed) | `attempt.view` | assessment-service, attempt-service (TBD) | — |
| `/learner/assessments/:id` | Assessment player (quiz or exam) | `attempt.create` | attempt-service POST (TBD), quiz-engine or exam-engine | — |
| `/learner/certificates` | My certificates | `certificate.view` | certificate-service (TBD) | — |
| `/learner/certificates/:id` | Certificate view + download link | `certificate.view` | certificate-service (TBD) | — |
| `/learner/badges` | My earned badges | `badge.view` | badge-service (TBD) | — |
| `/learner/payments` | Payment history | `payment.view` | GET /api/v1/checkout/orders (TBD filter by learner_id) | — |
| `/learner/checkout` | Checkout flow (multi-step) | `checkout.create` | POST /api/v1/checkout/sessions, /items, /submit, /initiate-payment | — |
| `/learner/orders/:id` | Order status and detail | `payment.view` | GET /api/v1/checkout/orders/:id | — |
| `/learner/notifications` | Notification inbox | `notification.view` | notification-service (TBD) | — |

---

## Shared Routes

| Route | Purpose | Auth Required | Notes |
|---|---|---|---|
| `/profile` | User profile (name, email, avatar, password change) | Yes | POST /api/v2/auth/password/forgot for reset |
| `/403` | Access denied | No | Shown on `"decision": "deny"` from authorize endpoint |
| `/404` | Not found | No | — |
| `/500` | Server error | No | — |

---

## Route Count Summary

| Scope | Routes |
|---|---|
| Public | 5 |
| Admin | ~46 |
| Teacher | 18 |
| Learner | 22 |
| Shared | 4 |
| **Total** | **~95** |

---

## API TBD Tracker

Routes where the primary API path is TBD (not yet verified in code inspection):

| Service | TBD Routes | Priority |
|---|---|---|
| course-service | All course routes (admin + teacher + learner) | HIGH |
| lesson-service | All lesson routes | HIGH |
| content-service | All content upload routes | HIGH |
| academy-commerce-service | All academy ops routes | HIGH |
| user-service | All user management routes | HIGH |
| notification-service | All notification routes | MEDIUM |
| certificate-service | All certificate routes | MEDIUM |
| assessment-service | All assessment routes | MEDIUM |
| invoice-billing-service | All billing routes | MEDIUM |
| ai-tutor-service | Tutor panel API | MEDIUM |
| recommendation-service | Recommendations widget | MEDIUM |

TBD items require Node.js inspection sessions and API discovery for the uninspected Python services (GAP-012 reclassified; now a sprint task).
