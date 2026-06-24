# FRONTEND AUTHORITY MASTER

Status: Complete
Date: 2026-06-23
Phase: Phase 3 — Frontend Authority Capture
Owner: AI

---

## Purpose

This document is the top-level reference for all frontend authority decisions. It defines what the frontend must represent based on verified backend reality. Every element is derived from authority source documents — nothing is invented.

---

## Authoritative Source Documents

| Document | Location | Role |
|---|---|---|
| PROJECT_CHARTER.md | docs/00_authority/ | Product mission, objectives |
| FEATURE_SCOPE.md | docs/00_authority/ | Feature scope and boundaries |
| PRODUCT_WORKFLOWS.md | docs/00_authority/ | Business workflows |
| FULLSTACK_STITCHING_CONTRACT.md | docs/00_authority/ | Feature-to-API traceability |
| DOMAIN_MODEL.md | docs/00_authority/ | Domain entities |
| API_CONTRACT.md | docs/01_backend/ | API endpoints, headers, pagination |
| SERVICE_CATALOG.md | docs/01_backend/ | 69 registered services |
| VALIDATION_RULES.md | docs/01_backend/ | Validation constraints |
| ERROR_CONTRACT.md | docs/01_backend/ | Error shapes |
| AUTH_AND_TENANCY_CONTRACT.md | docs/03_fullstack_contracts/ | Auth flows, session model |
| USER_ROLES_AND_PERMISSIONS.md | docs/03_fullstack_contracts/ | RBAC model |
| DATA_SHAPE_REGISTRY.md | docs/03_fullstack_contracts/ | Request/response shapes |
| AI_OPERATING_CONTEXT.md | docs/07_governance/ | Architectural decisions |
| POST_COLLAPSE_FRONTEND_READINESS.md | docs/08_reports/ | Product scope locked |
| DETERMINISM_CERTIFICATION_REPORT.md | docs/08_reports/ | Repository determinism |
| FRONTEND_GAP_REGISTER.md | docs/08_reports/ | 6 implementation gaps |

---

## Frontend Architecture Constraints (Non-Negotiable)

These constraints are derived from backend reality and are fixed before any frontend is built:

### 1. Permission-Based Navigation (PDC-012, confirmed)
All route guards and UI element visibility are driven by `POST /api/v1/rbac/authorize`. No hardcoded role_key string comparisons in route middleware or UI rendering.

### 2. JWT Identity Model (AUTH_AND_TENANCY_CONTRACT.md)
- `access_token.sub` = session_id (NOT user_id)
- `user_id` is in login response at `response.user.user_id`
- `tenant_id` is in login response at `response.user.tenant_id`
- Roles are NOT in login response — fetch via `GET /api/v1/rbac/assignments?subject_id=<user_id>&tenant_id=<tenant_id>`

### 3. Required Headers on Every Request
```
Authorization: Bearer <access_token>
X-Tenant-Id: <tenant_id>
Content-Type: application/json
```

### 4. Session-Service API Version Exception
All services use `/api/v1/`. Session-service uses `/api/v2/sessions/` — intentional (documented OA-009).
Auth-service uses `/api/v2/auth/` — native v2.

### 5. No Invented Functionality
All screens, routes, workflows, and forms must map to a backend service endpoint or a confirmed FGAP. No orphan screens.

---

## User Roles in Scope

| Role | Build Status | Experience |
|---|---|---|
| Admin (tenant admin, platform admin) | ✅ Build now | Full tenant management, academy ops, RBAC, analytics |
| Teacher | ✅ Build now | Content delivery, batch management, attendance, grading |
| Learner | ✅ Build now | Course consumption, payments, assessments, certificates, AI tutor |
| Parent/Guardian | ❌ FGAP-001 | Child monitoring — sprint required before building |

---

## Features in Scope (Build Now)

| Feature Area | §FEATURE_SCOPE | Services |
|---|---|---|
| Identity & Access (login, SSO, password reset) | §1.1 | auth-service, sso-service, rbac-service |
| Organization & Tenancy | §1.2 | tenant-service, org-service, institution-service |
| Learning Structure (courses, lessons, content) | §1.3 | course-service, lesson-service, content-service, scorm-service |
| Learning Runtime (enrollment, progress, session) | §1.4 | enrollment-service, progress-service, session-service |
| Assessment & Certification | §1.5 | assessment-service, certificate-service, badge-service |
| Commerce & Billing (JazzCash/EasyPaisa) | §1.6 | checkout-service, payment-service, invoice-billing-service |
| Academy Operations (branches, batches, timetable) | §1.7 | academy-commerce-service, academy-ops domain |
| Notifications | §1.8 | notification-service |
| Analytics & Reporting | §1.9 | learning-analytics-service, reporting-service |
| AI Tutor + Recommendations + Course Generation | §1.10 | ai-tutor-service, recommendation-service, course-generation-service |
| User & Profile Management | Platform | user-service |
| RBAC Management | Platform | rbac-service |
| Reviews & Ratings | §1.3 | review-service |
| HRIS Integration | §1.11 | hris-sync-service |
| LTI Integration | §1.11 | lti-service |
| Webhooks | §1.11 | webhook-service |
| Feature Flags | §1.11 | feature-flag-service |

