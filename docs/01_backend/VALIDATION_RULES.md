# VALIDATION_RULES

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Documents all validation rules implemented in `backend/services/` as found in the code. Covers authentication rules, tenant isolation rules, business validation, and password policy.

---

## Authentication and Authorization Rules

### JWT Validation (FastAPI services — require_jwt)

1. Endpoint path must not be in exempt list (`/health`, `/metrics`, `/openapi.json`, `/docs`, `/redoc`, `/.well-known/jwks.json`)
2. `JWT_SHARED_SECRET` environment variable must be set (else 503)
3. Authorization header must be present and start with `Bearer ` (else 401)
4. Token must split into exactly 3 parts by `.` (else 401 malformed_jwt)
5. HS256 signature must match (using `JWT_SHARED_SECRET`) — see NOTE on RS256 below
6. Token `exp` claim must not be in the past (else 401 token_expired)
7. If `is_jti_revoked` callback provided and JTI is revoked (else 401 token_revoked)

**NOTE**: rbac-service `require_jwt` validates HS256 only. auth-service issues RS256 (with HS256 fallback). Services that only validate HS256 cannot accept RS256 tokens. This is tracked security debt (R-012).

### Tenant Scope Validation (require_tenant_scope — rbac-service)

1. JWT payload must contain `tenant_id` claim
2. `X-Tenant-Id` header must be present and non-empty
3. JWT `tenant_id` claim must exactly equal `X-Tenant-Id` header value (else 403 tenant_mismatch)

### Tenant Validation (enrollment-service inline)

1. Decode JWT payload (best-effort, no signature re-check here — require_jwt already validated)
2. Extract `tenant_id` or `tid` from JWT payload
3. If JWT tenant claim present AND `X-Tenant-Id` header present AND they differ → 401 tenant_header_jwt_mismatch
4. If JWT parse fails silently → pass (JWT middleware already validated)

---

## Password Policy (auth-service)

Rule set for `POST /api/v2/auth/password/policy/validate`:

| Rule | Violation Code | Description |
|---|---|---|
| Minimum length | `min_length_8` | Password must be at least 8 characters |
| Uppercase required | `requires_uppercase` | At least one uppercase character |
| Digit required | `requires_digit` | At least one numeric digit |

Response:
```json
{"valid": false, "violations": ["min_length_8", "requires_uppercase"]}
{"valid": true, "violations": []}
```

Password hashing rules:
1. Argon2id used when `argon2-cffi` package installed (time_cost=3, memory_cost=65536, parallelism=2)
2. Falls back to PBKDF2-HMAC-SHA256 (200,000 iterations) if argon2-cffi unavailable
3. Legacy PBKDF2 hashes accepted during migration (backwards compatible verification)

---

## Tenant Creation Validation (tenant-service)

Fields validated by `validate_tenant_creation`:
- `name` — non-empty string
- `country_code` — must be a supported country code
- `segment_type` — must be a recognized segment
- `plan_type` — must be a recognized plan
- `addon_flags` — list of valid addon identifiers

Returns: `{"validation_passed": bool, "errors": [...]}`

Idempotency requirements:
- `POST /api/v1/tenants` — requires `Idempotency-Key` header (B02-004)
- All lifecycle transitions (suspend, reactivate, archive, decommission) — require `Idempotency-Key` header

---

## Enrollment Validation

| Rule | Error | HTTP |
|---|---|---|
| Learner not already enrolled in course | `already_enrolled` | 409 |
| Expected version matches current version | `version_conflict` | 409 |
| Enrollment must be active for progress update | `enrollment_inactive` | 409 |
| Status transitions must be valid per state machine | (ValidationError message) | 422 |

---

## RBAC Validation

| Rule | Error | HTTP |
|---|---|---|
| Role must exist for GET/PATCH/DELETE | `role_not_found` | 404 |
| Permission must exist for GET | `permission_not_found` | 404 |
| Role deletion is soft-delete (sets disabled) — hard delete not permitted | N/A | Business rule |
| Policy rule deletion is soft-disable — hard delete not permitted | N/A | Business rule |

---

## Progress Validation

| Rule | Error | HTTP |
|---|---|---|
| `X-Tenant-Id` header must match `request.tenant_id` body field | `tenant_mismatch` | 400 |
| Course progress must exist for eligibility check | Returns `eligible=false`, status `not_started` | 200 (no 404) |

---

## Config Resolution Validation (shared/models/config.py)

| Rule | Enforced By |
|---|---|
| `scope_id` must not be blank | `ConfigScope.__post_init__` raises ValueError |
| Global config must have `scope_id="global"` | `ConfigOverride.__post_init__` raises ValueError |
| ConfigLevel must be GLOBAL, COUNTRY, SEGMENT, or TENANT | Python Enum (only 4 values) |

---

## Session Validation (auth-service)

1. Session retrieved by session_id must exist (else 404 session_not_found)
2. Session state: `active` (not revoked, not expired), `revoked`, `expired`
3. Revoked sessions cannot be used for authorization

---

## Request Body Rules (All Services)

- `Content-Type: application/json` expected for POST/PATCH/PUT
- FastAPI services: Pydantic schema validation at binding time → 422 on schema mismatch
- Stdlib services: manual `json.loads()` → 400 on `json.JSONDecodeError`

---

## Immutable Fields (Cross-Cutting Rule)

| Field | Rule | Enforcement |
|---|---|---|
| `tenant_id` on any model | Never changes after creation | PROHIBITED per governance |
| `assignment_id` | Immutable once created | Business invariant |
| `session_id` | Immutable once issued | Business invariant |

---

## Fields Referenced from JWT Claims

| JWT Field | Alias | Used By |
|---|---|---|
| `tenant_id` | `tid` (fallback) | enrollment-service tenant validation |
| `tenant_id` | — | rbac-service require_tenant_scope |
| `exp` | — | All services (token expiry) |
| `jti` | — | auth-service revocation check |
| `iss` | — | Defaults to "lms-platform" |
| `aud` | — | Defaults to ["lms.api"] |
| `sid` | — | Set from `session_id` claim |

---

## Related Documents

- `docs/01_backend/API_CONTRACT.md` — endpoint definitions
- `docs/01_backend/ERROR_CONTRACT.md` — error codes
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — full auth contract
- `docs/03_fullstack_contracts/VALIDATION_PARITY.md` — backend/frontend validation alignment
