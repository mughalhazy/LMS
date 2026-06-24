# FRONTEND API DEPENDENCY MAP

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Source Authority

- API_CONTRACT.md (base paths, headers, auth rules)
- SERVICE_CATALOG.md (all 69 services, port map)
- FULLSTACK_STITCHING_CONTRACT.md (FSC-001 through FSC-009)
- AUTH_AND_TENANCY_CONTRACT.md
- FRONTEND_SCREEN_CATALOG.md
- FRONTEND_ROUTE_CATALOG.md

---

## Universal API Requirements

All requests (except exempt paths) MUST include:

```
Authorization: Bearer <access_token>
X-Tenant-Id: <tenant_id>
Content-Type: application/json
```

All responses include:
```
X-API-Version: v1
```

### Exempt Paths (no auth headers required)

```
/health
/metrics
/.well-known/jwks.json
/api/v2/auth/sessions/login
/api/v2/auth/password/forgot
/api/v2/auth/tenant
```

### Session-Service v2 Exception

All services: `/api/v1/`
Except: auth-service (`/api/v2/auth`) and session-service (`/api/v2/sessions`)

---

## Pagination Shape

All list endpoints return:
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

NOTE: `total` field is a stub — always returns 0 until count query sprint. Frontend must handle 0 gracefully (do not render "0 results" when items is non-empty).

---

## Screen-to-API Dependency Map

### Auth & Session Screens

| Screen | Route | Service | Port | Method | Endpoint | Purpose |
|---|---|---|---|---|---|---|
| Login | /login | auth-service | 8100 | GET | `/api/v2/auth/tenant?domain=<email>` | Tenant discovery |
| Login | /login | auth-service | 8100 | POST | `/api/v2/auth/sessions/login` | Create session |
| Login (post) | any | session-service | 8101 | POST | `/api/v2/sessions/refresh` | Refresh access token |
| Login (post) | any | session-service | 8101 | DELETE | `/api/v2/sessions/:id` | Logout / revoke |
| Login (post) | any | rbac-service | 8108 | GET | `/api/v1/rbac/assignments?subject_id=&tenant_id=` | Fetch role assignments |
| Login (post) | any | rbac-service | 8108 | GET | `/api/v1/rbac/subjects/user/{user_id}/effective-permissions` | Prefetch permissions for nav |
| Forgot Password | /forgot-password | auth-service | 8100 | POST | `/api/v2/auth/password/forgot` | Initiate reset |
| Reset Password | /reset-password | auth-service | 8100 | POST | `/api/v2/auth/password/reset` | Complete reset |

---

### Admin Screens

| Screen | Route | Service | Port | Method | Endpoint | Purpose |
|---|---|---|---|---|---|---|
| Admin Dashboard | /admin/dashboard | tenant-service | 8104 | GET | `/api/v1/tenants/:id/lifecycle` | Tenant status |
| Admin Dashboard | /admin/dashboard | enrollment-service | 8130 | GET | `/api/v1/enrollments` (agg) | Enrollment stats |
| Admin Dashboard | /admin/dashboard | revenue-service | TBD | GET | TBD | Revenue summary |
| Admin Dashboard | /admin/dashboard | learning-analytics-service | TBD | GET | TBD | Active users |
| User Management | /admin/users | user-service | TBD | GET | TBD | User list |
| User Detail | /admin/users/:id | user-service | TBD | GET | TBD | User profile |
| User Detail | /admin/users/:id | rbac-service | 8108 | GET | `/api/v1/rbac/assignments?subject_id=` | User role assignments |
| User Detail | /admin/users/:id | rbac-service | 8108 | POST | `/api/v1/rbac/assignments` | Add assignment |
| User Detail | /admin/users/:id | rbac-service | 8108 | DELETE | `/api/v1/rbac/assignments/:id` | Revoke assignment |
| Role Management | /admin/roles | rbac-service | 8108 | GET | `/api/v1/rbac/roles` | Role list |
| Role Detail | /admin/roles/:id | rbac-service | 8108 | GET | `/api/v1/rbac/roles/:id` | Role detail |
| Role Detail | /admin/roles/:id | rbac-service | 8108 | GET | `/api/v1/rbac/permissions` | Permissions catalog |
| Role Detail | /admin/roles/:id | rbac-service | 8108 | PUT | `/api/v1/rbac/roles/:id/permissions` | Update permissions |
| Role Detail | /admin/roles/:id | rbac-service | 8108 | PATCH | `/api/v1/rbac/roles/:id` | Edit role |
| Audit Log | /admin/audit-log | rbac-service | 8108 | GET | `/api/v1/rbac/audit-log` | Auth decisions |
| Policy Rules | /admin/policy-rules | rbac-service | 8108 | GET | `/api/v1/rbac/policy-rules` | Policy list |
| Policy Rules | /admin/policy-rules | rbac-service | 8108 | POST | `/api/v1/rbac/policy-rules` | Create rule |
| Policy Rules | /admin/policy-rules | rbac-service | 8108 | PATCH | `/api/v1/rbac/policy-rules/:id` | Update rule |
| Policy Rules | /admin/policy-rules | rbac-service | 8108 | DELETE | `/api/v1/rbac/policy-rules/:id` | Delete rule |
| Branch Management | /admin/branches | academy-commerce-service | TBD | GET/POST | TBD | Branch CRUD |
| Batch Management | /admin/batches/:id | academy-commerce-service | TBD | GET/POST/PATCH | TBD | Batch CRUD + students |
| Timetable | /admin/batches/:id/timetable | academy-commerce-service | TBD | GET/POST | TBD | Timetable slots |
| Fee Structures | /admin/fee-structures | academy-commerce-service | TBD | GET/POST/PATCH | TBD | Fee config |
| Course Management | /admin/courses | course-service | TBD | GET | TBD | Course list |
| Course Detail (admin) | /admin/courses/:id | course-service | TBD | GET/PATCH | TBD | Course detail + edit |
| Course Detail (admin) | /admin/courses/:id | enrollment-service | 8130 | GET | `/api/v1/enrollments?course_id=` | Enrolled students |
| Tenant Settings | /admin/settings | tenant-service | 8104 | PATCH | `/api/v1/tenants/:id/configuration` | Config update |
| Feature Flags | /admin/feature-flags | feature-flag-service | TBD | GET/PATCH | TBD | Feature toggles |
| Integrations | /admin/integrations | lti-service | TBD | GET/POST | TBD | LTI config |
| Analytics | /admin/analytics | learning-analytics-service | TBD | GET | TBD | Analytics data |
| Analytics | /admin/analytics | skill-analytics-service | TBD | GET | TBD | Skill data |
| Revenue | /admin/revenue | revenue-service | TBD | GET | TBD | Revenue report |
| Billing | /admin/billing | invoice-billing-service | TBD | GET | TBD | Invoice list |
| Notifications (admin) | /admin/notifications | notification-service | TBD | GET | TBD | Dispatch log |