---

## Feature Gaps (Sprint Required — Not in Initial Build)

| Gap | FGAP | Screens Blocked |
|---|---|---|
| Parent/Guardian Portal | FGAP-001 | All parent screens |
| Adaptive Learning | FGAP-002 | Adaptive content path |
| AI Copilot Overlay | FGAP-003 | Cross-screen copilot UI |
| Learner Risk Insights | FGAP-004 | Risk dashboard widgets |
| Reconciliation Admin Screen | FGAP-005 | Reconciliation admin view |
| PWA Offline Frontend | FGAP-006 | Offline state, service worker |

---

## Frontend Documents (This Directory)

| Document | Purpose |
|---|---|
| FRONTEND_AUTHORITY_MASTER.md | This document — top-level reference |
| FRONTEND_ROUTE_CATALOG.md | All routes: path, role, permissions, API |
| FRONTEND_SCREEN_CATALOG.md | All screens: purpose, actions, states |
| FRONTEND_DASHBOARD_CATALOG.md | All dashboards: widgets, KPIs, data sources |
| FRONTEND_NAVIGATION_MODEL.md | Navigation structure per role |
| FRONTEND_ROLE_EXPERIENCE_MATRIX.md | Role × feature experience matrix |
| FRONTEND_PERMISSION_MATRIX.md | Permission keys and their UI impact |
| FRONTEND_WORKFLOW_TO_SCREEN_MAP.md | Workflow → screen traceability |
| FRONTEND_API_DEPENDENCY_MAP.md | Screen → API dependency map |
| FRONTEND_COMPONENT_INVENTORY.md | Common UI components required |
| FRONTEND_GAP_REGISTER.md | 6 gaps (frontend-specific view) |
| FRONTEND_AUTHORITY_READINESS_REPORT.md | Final readiness assessment |

---

## Commerce Context (Pakistan-First)

Payment integration is Pakistan-specific in the current phase:
- **Payment providers:** JazzCash (primary), EasyPaisa (secondary)
- **Currency:** PKR
- **Checkout flow:** create session → add items → submit → initiate-payment → poll for status
- **Status polling:** `GET /api/v1/checkout/orders/{order_id}` — three states: PENDING / PAID / FAILED
- **No international payment methods** in current scope

---

## Key API Base Paths

| Service | Base Path | Port |
|---|---|---|
| auth-service | `/api/v2/auth` | 8104 |
| rbac-service | `/api/v1/rbac` | 8128 |
| tenant-service | `/api/v1/tenants` | 8135 |
| user-service | `/api/v1/users` (TBD) | 8136 |
| enrollment-service | `/api/v1/enrollments` | 8113 |
| progress-service | `/api/v1/progress` | 8125 |
| checkout-service | `/api/v1/checkout` | 8147 |
| session-service | `/api/v2/sessions` | 8165 |
| course-service | `/api/v1/courses` (TBD) | 8110 |
| notification-service | `/api/v1/notifications` (TBD) | 8122 |
| academy-commerce-service | TBD | 8143 |

---

## Commerce/Auth Token Flow (Summary)

```
1. GET /api/v2/auth/tenant?domain=<email>   ← tenant discovery (pre-login)
2. POST /api/v2/auth/sessions/login          ← login → { session_id, access_token, refresh_token, user: { user_id, tenant_id } }
3. Store: access_token, user_id, tenant_id, session_id
4. GET /api/v1/rbac/assignments?subject_id=&tenant_id=  ← load user permissions
5. POST /api/v1/rbac/authorize               ← before any gated UI render
6. POST /api/v2/auth/tokens/refresh          ← on 401 with refresh token
7. POST /api/v2/auth/sessions/logout         ← on logout
```

---

## Verdict

All source documents reviewed. Frontend authority model is deterministic from backend reality. 12 authority documents captured below. No frontend invention performed.
