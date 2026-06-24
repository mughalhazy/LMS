# FRONTEND SCREEN CATALOG

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- PRODUCT_WORKFLOWS.md (WF-001 through WF-010)
- FEATURE_SCOPE.md
- FULLSTACK_STITCHING_CONTRACT.md (FSC-001 through FSC-009)
- AUTH_AND_TENANCY_CONTRACT.md
- API_CONTRACT.md
- FRONTEND_NAVIGATION_MODEL.md

---

## Screen Template

Each screen documents:
- Purpose
- Primary users
- Required permissions
- API dependencies
- Workflows supported
- Actions available
- Navigation entry points
- Related screens
- Error states
- Empty states
- Loading states
- Success states

---

## SCR-001: Login Screen

| Field | Value |
|---|---|
| **Route** | `/login` |
| **Purpose** | Authenticate user and establish session |
| **Primary users** | All users (admin, teacher, learner) |
| **Required permissions** | None (public) |
| **API dependencies** | `GET /api/v2/auth/tenant?domain=<email>` (tenant discovery before submit), `POST /api/v2/auth/sessions/login` |
| **Workflow** | WF-001 step 2 (auth user created); FSC-001 |
| **Actions** | Submit login form; navigate to SSO; navigate to forgot-password |
| **Navigation entry** | Root redirect; any 401; logout redirect |
| **Related screens** | SCR-002 (Forgot Password), SCR-003 (SSO Callback), each role dashboard |
| **Error states** | Invalid credentials (400); account locked; tenant not found |
| **Empty states** | N/A |
| **Loading state** | Submit spinner; tenant discovery spinner |
| **Success state** | Redirect to role dashboard based on RBAC assignments |

**CRITICAL**: After login, store `response.user.user_id` and `response.user.tenant_id`. The JWT `sub` claim is `session_id` — NOT user_id. Fetch roles separately via `GET /api/v1/rbac/assignments?subject_id=<user_id>&tenant_id=<tenant_id>`.

---

## SCR-002: Forgot Password Screen

| Field | Value |
|---|---|
| **Route** | `/forgot-password` |
| **Purpose** | Initiate password reset flow |
| **Primary users** | All users |
| **Required permissions** | None (public) |
| **API dependencies** | `POST /api/v2/auth/password/forgot` |
| **Actions** | Submit email; navigate back to login |
| **Error states** | Email not found (show generic "if account exists" message for security) |
| **Success state** | "Reset email sent" confirmation |

---

## SCR-003: Reset Password Screen

| Field | Value |
|---|---|
| **Route** | `/reset-password?token=<token>` |
| **Purpose** | Complete password reset with token |
| **Primary users** | All users |
| **Required permissions** | None (token-authenticated) |
| **API dependencies** | `POST /api/v2/auth/password/reset` |
| **Actions** | Submit new password |
| **Error states** | Token expired (max attempts exceeded — 5 attempts per challenge); token invalid |
| **Validation** | Minimum 8 chars, 1 uppercase, 1 digit (per PASSWORD_POLICY in auth-service) |
| **Success state** | "Password updated — redirect to login" |

---

## SCR-004: Admin Dashboard

| Field | Value |
|---|---|
| **Route** | `/admin/dashboard` |
| **Purpose** | Tenant-wide overview: enrollments, revenue, user count, notifications |
| **Primary users** | Admin |
| **Required permissions** | `analytics.view` |
| **API dependencies** | enrollment-service (stats), revenue-service (revenue summary), user-service (count), learning-analytics-service (overview) |
| **Workflow** | WF-001 (post-onboarding state), WF-008 (revenue anomaly signals) |
| **Actions** | Navigate to sub-sections; view alerts |
| **Dashboard widgets** | See FRONTEND_DASHBOARD_CATALOG.md — DASH-001 |
| **Error states** | Service unavailable (show widget error states individually) |
| **Empty states** | "No data yet" per widget (new tenant) |

---

## SCR-005: User Management Screen

| Field | Value |
|---|---|
| **Route** | `/admin/users` |
| **Purpose** | List, search, filter users; create new users |
| **Primary users** | Admin |
| **Required permissions** | `user.view` |
| **API dependencies** | user-service GET /api/v1/users (TBD) |
| **Actions** | Search users; filter by role/status; navigate to user detail; create user |
| **Empty state** | "No users found" |
| **Loading state** | Table skeleton |
| **Error state** | Service unavailable |

---

## SCR-006: User Detail Screen

| Field | Value |
|---|---|
| **Route** | `/admin/users/:user_id` |
| **Purpose** | View user profile, manage role assignments |
| **Primary users** | Admin |
| **Required permissions** | `user.view`; `permission.assign` for role management tab |
| **API dependencies** | user-service GET /:id (TBD); `GET /api/v1/rbac/assignments?subject_id=<user_id>&tenant_id=`; `POST /api/v1/rbac/assignments`; `DELETE /api/v1/rbac/assignments/:id` |
| **Actions** | View profile; add role assignment; revoke assignment; reset password; deactivate user |
| **Related screens** | SCR-005 (User list), SCR-018 (Role management) |