---

### Teacher Screens

| Screen | Route | Service | Port | Method | Endpoint | Purpose |
|---|---|---|---|---|---|---|
| Teacher Dashboard | /teacher/dashboard | academy-commerce-service | TBD | GET | TBD | My batches |
| Teacher Dashboard | /teacher/dashboard | assessment-service | TBD | GET | TBD | Upcoming assessments |
| Teacher Dashboard | /teacher/dashboard | attempt-service | TBD | GET | TBD | Ungraded submissions |
| Timetable (teacher) | /teacher/batches/:id/timetable | academy-commerce-service | TBD | GET | TBD | View timetable |
| Course Detail (teacher) | /teacher/courses/:id | course-service | TBD | GET/PATCH | TBD | Course detail |
| Content Upload | /teacher/courses/:id/content | content-service | TBD | POST | TBD | Register content metadata |
| Content Upload | /teacher/courses/:id/content | media-service | TBD | POST | TBD | Binary upload |
| Attendance | /teacher/batches/:id/attendance | academy-commerce-service | TBD | POST | TBD | Mark attendance |
| Grading | /teacher/assessments/:id/grade | attempt-service | TBD | GET | TBD | View submissions |
| Grading | /teacher/assessments/:id/grade | attempt-service | TBD | PATCH | TBD | Submit grade |

---

### Learner Screens

| Screen | Route | Service | Port | Method | Endpoint | Purpose |
|---|---|---|---|---|---|---|
| Learner Dashboard | /learner/dashboard | enrollment-service | 8130 | GET | `/api/v1/enrollments?learner_id=` | Enrolled courses |
| Learner Dashboard | /learner/dashboard | progress-service | TBD | GET | `/api/v1/progress/learners/:id` | Progress summary |
| Learner Dashboard | /learner/dashboard | recommendation-service | TBD | GET | TBD | Recommendations |
| Learner Dashboard | /learner/dashboard | assessment-service | TBD | GET | TBD | Upcoming assessments |
| Learner Dashboard | /learner/dashboard | certificate-service | TBD | GET | TBD | Certificates |
| Course Catalog | /learner/courses | course-service | TBD | GET | TBD | Course list |
| Course Catalog | /learner/courses | enrollment-service | 8130 | GET | `/api/v1/enrollments?learner_id=` | My enrollments |
| Course Player | /learner/courses/:id/learn/:lid | lesson-service | TBD | GET | TBD | Lesson content |
| Course Player | /learner/courses/:id/learn/:lid | content-service | TBD | GET | TBD | Content assets |
| Course Player | /learner/courses/:id/learn/:lid | progress-service | TBD | POST | `/api/v1/progress/lessons/:id/upsert` | Save progress |
| Course Player | /learner/courses/:id/learn/:lid | progress-service | TBD | POST | `/api/v1/progress/lessons/:id/complete` | Mark complete |
| Course Player | /learner/courses/:id/learn/:lid | ai-tutor-service | TBD | POST | TBD | AI tutor chat |
| Course Player | /learner/courses/:id/learn/:lid | enrollment-service | 8130 | GET | `/api/v1/enrollments?learner_id=&course_id=` | Verify enrollment (gate) |
| Assessment Player | /learner/assessments/:id | assessment-service | TBD | GET | TBD | Assessment data |
| Assessment Player | /learner/assessments/:id | attempt-service | TBD | POST | TBD | Submit attempt |
| Checkout | /learner/checkout | checkout-service | TBD | POST | `/api/v1/checkout/sessions` | Create session |
| Checkout | /learner/checkout | checkout-service | TBD | POST | `/api/v1/checkout/sessions/:id/items` | Add item |
| Checkout | /learner/checkout | checkout-service | TBD | POST | `/api/v1/checkout/sessions/:id/submit` | Submit |
| Checkout | /learner/checkout | checkout-service | TBD | POST | `/api/v1/checkout/orders/:id/initiate-payment` | Initiate payment |
| Order Status | /learner/orders/:id | checkout-service | TBD | GET | `/api/v1/checkout/orders/:id` | Poll status |
| Certificate | /learner/certificates/:id | certificate-service | TBD | GET | TBD | Certificate detail |

