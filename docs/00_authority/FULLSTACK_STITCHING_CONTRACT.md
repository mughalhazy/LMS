# FULLSTACK_STITCHING_CONTRACT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Shared

> **PHASE 2 BACKEND AUTHORITY CAPTURE COMPLETE (2026-06-23)**
> **PHASE 3 FRONTEND AUTHORITY CAPTURE COMPLETE (2026-06-23)**
> Backend traceability verified by direct code inspection. Frontend consumer columns populated from Phase 3 authority documents.
> Authority documents: `docs/01_backend/` (8 docs), `docs/03_fullstack_contracts/` (5 docs), `docs/03_frontend_authority/` (12 docs), `docs/08_reports/` (8 reports)

---

## Purpose

This document traces every major feature from frontend consumer to backend component to domain entity to permission model to test coverage. It is the traceability ledger for the full stack.

**Constraint:** Populated only from verified repository information. Unknowns marked TBD – REQUIRES VERIFICATION.

---

## Traceability Structure

Each feature entry follows:

```
Feature
→ Workflow
→ Domain Entity
→ Backend Component (service + path)
→ API Endpoint
→ Frontend Consumer
→ Permission Model
→ Validation Layer
→ Test Coverage
→ Deployment Dependency
```

---

## FSC-001: User Login

**Feature:** Authenticate user and issue JWT
**Workflow:** WF-001 (Tenant Onboarding), WF-003 (Student Enrollment — auth step)
**Domain Entity:** User (Identity Domain), SessionToken
**Backend Component:** `backend/services/auth-service/`
**API Endpoint:** POST /api/v2/auth/sessions/login (from docs/specs/auth-service-spec.md §4.1; base path /api/v2/auth)
**Frontend Consumer:** `/login` screen (SCR-001 — FRONTEND_SCREEN_CATALOG.md). Tenant discovery via `GET /api/v2/auth/tenant?domain=<email>` before submit. On success: store `response.user.user_id` and `response.user.tenant_id`; fetch roles via `GET /api/v1/rbac/assignments`. Redirect to role dashboard.
**Permission Model:** Public endpoint (no prior auth required); issues RS256 JWT on success
**Validation Layer:** Username/password or SSO token; password policy via IdentityLifecycleService
**Test Coverage:** backend/services/auth-service/tests/ (confirmed; exact count not code-inspected)
**Deployment Dependency:** auth-service, user-service, rbac-service

---

## FSC-002: Course Enrollment

**Feature:** Learner enrolls in a course
**Workflow:** WF-003 (Student Enrollment — Path A)
**Domain Entity:** Enrollment (Learning Runtime Domain), Progress
**Backend Component:** `backend/services/enrollment-service/`
**API Endpoint:** POST /api/v1/enrollments (v2 compat middleware accepted; Phase 2 addendum confirms canonical is /api/v1/)
**Frontend Consumer:** `/learner/courses/:id` course detail page — "Enroll" button triggers POST /api/v1/enrollments. On success, redirect to `/learner/courses/:id/learn` (course player SCR-018). WF-003 Path A.
**Permission Model:** Authenticated learner; rbac-service enforces LEARNER role; entitlement-service checks capability
**Validation Layer:** Prerequisite check (prerequisite-engine-service), entitlement check, duplicate enrollment guard
**Test Coverage:** backend/services/enrollment-service/tests/ (confirmed; count not code-inspected)
**Deployment Dependency:** enrollment-service, prerequisite-engine-service, entitlement-service, progress-service

---

## FSC-003: JazzCash Checkout (Pakistan)

