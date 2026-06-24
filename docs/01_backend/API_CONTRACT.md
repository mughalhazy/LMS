# API_CONTRACT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

This document captures the API contract patterns as implemented across `backend/services/`. It covers request/response conventions, required headers, versioning, authentication, and pagination. Derived from direct code inspection.

---

## Base Path Conventions

| Pattern | Status | Notes |
|---|---|---|
| `/api/v1/<resource>` | Active | Primary path for all services |
| `/api/v2/<resource>` | Compat alias | Middleware rewrites to `/api/v1/` in enrollment-service; not universally implemented |
| `/api/v2/auth/<resource>` | Auth-service only | auth-service uses v2 natively (not via rewrite) |

Auth-service base path: `/api/v2/auth`
All other services: `/api/v1/<domain>`

---

## Required Headers

### On Every Request (Non-Exempt Endpoints)

| Header | Value | Required | Notes |
|---|---|---|---|
| `Authorization` | `Bearer <jwt>` | Yes | All authenticated endpoints |
| `X-Tenant-Id` | Tenant identifier string | Yes | All tenant-scoped endpoints |

### On Some Requests

| Header | Value | Required When | Notes |
|---|---|---|---|
| `Idempotency-Key` | Client-generated UUID | Tenant lifecycle transitions, POST /tenants | B02-004 |
| `X-Actor-Id` | Actor identifier | Some services (e.g., enrollment-service) | Default: "system" |
| `X-Correlation-Id` | Correlation UUID | RBAC authorize endpoint | Optional; passed through |
| `Content-Type` | `application/json` | All POST/PATCH/PUT | Standard |

### On Every Response

| Header | Value | Set By |
|---|---|---|
| `X-API-Version` | `v1` | All services via middleware (CAT-004) |
| `Content-Type` | `application/json` | All endpoints |
| `X-Content-Type-Options` | `nosniff` | FastAPI services via apply_security_headers() |
| `X-Frame-Options` | `DENY` | FastAPI services via apply_security_headers() |
| `Referrer-Policy` | `no-referrer` | FastAPI services via apply_security_headers() |
| `Cache-Control` | `no-store` | FastAPI services via apply_security_headers() |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | FastAPI services via apply_security_headers() |

---

## Authentication Contract

All non-exempt endpoints require a Bearer JWT in the Authorization header.

**Exempt paths (no auth required):**
```
/health
/metrics
/.well-known/jwks.json
/openapi.json
/docs
/docs/oauth2-redirect
/redoc
```

JWT validation behavior:
- FastAPI services: `require_jwt` dependency at app level validates all routes
- auth-service / checkout-service: manual JWT validation per request in handler

---

## Standard Endpoints (All Services)

Every service implements:

| Endpoint | Method | Response | Notes |
|---|---|---|---|
| `/health` | GET | `{"status": "ok", "service": "<name>"}` | No auth required |
| `/metrics` | GET | `{"service": "<name>", "service_up": 1, ...}` | Prometheus-style counters |

auth-service also exposes:
- `GET /.well-known/jwks.json` — RS256 public key in JWK format

---

## auth-service API (Base: `/api/v2/auth`)

| Path | Method | Description |
|---|---|---|
| `/sessions/login` | POST | Primary login endpoint |
| `/login` | POST | Compat alias for /sessions/login |
| `/tokens/refresh` | POST | Refresh token rotation |
| `/token/refresh` | POST | Compat alias for /tokens/refresh |
| `/token` | POST | Legacy session-based token issuance |
| `/sessions/validate` | POST | Validate session/token |
| `/sessions/logout` | POST | Single session logout |
| `/sessions/logout-all` | POST | Logout all sessions |
| `/sessions/logout_all` | POST | Alias (underscore) |
| `/sessions/revoke-all` | POST | Alias for logout_all |
| `/sessions/{session_id}/revoke` | POST | Targeted session revocation |
| `/sessions/{session_id}` | GET | Fetch session metadata |
| `/password/forgot` | POST | Initiate password reset |
| `/password/reset/request` | POST | Alias for forgot |
| `/password/reset` | POST | Complete password reset |
| `/password/reset/confirm` | POST | Alias for reset |
| `/password/policy/validate` | POST | Validate password against policy |
| `/tenant` | GET | Discover tenant by email domain |
| `/sso/initiate` | POST | SSO pre-auth flow (SAML/OIDC) |
| `/sso/callback` | POST | SSO assertion exchange |
| `/admin/users/{user_id}/reset-password` | POST | Admin-initiated password reset |

---

## rbac-service API (Base: `/api/v1/rbac`)

| Path | Method | Description |
|---|---|---|
| `/roles` | POST | Create role |
| `/roles` | GET | List roles |
| `/roles/{role_id}` | GET | Get role |
| `/roles/{role_id}` | PATCH | Update role |
| `/roles/{role_id}` | DELETE | Soft-delete role (sets status=disabled) |
| `/roles/{role_id}/permissions` | PUT | Replace role permissions |
| `/permissions` | GET | List all permissions |
| `/permissions/{permission_key}` | GET | Get permission |
| `/assignments` | POST | Create subject-role assignment |
| `/assignments` | GET | List assignments |
| `/assignments/{assignment_id}` | PATCH | Update assignment |
| `/assignments/{assignment_id}` | DELETE | Revoke assignment |
| `/subjects/{subject_type}/{subject_id}/effective-permissions` | GET | Compute effective permissions |
| `/authorize` | POST | Single permission check |
| `/authorize/batch` | POST | Batch permission check |
| `/policy-rules` | POST | Create policy rule |
| `/policy-rules` | GET | List policy rules |
| `/policy-rules/{policy_rule_id}` | PATCH | Update policy rule |
| `/policy-rules/{policy_rule_id}` | DELETE | Disable policy rule |
| `/audit-log` | GET | View authorization decisions (requires audit.view_tenant permission) |
| `/metrics` | GET | Service metrics |

