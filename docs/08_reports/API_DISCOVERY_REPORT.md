# API_DISCOVERY_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture

Source: Direct code inspection of backend/services/

---

## Purpose

Detailed findings from Phase 2 API discovery. Documents the API landscape as-implemented: versioning, authentication flow, routing patterns, and notable deviations from spec.

---

## API Versioning Reality

### Observed Patterns

| Pattern | Services | Notes |
|---|---|---|
| `/api/v1/<resource>` | Most services (enrollment, progress, rbac, tenant, etc.) | Primary active path |
| `/api/v2/auth/<resource>` | auth-service | auth-service uses v2 natively — not via rewrite |
| `/api/v2/<resource>` accepted → rewrites to `/api/v1/` | enrollment-service only | Middleware path rewrite |
| `/api/v1/` and `/api/v2/auth/` on same service | auth-service admin path | `/api/v2/admin/users/{id}/reset-password` |

**Finding**: Version consistency is mixed. auth-service uses v2; all others use v1. Only enrollment-service implements a v2 compat rewrite. This creates a versioning inconsistency that frontend must handle.

### Response Header

`X-API-Version: v1` is set on every response by every service (via middleware in FastAPI, manual in stdlib services). This is compliant with CAT-004.

---

## HTTP Server Implementation Gap

| Service | Implementation | Registered As |
|---|---|---|
| auth-service | Python stdlib `http.server.BaseHTTPRequestHandler` | `app.main:app` in manifest |
| checkout-service | Python stdlib `http.server.BaseHTTPRequestHandler` | `app.main:app` in manifest |
| All others | FastAPI (ASGI) | `app.main:app` in manifest |

**Finding**: auth-service and checkout-service use synchronous stdlib HTTP server, not FastAPI. This means:
1. No Pydantic automatic request validation (manual JSON parsing only)
2. No FastAPI automatic OpenAPI docs at `/docs`
3. No ASGI compatibility — uvicorn cannot start these as `app.main:app`
4. Manual routing via `if self.path == "..."` dispatch

---

## Routing Patterns

### FastAPI Services

Standard FastAPI path decorators:
```python
@app.get("/api/v1/resource/{id}")
@app.post("/api/v1/resource")
@app.patch("/api/v1/resource/{id}")
@app.delete("/api/v1/resource/{id}")
@app.put("/api/v1/resource/{id}/sub-resource")
```

All routes are versioned: `/api/v1/` prefix.

### Stdlib Services (auth, checkout)

Manual dispatch in `_dispatch()`:
```python
if self.path in ("/api/v2/auth/sessions/login", "/api/v2/auth/login"):
    return SERVICE.login(...)
if self.path.startswith("/api/v2/auth/sessions/") and self.path.endswith("/revoke"):
    # extract path segment
```

Path matching uses exact string comparison or `str.startswith()` + `str.endswith()`.

---

## Compatibility Aliases

Several services maintain legacy path aliases alongside canonical paths:

| Canonical Path | Alias(es) | Service |
|---|---|---|
| `/api/v2/auth/sessions/login` | `/api/v2/auth/login` | auth-service |
| `/api/v2/auth/tokens/refresh` | `/api/v2/auth/token/refresh` | auth-service |
| `/api/v2/auth/password/forgot` | `/api/v2/auth/password/reset/request` | auth-service |
| `/api/v2/auth/password/reset` | `/api/v2/auth/password/reset/confirm` | auth-service |
| `/api/v2/auth/sessions/logout-all` | `/api/v2/auth/sessions/logout_all` (underscore), `/api/v2/auth/sessions/revoke-all` | auth-service |
| `/api/v1/enrollments/{id}/transitions` | `/api/v1/enrollments/{id}/status-transitions` | enrollment-service |
| `/api/v2/enrollments/*` | rewrites to `/api/v1/enrollments/*` | enrollment-service middleware |