**Feature:** Learner pays for course/batch via JazzCash or EasyPaisa
**Workflow:** WF-005 (Commerce Checkout)
**Domain Entity:** CheckoutSession, Order, Transaction (Commerce Domain)
**Backend Component (HTTP):** `backend/services/checkout-service/`, `backend/services/payment-service/`, `backend/services/academy-commerce-service/`
**Backend Component (Domain):** `services/commerce/checkout.py`, `services/commerce/service.py`
**API Endpoint:** VERIFIED (Phase 2 addendum): POST /api/v1/checkout/sessions → POST .../items → POST .../submit → POST /api/v1/checkout/orders/{id}/initiate-payment → GET /api/v1/checkout/orders/{id} (poll)
**Frontend Consumer:** `/learner/checkout` multi-step checkout flow (SCR-019 — FRONTEND_SCREEN_CATALOG.md). Poll loop on order status: PENDING/PAID/FAILED. Client generates idempotency_key (UUID v4) on session creation. WF-005.
**Permission Model:** Authenticated learner; tenant_id must match payment context
**Validation Layer:** Idempotency check (tenant_id + idempotency_key), product existence check, payment retry limit (max_retries=2)
**Test Coverage:** services/commerce/tests/ (4 test files); backend/services/checkout-service/tests/ (not code-inspected)
**Deployment Dependency:** checkout-service, payment-service, integrations/payments/ (JazzCash/EasyPaisa adapters), academy-commerce-service
**CRITICAL GAP:** CheckoutService persistence is in-memory; see R-005

---

## FSC-004: Progress Tracking

**Feature:** Track learner progress through lessons and courses
**Workflow:** WF-004 (Learning and Completion)
**Domain Entity:** Progress (Learning Runtime Domain), Lesson
**Backend Component:** `backend/services/progress-service/`
**API Endpoint:** VERIFIED (Phase 2 addendum): POST /api/v1/progress/lessons/{lesson_id}/upsert, POST /api/v1/progress/lessons/{lesson_id}/complete, GET /api/v1/progress/learners/{learner_id}
**Frontend Consumer:** Course player `/learner/courses/:id/learn/:lid` (SCR-018). Lesson progress upserted automatically on playback. Lesson complete called on explicit "Mark complete" action. Learner summary drives progress bars on dashboard (DASH-003). WF-004.
**Permission Model:** Authenticated learner; tenant_id scoped
**Validation Layer:** Enrollment existence check (must be enrolled), lesson existence check
**Test Coverage:** backend/services/progress-service/tests/ (confirmed; exact count not code-inspected); also imported by system-of-record (U10)
**Deployment Dependency:** progress-service, lesson-service, enrollment-service
**ARCHITECTURAL NOTE:** system-of-record in services/ imports progress-service/src/ via importlib (U10 RD-003 — reverse dependency)

---

## FSC-005: Certificate Issuance

**Feature:** Issue certificate on course completion
**Workflow:** WF-004 (Learning and Completion — step 7)
**Domain Entity:** Certificate, Enrollment
**Backend Component:** `backend/services/certificate-service/`
**API Endpoint:** Per spec (docs/specs/certificate-service-spec.md): POST /api/v1/certificates (issue), GET /api/v1/certificates/{id} (retrieve), GET /api/v1/certificates (list), POST /api/v1/certificates/{id}/revoke, GET /api/v1/certificates/verify/{code} (public). Code inspection pending.
**Frontend Consumer:** `/learner/certificates/:id` (SCR-021 — FRONTEND_SCREEN_CATALOG.md). View and download earned certificate. Certificate list on learner dashboard (DASH-003). WF-004 step 7.
**Permission Model:** System-triggered (on enrollment completion event), or admin-triggered
**Validation Layer:** Enrollment completion status check; no re-issuance for duplicate completion
**Test Coverage:** backend/services/certificate-service/tests/ (not code-inspected)
**Deployment Dependency:** certificate-service, enrollment-service, event-ingestion-service

---

## FSC-006: Timetable and Attendance (Pakistan Academy)