---

## tenant-service API (Base: `/api/v1/tenants`)

| Path | Method | Description |
|---|---|---|
| `/validate` | POST | Pre-creation validation |
| `` (root) | POST | Create tenant (requires Idempotency-Key) |
| `/{tenant_id}/configuration` | PUT | Initialize configuration |
| `/{tenant_id}/configuration` | GET | Get configuration |
| `/{tenant_id}/configuration` | PATCH | Update configuration |
| `/{tenant_id}/feature-flags` | PATCH | Manage feature flags |
| `/{tenant_id}/lifecycle` | GET | Get lifecycle status |
| `/{tenant_id}/lifecycle/suspend` | POST | Suspend tenant (Idempotency-Key) |
| `/{tenant_id}/lifecycle/reactivate` | POST | Reactivate tenant (Idempotency-Key) |
| `/{tenant_id}/lifecycle/archive` | POST | Archive tenant (Idempotency-Key) |
| `/{tenant_id}/lifecycle/decommission` | POST | Decommission tenant (Idempotency-Key) |
| `/api/v1/isolation/evaluate` | POST | Evaluate isolation context |

---

## enrollment-service API (Base: `/api/v1/enrollments`)

| Path | Method | Status Code | Description |
|---|---|---|---|
| `` | POST | 201 | Create enrollment |
| `` | GET | 200 | List enrollments (filterable) |
| `/{enrollment_id}` | GET | 200 | Get enrollment |
| `/{enrollment_id}/links` | PATCH | 200 | Update cohort/session links |
| `/{enrollment_id}/transitions` | POST | 200 | Status transition (canonical) |
| `/{enrollment_id}/status-transitions` | POST | 200 | Alias for /transitions |
| `/bulk-assign` | POST | 202 | Bulk enrollment assignment |
| `/api/v1/audit-logs` | GET | 200 | Audit log |

Query parameters (list): `learner_id`, `course_id`, `status`, `cohort_id`, `session_id`, `page` (default 1), `page_size` (default 50, max 200)

---

## progress-service API (Base: `/api/v1/progress`)

| Path | Method | Status Code | Description |
|---|---|---|---|
| `/lessons/{lesson_id}/upsert` | POST | 200 | Upsert lesson progress |
| `/lessons/{lesson_id}/complete` | POST | 200 | Mark lesson complete |
| `/learners/{learner_id}` | GET | 200 | Learner progress summary |
| `/learners/{learner_id}/courses/{course_id}` | GET | 200 | Course-level progress |
| `/learning-paths/{learning_path_id}/assignments` | POST | 202 | Assign learning path |
| `/eligibility/courses/{course_id}/users/{user_id}` | GET | 200 | Certificate eligibility check |

---

## checkout-service API (Base: `/api/v1/checkout`)

| Path | Method | Description |
|---|---|---|
| `/sessions` | POST | Create checkout session |
| `/sessions/{session_id}` | GET | Get session |
| `/sessions/{session_id}/items` | POST | Update session items |
| `/sessions/{session_id}/submit` | POST | Submit session |
| `/orders/{order_id}` | GET | Get order |
| `/orders/{order_id}/initiate-payment` | POST | Initiate payment |

---

## Pagination Contract

Standard list response shape (observed in enrollment-service):

```json
{
  "items": [...],
  "page": 1,
  "page_size": 50,
  "total": 42
}
```

Note: `total` is currently a stub (returns `len(items)` not a true DB count). Per code comment: `# stub total; real impl would query count separately`

---

## RBAC Authorize Request/Response

Single authorization check:

Request:
```json
{
  "subject_type": "user",
  "subject_id": "usr_123",
  "permission_key": "course.publish",
  "resource_type": "course",
  "resource_id": "crs_456"
}
```

Response:
```json
{
  "decision": "allow",
  "reason_codes": [],
  "policy_trace": []
}
```

Batch authorization: `POST /authorize/batch` with `{"checks": [<AuthorizeRequest>, ...]}`

---

## Effective Permissions Response

```json
{
  "subject": {"type": "user", "id": "usr_123"},
  "tenant_id": "tnt_abc",
  "effective_permissions": [
    {"permission_key": "course.view"},
    {"permission_key": "course.enroll"}
  ],
  "computed_at": "2026-06-23T00:00:00Z"
}
```

---

## Tenant Isolation Rules

- All endpoints (except health/metrics/JWKS) require `X-Tenant-Id` header
- JWT `tenant_id` claim must match `X-Tenant-Id` header
- Cross-tenant reads and writes are rejected (403 or 401)
- `tenant_id` field in data models is immutable once set (PROHIBITED to change)

---

## Related Documents

- `docs/01_backend/ERROR_CONTRACT.md` — error response shapes
- `docs/01_backend/BACKEND_ARCHITECTURE.md` — service architecture
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — auth details
- `docs/specs/` — per-service engineering specifications (53 files)