---

## SCR-007: Role Management Screen

| Field | Value |
|---|---|
| **Route** | `/admin/roles` |
| **Purpose** | List all roles; create custom roles |
| **Primary users** | Admin |
| **Required permissions** | `role.view` |
| **API dependencies** | `GET /api/v1/rbac/roles`; `GET /api/v1/rbac/permissions` |
| **Actions** | View role list; create role; navigate to role detail |

---

## SCR-008: Role Detail Screen

| Field | Value |
|---|---|
| **Route** | `/admin/roles/:role_id` |
| **Purpose** | View/edit role, manage permission bindings |
| **Primary users** | Admin |
| **Required permissions** | `role.view`; `role.update` for editing |
| **API dependencies** | `GET /api/v1/rbac/roles/:id`; `GET /api/v1/rbac/permissions`; `PUT /api/v1/rbac/roles/:id/permissions`; `PATCH /api/v1/rbac/roles/:id` |
| **Actions** | Edit display name; add/remove permissions; soft-delete role (system roles cannot be deleted) |
| **Constraint** | System roles (`is_system=true`) — no delete button |

---

## SCR-009: RBAC Audit Log Screen

| Field | Value |
|---|---|
| **Route** | `/admin/audit-log` |
| **Purpose** | View all authorization decisions logged by rbac-service |
| **Primary users** | Admin |
| **Required permissions** | `audit.view_tenant` (enforced server-side — also enforced client-side before rendering) |
| **API dependencies** | `GET /api/v1/rbac/audit-log` |
| **Actions** | Filter by date, user, decision, permission_key; export |
| **Error state** | 403 if `audit.view_tenant` not held |

---

## SCR-010: Branch Management Screen

| Field | Value |
|---|---|
| **Route** | `/admin/branches` |
| **Purpose** | List and manage academy branches (Pakistan) |
| **Primary users** | Admin |
| **Required permissions** | `branch.view` |
| **API dependencies** | academy-commerce-service (TBD) |
| **Workflow** | WF-002 step 1 |
| **Actions** | Create branch; view branch; assign teachers to branch |

---

## SCR-011: Batch Management Screen

| Field | Value |
|---|---|
| **Route** | `/admin/batches/:id` |
| **Purpose** | Manage batch: students, timetable, fee structure, teacher assignments |
| **Primary users** | Admin |
| **Required permissions** | `batch.view`; specific permissions per tab |
| **API dependencies** | academy-commerce-service (TBD); `GET /api/v1/enrollments?cohort_id=` |
| **Workflow** | WF-002 steps 2–5 |
| **Actions** | Add student; assign teacher; build timetable; set fee structure |
| **Sub-screens** | Timetable tab (SCR-012); Attendance tab (SCR-026); Students tab |

---

## SCR-012: Timetable Screen

| Field | Value |
|---|---|
| **Route** | `/admin/batches/:id/timetable` and `/teacher/batches/:id/timetable` |
| **Purpose** | View and manage class timetable; conflict detection |
| **Primary users** | Admin (manage), Teacher (view) |
| **Required permissions** | `timetable.manage` (admin), `timetable.view` (teacher) |
| **API dependencies** | academy-commerce-service (TBD) |
| **Workflow** | WF-002 step 4; WF-006 step 1 |
| **Actions (admin)** | Add slot; remove slot; resolve conflicts |
| **Actions (teacher)** | View only |
| **Constraint** | AcademyOpsService conflict detection runs server-side on slot creation |

---

## SCR-013: Course Management Screen (Admin)

| Field | Value |
|---|---|
| **Route** | `/admin/courses` |
| **Purpose** | Course catalog management: create, publish, manage content |
| **Primary users** | Admin |
| **Required permissions** | `course.view` |
| **API dependencies** | course-service GET (TBD) |
| **Actions** | Create course; filter/search; publish; navigate to detail |

---

## SCR-014: Course Detail Screen (Admin/Teacher)

| Field | Value |
|---|---|
| **Route** | `/admin/courses/:id` and `/teacher/courses/:id` |
| **Purpose** | View course metadata, lessons, content, enrolled students |
| **Primary users** | Admin, Teacher |
| **Required permissions** | `course.view` |
| **API dependencies** | course-service GET /:id (TBD), lesson-service GET (TBD), enrollment-service GET ?course_id= |
| **Actions** | Edit metadata (admin); publish/unpublish (admin); add lesson; add content; view students |
| **Sub-screens** | Lesson list; Content library; Student list |