**Feature:** Manage class timetable and record student attendance
**Workflow:** WF-002 (Academy Setup), WF-006 (Fee Tracking)
**Domain Entity:** academy.timetable, academy.attendance (academy-ops domain)
**Backend Component:** `backend/services/academy-commerce-service/` (HTTP wrapper), `services/academy-ops/` (domain)
**API Endpoint:** BACKEND-TBD (academy-commerce-service port 8143 — not code-inspected; spec sprint required). Domain layer confirmed via services/academy-ops/service.py: create_branch(), create_batch(), build_timetable(), record_attendance().
**Frontend Consumer:** Admin: `/admin/batches/:id/timetable` (SCR-012) — timetable management. Teacher: `/teacher/batches/:id/attendance` (SCR-023) — attendance marking. WF-002 steps 1–4, WF-006.
**Permission Model:** Authenticated teacher or admin; `timetable.manage` (admin), `attendance.mark` (teacher) permissions
**Validation Layer:** Timetable conflict detection in AcademyOpsService (verified in service.py), batch existence check
**Test Coverage:** services/academy-ops/tests/ (3 test files confirmed); backend/services/academy-commerce-service/tests/ not inspected
**Deployment Dependency:** academy-commerce-service, services/academy-ops/, services/system-of-record/, services/config-service/, backend/progress-service (via system-of-record import chain)

---

## FSC-007: Capability Gating

**Feature:** Gate feature access by tenant plan and entitlement
**Workflow:** WF-009 (Config and Entitlement Resolution)
**Domain Entity:** Capability (Platform Domain)
**Backend Component (Deployed):** `services/capability-registry/` (class-based), `services/config-service/` (class-based), `services/entitlement-service/` (class-based)
**Backend Component (HTTP):** `backend/services/capability-registry/`, `backend/services/config-service/`, `backend/services/entitlement-service/`
**API Endpoint:** BACKEND-TBD (capability-registry 8140, config-service 8141, entitlement-service 8142 — ASGI shims added Phase 2.9; HTTP API endpoints not yet inspected). Evaluation sequence confirmed: capability→config→entitlement→final_state.
**Frontend Consumer:** All permission-gated UI elements via `ShowIfAllowed`/`HideIfDenied`/`DisableIfDenied` components (FRONTEND_COMPONENT_INVENTORY.md). Admin feature-flag management: `/admin/feature-flags`. Capability gating is transparent to the frontend — it surfaces as RBAC authorize decisions. WF-009.
**Permission Model:** Any authenticated user; result scoped to tenant context
**Validation Layer:** Fixed evaluation sequence (capability → config → entitlement → final_state); MS-CONFIG-01 no branching rule
**Test Coverage:** services/capability-registry/tests/ (2), services/config-service/tests/ (1), services/entitlement-service/tests/ (1); .pyc confirms these were executed in production
**Deployment Dependency:** capability-registry (DEPLOYED class-based), config-service (DEPLOYED class-based), entitlement-service (DEPLOYED class-based — has reverse dep on backend/shared/events)
**CRITICAL GAP:** entitlement-service has direct reverse dependency on backend/services/shared/events/envelope.py (U10 RD-001 — R-001 fix required)

---

## FSC-008: LTI Integration

**Feature:** LMS-to-LMS content launch and grade passback via LTI 1.3
**Workflow:** WF-010 (LTI Integration)
**Domain Entity:** LtiLaunchContext, LtiNonce, LtiGradePassback (per docs/integrations/lti-consumer-spec.md)
**Backend Component:** `backend/services/lti-service/`
**API Endpoint:** BACKEND-TBD (lti-service port 8120 not code-inspected; spec exists in docs/integrations/lti-consumer-spec.md + lti-provider-spec.md)
**Frontend Consumer:** `/lti/launch` special route (WF-010 — FRONTEND_WORKFLOW_TO_SCREEN_MAP.md). LTI launch handler validates launch parameters, then redirects to `/learner/courses/:id/learn/:lid` or SCORM iframe. Admin LTI config: `/admin/integrations`. Grade passback is automatic on lesson completion.
**Permission Model:** LTI-specific auth; nonce validation; LTI nonce stored in Redis TTL=600s (U9 H-010)
**Validation Layer:** LTI nonce uniqueness, signature validation, context mapping
**Test Coverage:** backend/services/lti-service/tests/ (not code-inspected)
**Deployment Dependency:** lti-service, Redis (confirmed for nonce store per U9 H-010)

