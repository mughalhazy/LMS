# UNDOCUMENTED CODE REGISTER

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Source: Direct code inspection + five-domain audit

Code that exists and is functional but has no documentation coverage in any authority document. These are not gaps — the code is real. The documentation is missing.

---

## UDC-001: API Contract Covers Only 6 of 69 Services (~9%)

| Field | Value |
|---|---|
| **ID** | UDC-001 |
| **Severity** | CRITICAL |
| **Description** | API_CONTRACT.md documents endpoint-level detail for only auth, rbac, tenant, enrollment, progress, checkout. The other 63 services have no endpoint documentation in any contract document. |
| **Impact** | Frontend cannot plan API integration for any undocumented service |
| **Services undocumented** | All 63 not listed above — see UDC-002 through UDC-013 for sampled services |
| **Action** | Owner decision on scope of contract documentation before Frontend Authority Capture |

---

## UDC-002: user-service — 17+ Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-002 |
| **Severity** | CRITICAL |
| **Base path** | `/api/v1/users` |
| **Endpoints found** | CRUD (create, get, update, delete), status lifecycle (activate, deactivate, suspend, lock), profile, role-links, identity-links, preferences (get/set), timeline/audit, events, bulk-status |
| **Data shapes missing** | `CreateUserRequest` (12 fields), `UserResponse`, `UpdateUserRequest`, `UserPreferencesRequest/Response`, `IdentityLinkRequest/Response`, `LifecycleCommand`, `AuditLogResponse` — none in DATA_SHAPE_REGISTRY.md |
| **Evidence** | backend/services/user-service/app/main.py, schemas.py |

---

## UDC-003: course-service — 12 Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-003 |
| **Severity** | CRITICAL |
| **Base path** | `/api/v1/courses` |
| **Endpoints found** | CRUD, publish, archive, program-links, session-links |
| **Data shapes missing** | `CreateCourseRequest` (rich — 17 fields + embedded TenantContext), `CourseResponse` (17 fields), `UpdateCourseRequest`, `PublishCourseRequest`, `ArchiveCourseRequest`, `UpsertProgramLinksRequest`, `SessionLinksRequest` |
| **Unusual pattern** | CreateCourseRequest embeds tenant context fields directly in body (`tenant_name`, `country_code`, `segment_context`, `plan_type`, `addon_flags`) alongside `tenant_id` — not documented anywhere |
| **Evidence** | backend/services/course-service/app/main.py, schemas.py |

---

## UDC-004: lesson-service — 14+ Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-004 |
| **Severity** | CRITICAL |
| **Base path** | `/api/v1/lessons` |
| **Endpoints found** | CRUD, versions, publish, unpublish, archive, delivery-state, progression-hooks, reorder |
| **Evidence** | backend/services/lesson-service/app/main.py |

---

## UDC-005: session-service — 14+ Endpoints Undocumented, v2 Prefix

| Field | Value |
|---|---|
| **ID** | UDC-005 |
| **Severity** | HIGH |
| **Base path** | `/api/v2/sessions` (v2, not v1) |
| **Endpoints found** | Lifecycle: schedule, publish, start, complete, cancel, archive; course/lesson/cohort links, calendar, by-course, by-cohort |
| **Note** | session-service uses `/api/v2/` prefix — different from all other services on `/api/v1/`. Not documented in API_CONTRACT.md or any contract. |
| **Evidence** | backend/services/session-service/app/main.py |

---

## UDC-006: org-service — Owns Three Entity Types Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-006 |
| **Severity** | HIGH |
| **Base paths** | `/api/v1/organizations`, `/api/v1/departments`, `/api/v1/teams` |
| **Endpoints found** | 14+ total across 3 entity types |
| **Note** | SERVICE_CATALOG.md describes org-service as "Organizational hierarchy only" — no mention that it also owns departments and teams. Frontend expecting separate department-service or team-service would be wrong. |
| **Evidence** | backend/services/org-service/app/main.py |

---

## UDC-007: assessment-service Owns Attempt Routes (Overlap with attempt-service)

| Field | Value |
|---|---|
| **ID** | UDC-007 |
| **Severity** | HIGH |
| **Description** | assessment-service/app/main.py registers both `/api/v1/assessments/*` AND `/api/v1/attempts/*` routes (18+ endpoints total). attempt-service is also a separate registered service at port 8103 — potential duplicate ownership of `/api/v1/attempts/*`. |
| **Impact** | Frontend must know which service to call for attempt operations |
| **Action** | Owner decision needed — see OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md OA-006 |