---

## SCR-015: Content Upload Screen

| Field | Value |
|---|---|
| **Route** | `/teacher/courses/:id/content` |
| **Purpose** | Upload course content: video, documents, SCORM packages |
| **Primary users** | Teacher, Admin |
| **Required permissions** | `content.upload` |
| **API dependencies** | content-service POST (metadata — TBD); media-service POST (binary upload — TBD) |
| **Actions** | Select file; upload; assign to lesson; delete |
| **STUB NOTE** | Binary upload API target is TBD pending content sprint. Form renders with upload action stub. Metadata registration to content-service is confirmed. |
| **Error states** | Upload failed; file too large; unsupported format |
| **Success state** | Content appears in lesson content list |

---

## SCR-016: Learner Dashboard

| Field | Value |
|---|---|
| **Route** | `/learner/dashboard` |
| **Purpose** | Learner home: enrolled courses, progress summary, AI recommendations, upcoming assessments |
| **Primary users** | Learner |
| **Required permissions** | `course.view`, `progress.view` |
| **API dependencies** | `GET /api/v1/enrollments?learner_id=`, `GET /api/v1/progress/learners/:id`, recommendation-service (TBD) |
| **Workflow** | WF-004 starting point |
| **Dashboard widgets** | See FRONTEND_DASHBOARD_CATALOG.md — DASH-003 |

---

## SCR-017: Course Catalog Screen (Learner)

| Field | Value |
|---|---|
| **Route** | `/learner/courses` |
| **Purpose** | Browse available courses; view enrolled courses |
| **Primary users** | Learner |
| **Required permissions** | `course.view` |
| **API dependencies** | course-service GET (TBD), `GET /api/v1/enrollments?learner_id=` |
| **Actions** | Browse catalog; filter by topic/level; enroll; view progress on enrolled courses |
| **Empty states** | "No courses available yet" (new tenant) |

---

## SCR-018: Course Player Screen (Learner)

| Field | Value |
|---|---|
| **Route** | `/learner/courses/:id/learn/:lesson_id` |
| **Purpose** | Consume lesson content with progress tracking and AI tutor panel |
| **Primary users** | Learner |
| **Required permissions** | `lesson.view`, `progress.update` |
| **API dependencies** | lesson-service GET /:id (TBD), content-service GET (TBD), `POST /api/v1/progress/lessons/:lesson_id/upsert`, `POST /api/v1/progress/lessons/:lesson_id/complete`, ai-tutor-service (TBD) |
| **Workflow** | WF-004 steps 1–2 |
| **Actions** | Play video; complete lesson; send AI tutor message; navigate to next lesson |
| **Blocking condition** | Must be enrolled in parent course (`GET /api/v1/enrollments?learner_id=&course_id=` must return active enrollment) |
| **Components** | Video player or SCORM iframe; progress tracker; AI Tutor Chat Panel; lesson navigation |
| **AI Tutor Panel** | Confirms from PDC-007: per-lesson text chat with ai-tutor-service. Scope: tutor only (not full copilot) |
| **Error states** | Content not found; enrollment check failed |
| **Loading state** | Content skeleton; tutor panel loading |
| **Success state** | Lesson marked complete; progress bar updated |

---

## SCR-019: Checkout Flow Screen

| Field | Value |
|---|---|
| **Route** | `/learner/checkout` |
| **Purpose** | Multi-step payment flow: create session → add items → submit → initiate payment |
| **Primary users** | Learner |
| **Required permissions** | `checkout.create` |
| **API dependencies** | `POST /api/v1/checkout/sessions`, `POST /api/v1/checkout/sessions/:id/items`, `POST /api/v1/checkout/sessions/:id/submit`, `POST /api/v1/checkout/orders/:id/initiate-payment`, `GET /api/v1/checkout/orders/:id` (poll) |
| **Workflow** | WF-005 |
| **Actions** | Add item to cart; submit; pay via JazzCash/EasyPaisa; poll for confirmation |
| **Payment states** | PENDING (spinner + "Payment processing…"), PAID (success screen), FAILED (retry CTA) |
| **Idempotency** | Client generates idempotency_key; passed in submit request |
| **Error states** | Payment failed; session expired; product not found |
| **Success state** | Order PAID → enrollment triggered → redirect to course |

---

## SCR-020: Assessment Player Screen (Learner)

| Field | Value |
|---|---|
| **Route** | `/learner/assessments/:assessment_id` |
| **Purpose** | Take quiz or exam |
| **Primary users** | Learner |
| **Required permissions** | `attempt.create` |
| **API dependencies** | assessment-service GET /:id (TBD), attempt-service POST (TBD), quiz-engine or exam-engine |
| **Workflow** | WF-004 steps 3–5 |
| **Actions** | Answer questions; submit attempt |
| **Error states** | Time limit exceeded; attempt limit reached |
| **Success state** | Score displayed; if passing → triggers certificate eligibility check |