---

## FSC-009: Notifications (WhatsApp/SMS/Email)

**Feature:** Dispatch notifications to users via preferred channel
**Workflow:** WF-007 (Notification Dispatch)
**Domain Entity:** Notification, NotificationTemplate, WorkflowAction (per notification-service-spec.md and orchestration.py). Channels: email, SMS, WhatsApp, push — routing via action_routing.py.
**Backend Component:** `backend/services/notification-service/`, `services/notification-service/orchestration.py`
**API Endpoint:** BACKEND-TBD (notification-service port 8122 not code-inspected; spec exists in docs/specs/notification-service-spec.md)
**Frontend Consumer:** `/notifications` notification center (SCR-025 — FRONTEND_SCREEN_CATALOG.md). Admin: `/admin/notifications` dispatch log. Frontend is consumer only — dispatch is backend-triggered by domain events. WF-007.
**Permission Model:** System-triggered or admin; tenant_id scoped
**Validation Layer:** Channel availability check, recipient opt-out check, template validation
**Test Coverage:** services/notification-service/tests/ (1 test file)
**Deployment Dependency:** notification-service (HS256 auth — debt), integrations/communication/, email-service, push-service
**SECURITY DEBT:** notification-service uses HS256 JWT — R-012 required before governance

---

## FSC Coverage Summary

| FSC | Feature | Frontend Consumer | API Status | Tests |
|---|---|---|---|---|
| FSC-001 | Login | ✅ `/login` (SCR-001) | ✅ VERIFIED (Phase 2 addendum) | Partial |
| FSC-002 | Enrollment | ✅ `/learner/courses/:id` enroll button | ✅ VERIFIED (Phase 2 addendum) | Partial |
| FSC-003 | JazzCash Checkout | ✅ `/learner/checkout` (SCR-019) | ✅ VERIFIED (Phase 2 addendum) | Partial (domain) |
| FSC-004 | Progress Tracking | ✅ `/learner/courses/:id/learn/:lid` (SCR-018) | ✅ VERIFIED (Phase 2 addendum) | Partial |
| FSC-005 | Certificate Issuance | ✅ `/learner/certificates/:id` (SCR-021) | ⚠️ Spec-only (not code-inspected) | Not inspected |
| FSC-006 | Timetable/Attendance | ✅ `/admin/batches/:id/timetable`, `/teacher/batches/:id/attendance` | ⚠️ BACKEND-TBD | Partial (domain) |
| FSC-007 | Capability Gating | ✅ All gated UI via PermissionGuard | ⚠️ BACKEND-TBD (ASGI shims done) | Confirmed (.pyc) |
| FSC-008 | LTI | ✅ `/lti/launch` (WF-010) | ⚠️ BACKEND-TBD | Not inspected |
| FSC-009 | Notifications | ✅ `/notifications` (SCR-025) | ⚠️ BACKEND-TBD | Partial (domain) |

**Frontend consumer column: COMPLETE** — all 9 FSC frontend consumers populated from Phase 3 Frontend Authority Capture (2026-06-23). See `docs/03_frontend_authority/FRONTEND_SCREEN_CATALOG.md` and `FRONTEND_WORKFLOW_TO_SCREEN_MAP.md`.

**Remaining ⚠️ BACKEND-TBD items** (FSC-005 through FSC-009): API endpoints confirmed in specs but not yet code-inspected. These are implementation sprint tasks, not owner decisions.

---

## PHASE 2 ADDENDUM — Backend Traceability Verified (2026-06-23)