---

### Shared / All Roles

| Screen | Route | Service | Port | Method | Endpoint | Purpose |
|---|---|---|---|---|---|---|
| All routes | Any | rbac-service | 8108 | POST | `/api/v1/rbac/authorize` | Permission check |
| Notifications | /notifications | notification-service | TBD | GET | TBD | Notification inbox |
| Profile | /profile | user-service | TBD | GET/PATCH | TBD | Own profile |

---

## Service TBD Tracker

The following services have confirmed base paths from SERVICE_CATALOG.md but specific API endpoints require inspection during frontend implementation sprint:

| Service | Port | Domain | Confirmed Base | Needs |
|---|---|---|---|---|
| user-service | TBD | Auth/Identity | /api/v1/users | GET /:id, GET list, PATCH /:id |
| course-service | TBD | Learning | /api/v1/courses | GET list, GET /:id, PATCH /:id |
| lesson-service | TBD | Learning | /api/v1/lessons | GET /:id, POST, PATCH /:id |
| content-service | TBD | Media | /api/v1/content | POST (metadata), GET /:id |
| media-service | TBD | Media | /api/v1/media | POST (binary upload) |
| assessment-service | TBD | Assessment | /api/v1/assessments | GET /:id, GET list |
| attempt-service | TBD | Assessment | /api/v1/attempts | POST, GET /:id, PATCH (grade) |
| progress-service | TBD | Learning | /api/v1/progress | Confirmed upsert/complete |
| certificate-service | TBD | Learning | /api/v1/certificates | GET /:id |
| notification-service | TBD | Communication | /api/v1/notifications | GET list |
| ai-tutor-service | TBD | AI | /api/v1/ai-tutor | POST chat |
| recommendation-service | TBD | AI | /api/v1/recommendations | GET |
| academy-commerce-service | TBD | Commerce/Ops | /api/v1/academy | CRUD branches, batches, timetable, attendance |
| revenue-service | TBD | Finance | /api/v1/revenue | GET summary, GET trend |
| invoice-billing-service | TBD | Finance | /api/v1/invoices | GET list, GET /:id |
| feature-flag-service | TBD | Platform | /api/v1/feature-flags | GET, PATCH |
| learning-analytics-service | TBD | Analytics | /api/v1/analytics/learning | GET aggregates |
| skill-analytics-service | TBD | Analytics | /api/v1/analytics/skills | GET |
| lti-service | TBD | Integration | /api/v1/lti | GET/POST config |

---

## Request/Response Shape Reference

### Authorize (used on every gated route)

Request:
```json
POST /api/v1/rbac/authorize
{
  "subject_type": "user",
  "subject_id": "<user_id>",
  "permission_key": "course.publish",
  "resource_type": "course",
  "resource_id": "<course_id>"
}
```

Response:
```json
{
  "decision": "allow",
  "policy_rule_id": null,
  "reason": null
}
```

### Login (FSC-001 confirmed shape)

Response:
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<token>",
  "session_id": "<uuid>",
  "expires_in": 3600,
  "user": {
    "user_id": "<uuid>",
    "tenant_id": "<uuid>",
    "email": "...",
    "display_name": "..."
  }
}
```

IMPORTANT: `access_token.sub` = session_id (NOT user_id). Roles NOT in login response — fetch via `GET /api/v1/rbac/assignments`.

### Enrollment (FSC-002 confirmed)

Request: `POST /api/v1/enrollments`
Response: enrollment object

Progress endpoints confirmed (FSC-003):
- `POST /api/v1/progress/lessons/:lesson_id/upsert` → upsert progress
- `POST /api/v1/progress/lessons/:lesson_id/complete` → mark complete
- `GET /api/v1/progress/learners/:learner_id` → learner summary

Checkout (FSC-004 confirmed):
- `POST /api/v1/checkout/sessions` → create session
- `POST /api/v1/checkout/sessions/:id/items` → add items
- `POST /api/v1/checkout/sessions/:id/submit` → submit
- `POST /api/v1/checkout/orders/:id/initiate-payment` → pay
- `GET /api/v1/checkout/orders/:id` → poll (states: PENDING, PAID, FAILED)