---

## SCR-021: Certificate Screen (Learner)

| Field | Value |
|---|---|
| **Route** | `/learner/certificates/:id` |
| **Purpose** | View and download earned certificate |
| **Primary users** | Learner |
| **Required permissions** | `certificate.view` |
| **API dependencies** | certificate-service GET /:id (TBD) |
| **Workflow** | WF-004 step 7 (post-completion) |
| **Actions** | View certificate; download PDF; share link |
| **Success state** | Certificate rendered with learner name, course name, issue date |

---

## SCR-022: Teacher Dashboard

| Field | Value |
|---|---|
| **Route** | `/teacher/dashboard` |
| **Purpose** | Teacher home: my batches, today's timetable, recent submissions, notifications |
| **Primary users** | Teacher |
| **Required permissions** | `batch.view`, `assessment.view` |
| **API dependencies** | academy-commerce-service (TBD), assessment-service GET (TBD), notification-service (TBD) |
| **Dashboard widgets** | See FRONTEND_DASHBOARD_CATALOG.md — DASH-002 |

---

## SCR-023: Attendance Marking Screen

| Field | Value |
|---|---|
| **Route** | `/teacher/batches/:id/attendance` |
| **Purpose** | Mark student attendance for a class session |
| **Primary users** | Teacher |
| **Required permissions** | `attendance.mark` |
| **API dependencies** | academy-commerce-service POST attendance (TBD) |
| **Workflow** | WF-002 via SOR.record_attendance() |
| **Actions** | Select session date; mark present/absent per student; submit |
| **Success state** | Attendance recorded; SOR updated |

---

## SCR-024: Assessment Grading Screen (Teacher)

| Field | Value |
|---|---|
| **Route** | `/teacher/assessments/:id/grade` |
| **Purpose** | Grade submitted assessment attempts |
| **Primary users** | Teacher |
| **Required permissions** | `assessment.grade` |
| **API dependencies** | attempt-service GET (TBD), attempt-service PATCH (TBD) |
| **Actions** | View submission; enter score; provide feedback; submit grade |
| **Success state** | Grade saved; learner notified via notification-service |

---

## SCR-025: Notification Center

| Field | Value |
|---|---|
| **Route** | `/notifications` (all roles); `/admin/notifications` (admin management) |
| **Purpose** | View received notifications; admin: view dispatch history |
| **Primary users** | All |
| **Required permissions** | `notification.view`; `notification.manage` (admin) |
| **API dependencies** | notification-service GET (TBD) |
| **Workflow** | WF-007 (frontend is consumer only; dispatch is backend-triggered) |
| **Actions** | Mark as read; filter by type; admin: resend notification |
| **Channel indicators** | WhatsApp, SMS, Email, Push — shown per notification record |

---

## SCR-026: Tenant Onboarding Wizard

| Field | Value |
|---|---|
| **Route** | `/admin/onboarding` |
| **Purpose** | Guide new tenant admin through initial setup |
| **Primary users** | Admin (new tenant) |
| **Required permissions** | `tenant.configure` |
| **API dependencies** | onboarding-service (TBD), tenant-service PATCH config |
| **Workflow** | WF-001 post-signup |
| **Steps** | 1. Configure org; 2. Set up first branch; 3. Create first batch; 4. Invite first teacher; 5. Add first course |

---

## SCR-027: Policy Rules Screen

| Field | Value |
|---|---|
| **Route** | `/admin/policy-rules` |
| **Purpose** | Manage SOD, explicit deny, time-window, step-up, network boundary rules |
| **Primary users** | Admin |
| **Required permissions** | `role.manage_policy` |
| **API dependencies** | `GET /api/v1/rbac/policy-rules`, `POST /api/v1/rbac/policy-rules`, `PATCH /api/v1/rbac/policy-rules/:id`, `DELETE /api/v1/rbac/policy-rules/:id` |
| **Actions** | Create rule; enable/disable rule; update rule expression |
| **Rule types** | SOD_CONFLICT, EXPLICIT_DENY, STEP_UP_REQUIRED, TIME_WINDOW, NETWORK_BOUNDARY |

---

## Screen Gap Summary

The following screens are identified as gaps (FGAP) — not built in initial sprint:

| FGAP | Screens Excluded |
|---|---|
| FGAP-001 | All parent portal screens |
| FGAP-002 | Adaptive content path view |
| FGAP-003 | AI copilot overlay (additive to SCR-018) |
| FGAP-004 | Risk insights dashboard widget (additive to SCR-004 and SCR-022) |
| FGAP-005 | Reconciliation admin screen (placeholder route in /admin/reconciliation) |
| FGAP-006 | Offline state variants; service worker |