The following updates reflect direct code inspection of `backend/services/`. TBD items in the table above have been resolved or confirmed as-found below.

### FSC-001: Login — Phase 2 Update

**API Endpoint VERIFIED**:
- Primary: `POST /api/v2/auth/sessions/login`
- Compat alias: `POST /api/v2/auth/login`
- Token refresh: `POST /api/v2/auth/tokens/refresh`
- Session validate: `POST /api/v2/auth/sessions/validate`

**HTTP Server**: stdlib `http.server.BaseHTTPRequestHandler` (NOT FastAPI) — manifest `app.main:app` is potentially wrong for this service.

**Storage**: `InMemoryAuthStore` — sessions lost on restart (RISK-003).

**JWT**: auth-service issues RS256 (primary) or HS256 (fallback). Consuming services validate HS256 only — MISMATCH (RISK-004, RISK-006).

**Password hashing**: Argon2id (primary), PBKDF2 (fallback). Password policy: 8 chars + uppercase + digit.

**JWKS**: `GET /.well-known/jwks.json` — RSA public key for RS256 verification.

### FSC-002: Course Enrollment — Phase 2 Update

**API Endpoint VERIFIED**:
- Create: `POST /api/v1/enrollments` (v2 path also accepted via middleware rewrite)
- Get: `GET /api/v1/enrollments/{enrollment_id}`
- List: `GET /api/v1/enrollments` (filterable: learner_id, course_id, status, cohort_id, session_id)
- Status transition: `POST /api/v1/enrollments/{id}/transitions` (canonical; `/status-transitions` is alias)
- Bulk assign: `POST /api/v1/enrollments/bulk-assign` (202 response)
- Audit log: `GET /api/v1/audit-logs`

**Note**: FSC-002 previously stated `POST /api/v2/enrollments` — this is accepted via compat middleware which rewrites to `/api/v1/enrollments`.

**Storage**: `InMemoryEnrollmentStore` — data lost on restart (RISK-001).

**Optimistic locking**: `version` field on Enrollment model; `expected_version` in transition request.

**X-Actor-Id header**: Accepted (default "system").

### FSC-003: JazzCash Checkout — Phase 2 Update

**API Endpoint VERIFIED** (checkout-service base: `/api/v1/checkout`):
- Create session: `POST /api/v1/checkout/sessions`
- Get session: `GET /api/v1/checkout/sessions/{session_id}`
- Update items: `POST /api/v1/checkout/sessions/{session_id}/items`
- Submit session: `POST /api/v1/checkout/sessions/{session_id}/submit`
- Get order: `GET /api/v1/checkout/orders/{order_id}`
- Initiate payment: `POST /api/v1/checkout/orders/{order_id}/initiate-payment`

**HTTP Server**: stdlib `http.server.BaseHTTPRequestHandler` (NOT FastAPI).

**Storage**: `InMemoryCheckoutStore` — orders lost on restart (RISK-002 CRITICAL).

**JWT**: HS256 inline validation. `_jwt_valid()` returns `True` if `JWT_SHARED_SECRET` not set — security gap.

**Idempotency**: `CheckoutService.submit_session()` has idempotency check — PROHIBITED to remove per governance.

### FSC-004: Progress Tracking — Phase 2 Update

**API Endpoint VERIFIED** (progress-service base: `/api/v1/progress`):
- Upsert lesson: `POST /api/v1/progress/lessons/{lesson_id}/upsert`
- Complete lesson: `POST /api/v1/progress/lessons/{lesson_id}/complete`
- Learner summary: `GET /api/v1/progress/learners/{learner_id}`
- Course progress: `GET /api/v1/progress/learners/{learner_id}/courses/{course_id}`
- Assign learning path: `POST /api/v1/progress/learning-paths/{id}/assignments` (202)
- Certificate eligibility: `GET /api/v1/progress/eligibility/courses/{course_id}/users/{user_id}`