---

## UDC-008: certificate-service — 10+ Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-008 |
| **Severity** | HIGH |
| **Base path** | `/api/v1/certificates`, `/api/v1/certificate-templates` |
| **Endpoints found** | CRUD, verify by code, badge-extension, templates CRUD |
| **Evidence** | backend/services/certificate-service/app/main.py |

---

## UDC-009: notification-service — 7 Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-009 |
| **Severity** | HIGH |
| **Base path** | `/api/v1/notifications/*` |
| **Endpoints found** | preferences, routes, orchestrate, events, deliveries/drain, inbox |
| **Evidence** | backend/services/notification-service/app/main.py |

---

## UDC-010: program-service — 9 Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-010 |
| **Severity** | HIGH |
| **Base path** | `/api/v1/programs` |
| **Endpoints found** | CRUD, status transition, institution-links, course mapping |
| **Evidence** | backend/services/program-service/app/main.py |

---

## UDC-011: badge-service — 6+ Endpoints Undocumented

| Field | Value |
|---|---|
| **ID** | UDC-011 |
| **Severity** | MEDIUM |
| **Base path** | `/api/v1/badge/definitions`, `/api/v1/badge/issuances` |
| **Endpoints found** | 6+ endpoints across badge definitions and issuances |
| **Evidence** | backend/services/badge-service/app/main.py |

---

## UDC-012: Shared Security Module — Not Documented

| Field | Value |
|---|---|
| **ID** | UDC-012 |
| **Severity** | MEDIUM |
| **Description** | `backend/services/shared/security.py` (created Task 7) is a canonical RS256+HS256 security module with `require_jwt()`, `require_tenant_scope()`, `apply_security_headers()`, `validate_jwt()`. Not referenced in any architecture or contract document. |
| **Action** | Add reference to BACKEND_ARCHITECTURE.md shared utilities section |

---

## UDC-013: auth_tenants Table in auth-service

| Field | Value |
|---|---|
| **ID** | UDC-013 |
| **Severity** | MEDIUM |
| **Description** | auth-service/app/store_db.py creates an `auth_tenants` table (tenant_id, name, active) as a local read-only tenant cache. Not documented in auth-service-storage-contract.md or DATABASE_SCHEMA.md. |
| **Action** | Add to auth-service-storage-contract.md |

---

## UDC-014: Refresh JWT Extra Claims

| Field | Value |
|---|---|
| **ID** | UDC-014 |
| **Severity** | MEDIUM |
| **Description** | Refresh tokens contain additional claims not in any contract: `token_type: "refresh"`, `family_id` (UUID for lineage tracking per AUD-050), explicit `jti`. Access tokens also include undocumented `scope: "lms.api"` and both `sid` and `session_id` claims (duplication). |
| **Action** | Add to AUTH_AND_TENANCY_CONTRACT.md JWT claims table |

---

## UDC-015: root services/ Directories with Active Backend Imports

| Field | Value |
|---|---|
| **ID** | UDC-015 |
| **Severity** | MEDIUM |
| **Description** | Root `services/entitlement-service/` is imported by payment-service (guarded). Root `services/subscription-service/` is imported by tenant-service (guarded). Root `shared/` is imported by 5 backend services. Root `integrations/` is imported by notification-service, payment-service, sso-service. None of this cross-layer import topology is documented. |
| **Action** | Document import topology in BACKEND_ARCHITECTURE.md |

---

## UDC-016: Three Undocumented Backend HTTP Services (Dual-Layer)

| Field | Value |
|---|---|
| **ID** | UDC-016 |
| **Severity** | MEDIUM |
| **Description** | `backend/services/capability-registry/`, `backend/services/config-service/`, `backend/services/entitlement-service/` are complete stdlib http.server implementations with routes, but are NOT registered in service-manifest.json (only their root `services/` equivalents are). They are completely undocumented in any catalog or contract. |
| **Action** | Document existence; owner decision on whether to replace manifest entries |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 2 (UDC-001, UDC-002/003 pattern) |
| HIGH | 9 |
| MEDIUM | 5 |
| **Total** | **16** |