**AUD references**: AUD-001 (login canonical), AUD-002 (token refresh), AUD-003 (underscore alias), AUD-009 (transitions canonical), AUD-052.

---

## Standard Endpoint Inventory

### auth-service (`/api/v2/auth`)

24 endpoint paths (including aliases). Key paths:
- Login, token refresh, session validate, logout, revoke, forgot/reset password
- Admin password reset, password policy validate
- SSO initiate, SSO callback, tenant discovery
- Session CRUD (GET session, revoke session)
- JWKS at `/.well-known/jwks.json`

### rbac-service (`/api/v1/rbac`)

20 endpoints. Roles, permissions, assignments, policy rules, authorize, audit log.

### tenant-service (`/api/v1/tenants`)

11 endpoints. Create, configure, feature flags, lifecycle transitions (suspend/reactivate/archive/decommission), isolation evaluation.

### enrollment-service (`/api/v1/enrollments`)

8 endpoints. CRUD, bulk-assign, status-transitions, audit logs.

### progress-service (`/api/v1/progress`)

6 endpoints. Lesson upsert/complete, learner summary, course progress, learning path assignment, certificate eligibility.

### checkout-service (`/api/v1/checkout`)

6 endpoints. Session CRUD + items, submit, order GET, initiate-payment.

---

## Authentication Flow

All non-exempt endpoints require:
1. `Authorization: Bearer <jwt>` header
2. `X-Tenant-Id: <tenant_id>` header
3. JWT `tenant_id` claim must match `X-Tenant-Id`

Exempt paths (no auth required):
- `/health`, `/metrics`, `/.well-known/jwks.json`, `/openapi.json`, `/docs`, `/redoc`

---

## Notable API Design Patterns

### Idempotency

`Idempotency-Key` header required for tenant lifecycle transitions and tenant creation (B02-004 compliance).

### Pagination

Standard list response: `{"items": [...], "page": N, "page_size": N, "total": N}`
`total` is a stub in enrollment-service (returns current page length, not true count).

### 202 Accepted for Async Operations

Used by:
- `POST /api/v1/enrollments/bulk-assign` — job_id + accepted/rejected counts
- `POST /api/v1/progress/learning-paths/{id}/assignments` — async assignment

### Soft Delete Pattern

Used by rbac-service: DELETE sets `status=disabled` (role) or `enabled=false` (policy rule). No hard deletes.

### Optimistic Locking

enrollment-service uses `version` field for optimistic concurrency:
```json
{"expected_version": 3}
```
Returns 409 `version_conflict` if mismatch.

---

## No OpenAPI in Stdlib Services

auth-service and checkout-service do not expose:
- `/openapi.json`
- `/docs` (Swagger UI)
- `/redoc`

FastAPI services expose all three automatically.

---

## API Completeness Assessment

| Service | Has Spec | Has Implementation | Spec ↔ Impl Match |
|---|---|---|---|
| auth-service | Yes (auth-service-spec.md) | Yes | Partial — spec describes persistent entities; impl is in-memory |
| rbac-service | Yes | Yes | Largely aligned |
| tenant-service | Yes (tenant-service-spec.md) | Yes | Largely aligned |
| enrollment-service | Yes | Yes | Largely aligned |
| progress-service | Yes | Yes | Largely aligned |
| checkout-service | No specific spec found | Yes | Unknown alignment |
| ~25 other services | No | Yes | Unknown |

Full spec coverage: approximately 40 of 69 services have specs. 29 services have no spec (GAP-014). *(count corrected from 65 → 69 — 2026-06-23)*

---

## Related Documents

- `docs/01_backend/API_CONTRACT.md` — authoritative API contract
- `docs/01_backend/ERROR_CONTRACT.md` — error shapes
- `docs/01_backend/SERVICE_CATALOG.md` — service list
- `docs/08_reports/BACKEND_GAP_REGISTER.md` — GAP-004, GAP-007, GAP-014
- `docs/specs/` — engineering specifications (73 files)