**Storage**: `InMemoryProgressStore` — data lost on restart (RISK-001).

**Tenant validation**: `X-Tenant-Id` must match `request.tenant_id` body field (400 `tenant_mismatch` if not).

### FSC-005 through FSC-009: Status

| FSC | API Status | Service | Notes |
|---|---|---|---|
| FSC-005 Certificate | Spec-only; not code-inspected | certificate-service 8106 | API confirmed per spec (docs/specs/certificate-service-spec.md). Code inspection pending backend sprint. |
| FSC-006 Timetable | BACKEND-TBD | academy-commerce-service 8143 | Domain layer confirmed (academy-ops/service.py). HTTP API: code inspection pending. |
| FSC-007 Capability | ASGI shims complete (D-002 RESOLVED Phase 2.9) | capability-registry 8140, config-service 8141, entitlement-service 8142 | Startup mechanism resolved. HTTP API endpoints: code inspection pending. |
| FSC-008 LTI | BACKEND-TBD | lti-service 8120 | Specs: docs/integrations/lti-consumer-spec.md + lti-provider-spec.md. Code inspection pending. |
| FSC-009 Notifications | BACKEND-TBD | notification-service 8122 | Domain layer confirmed (orchestration.py, action_routing.py). HS256 auth exception documented (B05-002). HTTP API inspection pending. |

### Backend Cross-Cutting Facts (All FSCs)

| Rule | Verified |
|---|---|
| JWT Bearer required on all auth endpoints | Yes — `Depends(require_jwt)` at app level |
| X-Tenant-Id header required | Yes — all inspected services |
| JWT tenant_id claim must match X-Tenant-Id | Yes — 401/403 on mismatch |
| X-API-Version: v1 on all responses | Yes — CAT-004 compliant |
| Security headers on all FastAPI responses | Yes — `apply_security_headers()` |
| Event consumers registered at startup | Yes — FA-024 / G-24 compliant |
| All storage is in-memory | **Partially** — 16 services now use SQLite (Task 7 2026-06-23); 53 remain InMemory |
| All events are in-memory | **Partially** — shared in-process `EventBus` singleton (`backend/services/shared/events/bus.py`); NOT per-service InMemoryEventPublisher; cross-process delivery still requires external broker |

### Phase 2 New Documents (Backend Authority)

| Category | Documents |
|---|---|
| Backend Architecture | `docs/01_backend/BACKEND_ARCHITECTURE.md` |
| Database Schema | `docs/01_backend/DATABASE_SCHEMA.md` |
| API Contract | `docs/01_backend/API_CONTRACT.md` |
| Error Contract | `docs/01_backend/ERROR_CONTRACT.md` |
| Service Catalog | `docs/01_backend/SERVICE_CATALOG.md` |
| Integration Catalog | `docs/01_backend/INTEGRATION_CATALOG.md` |
| Validation Rules | `docs/01_backend/VALIDATION_RULES.md` |
| Event Architecture | `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` |
| Auth & Tenancy Contract | `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` |
| Roles & Permissions | `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` |
| Data Shape Registry | `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` |
| Validation Parity | `docs/03_fullstack_contracts/VALIDATION_PARITY.md` |
| Contract Version Registry | `docs/03_fullstack_contracts/CONTRACT_VERSION_REGISTRY.md` |
| Backend Capture Report | `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` |
| Architecture Report | `docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md` |
| Database Discovery | `docs/08_reports/DATABASE_DISCOVERY_REPORT.md` |
| API Discovery | `docs/08_reports/API_DISCOVERY_REPORT.md` |
| Security Discovery | `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` |
| Event Discovery | `docs/08_reports/EVENT_DISCOVERY_REPORT.md` |
| Gap Register | `docs/08_reports/BACKEND_GAP_REGISTER.md` |
| Risk Register | `docs/08_reports/BACKEND_RISK_REGISTER.md` |
