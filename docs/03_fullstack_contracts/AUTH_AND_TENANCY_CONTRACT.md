# AUTH_AND_TENANCY_CONTRACT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Cross-layer contract covering authentication, session management, and tenant isolation. This document is authoritative for both backend and frontend implementations. Backend derived from direct code inspection. Frontend verification is pending (Frontend Authority Capture not yet executed).

---

## Authentication Architecture

### JWT Token Issuance

**Issuing service**: `auth-service` (port 8104)

**Algorithm hierarchy**:
1. RS256 (primary) — requires `cryptography` Python package + `JWT_PRIVATE_KEY` env var (PEM-encoded RSA private key)
2. HS256 (fallback) — used when `cryptography` package unavailable or RSA key not provided
   - Fallback logs a warning: `"auth-service: RS256 signing unavailable — falling back to HS256"`
   - Fallback uses `JWT_SHARED_SECRET` env var

**JWKS endpoint**: `GET /.well-known/jwks.json` on auth-service
- Returns RSA public key in JWK format `{"keys": [{"kty": "RSA", "kid": "...", "alg": "RS256", "use": "sig", "n": "...", "e": "..."}]}`
- `kid` is derived from SHA-256 of the public key DER bytes (first 16 hex chars)
- If `JWT_PRIVATE_KEY` not set, an ephemeral in-process RSA key is used — tokens invalidated on restart

### JWT Claims (Standard)

| Claim | Set By | Description |
|---|---|---|
| `iat` | auth-service | Issued at (Unix timestamp) |
| `exp` | auth-service | Expiry (Unix timestamp) |
| `jti` | auth-service | JWT ID (UUID) — used for revocation |
| `iss` | auth-service | Issuer: `"lms-platform"` |
| `aud` | auth-service | Audience: `["lms.api"]` |
| `sid` | auth-service | Session ID (from `session_id` claim) |
| `tenant_id` | auth-service | Tenant the token belongs to |
| (business claims) | auth-service | user_id, roles[], etc. |

### JWT Token Validation (Consuming Services)

**Status (Task 7 — 2026-06-23)**: All 33 consuming services now support both RS256 and HS256. Algorithm is routed from the JWT header `alg` claim at validation time.

| Service | Validation Method | Algorithm Supported |
|---|---|---|
| rbac-service | `require_jwt` with alg-routing | RS256 + HS256 |
| tenant-service | `require_jwt` with alg-routing | RS256 + HS256 |
| progress-service | `require_jwt` with alg-routing | RS256 + HS256 |
| enrollment-service | `require_jwt` with alg-routing | RS256 + HS256 |
| checkout-service | Inline `_jwt_valid()` (stdlib handler) | HS256 only — no alg-routing in stdlib path |
| auth-service (self-validation) | `validate_token()` | RS256 + HS256 (both) |

**Algorithm routing**: `require_jwt()` peeks at JWT header `alg` claim → RS256 validates via `JWT_PUBLIC_KEY` env var (PEM); HS256 validates via `JWT_SHARED_SECRET`.
**Deployment requirement**: `JWT_PUBLIC_KEY` must be set in all service environments for RS256 to activate. Without it, RS256 tokens return `503 jwt_public_key_not_configured`.
**Canonical implementation**: `backend/services/shared/security.py`. Per-service `security.py` files all implement the same alg-routing pattern.
**Prior security debt (R-012)**: RESOLVED — see BACKEND_RISK_REGISTER.md RISK-004.

**`JWT_SHARED_SECRET` env var**: Required by all services for HS256 validation. If not set → 503 `jwt_secret_not_configured`.

---

## Session Model

### Session States

| State | Description |
|---|---|
| `active` | Not revoked, not expired |
| `revoked` | Explicitly revoked (logout or admin action) |
| `expired` | Past `expires_at` timestamp |

State computed by `Session.state` property:
```python
if self.revoked: return "revoked"
if datetime.now(timezone.utc) > self.expires_at: return "expired"
return "active"
```

### Session Fields

| Field | Description |
|---|---|
| `session_id` | Unique session identifier |
| `user_id` | User associated with session |
| `tenant_id` | Tenant isolation key |
| `issued_at` | Session creation time |
| `expires_at` | Access token expiry |
| `refresh_expires_at` | Refresh token expiry |
| `revoked` | Boolean flag |
| `auth_method` | `"password"`, `"sso"`, etc. |
| `assurance_level` | `"password"`, etc. |
| `last_seen_at` | Last activity |
| `revoked_at` | When revoked |
| `revoked_reason` | Why revoked |

### Session Storage

**Updated (Task 7 — 2026-06-23)**: Sessions are stored in `SQLiteAuthStore` (`backend/services/auth-service/app/store_db.py`). Sessions persist across auth-service restarts. SQLite is file-backed per-service; distributed multi-replica deployments still require a shared session store (e.g., Redis) for session consistency across replicas.

---

## Login Flow

### Primary Login

`POST /api/v2/auth/sessions/login` (compat: `/api/v2/auth/login`)

Request:
```json
{
  "tenant_id": "tnt_123",
  "identifier": "user@example.com",
  "password": "***"
}
```

Response (200) — *corrected from code inspection (auth-service/app/service.py:144–152)*:
```json
{
  "session_id": "ses_123",
  "user": {
    "user_id": "usr_123",
    "tenant_id": "tnt_123"
  },
  "access_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "<rt>",
  "refresh_expires_in": 604800
}
```

**CRITICAL NOTES for frontend**:
- `user_id` and `tenant_id` are nested under the `"user"` sub-object — NOT at the top level.
- `roles` is NOT in the login response — roles are only in the JWT payload.
- `refresh_expires_in` (7 days = 604800 s) is present but was previously undocumented.
- JWT user identifier is in the standard `sub` claim, not a `user_id` claim. Frontend must read `payload.sub`.

### Token Refresh

`POST /api/v2/auth/tokens/refresh` (compat: `/api/v2/auth/token/refresh`)

### Session Validation

`POST /api/v2/auth/sessions/validate`

### Logout (Single Session)

`POST /api/v2/auth/sessions/logout`
`POST /api/v2/auth/sessions/{session_id}/revoke`

### Logout (All Sessions)

`POST /api/v2/auth/sessions/logout-all` (or `logout_all`, `revoke-all`)

---

## Tenant Isolation Contract

Tenant isolation is the primary security boundary. It operates at two levels:

### Level 1: Header Enforcement

Every request to every tenant-scoped endpoint must include:
```
X-Tenant-Id: <tenant_id>
```

Enforced by dependency injection (FastAPI services) or manual check (stdlib services).

### Level 2: JWT Claim Validation

The `tenant_id` in the JWT payload must match the `X-Tenant-Id` header:

| Service | Error Code | HTTP Status |
|---|---|---|
| rbac-service (via require_tenant_scope) | `tenant_mismatch` | 403 |
| enrollment-service (inline) | `tenant_header_jwt_mismatch` | 401 |
| progress-service (inline) | `tenant_mismatch` | 400 |

**Immutability rule**: `tenant_id` is immutable on all data models after creation. Governed as PROHIBITED to remove per DECISION_ESCALATION_MATRIX.

### Lifecycle-Gated Isolation

- `SUSPENDED` tenants: cannot create sessions or write data
- `ARCHIVED` / `DECOMMISSIONED` tenants: immutable — no reads or writes
- Cross-tenant writes: always denied

---

## Tenant Discovery (Pre-Login SSO)

`GET /api/v2/auth/tenant?domain=<email_domain>`

Returns tenant metadata for the email domain — used to route the user to the correct tenant's login page.

---

## SSO Contract

### Initiation

`POST /api/v2/auth/sso/initiate`

```json
{
  "tenant_id": "tnt_123",
  "provider_type": "saml" | "oidc",
  "redirect_uri": "https://...",
  "correlation_id": "optional-uuid"
}
```

### Callback

`POST /api/v2/auth/sso/callback`

```json
{
  "tenant_id": "tnt_123",
  "provider_type": "saml" | "oidc",
  "code_or_assertion": "<saml_assertion_or_oidc_code>",
  "correlation_id": "uuid"
}
```

---

## Canonical Tenant Contract (from `docs/anchors/tenant-contract.md`)

6-field tenant model (PROTECTED — do not change without owner approval):

| Field | Description |
|---|---|
| `tenant_id` | Primary isolation key |
| `name` | Display name |
| `active` | Boolean active state |
| `domain` | Optional email domain for SSO routing |
| (2 additional fields per anchor) | See docs/anchors/tenant-contract.md |

---

## Admin Password Reset

`POST /api/v2/admin/users/{user_id}/reset-password`

Admin-initiated reset — bypasses forgot-password email flow.

---

## Password Reset Flow

1. `POST /api/v2/auth/password/forgot` — sends reset token to user's email
2. `POST /api/v2/auth/password/reset` — consumes token, sets new password

Reset challenge model:
- Token hashed before storage (`challenge_hash` field)
- Max 5 attempts before challenge invalidated
- Delivery via `email` (default) or other channel

---

## Security Headers

All FastAPI auth-adjacent services set via `apply_security_headers()`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Cache-Control: no-store`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`

---

## Open Issues

| ID | Issue | Risk |
|---|---|---|
| RISK-006 | RS256/HS256 mismatch — consuming services validate HS256 but auth may issue RS256 | HIGH |
| RISK-007 | Ephemeral RSA key on restart — all RS256 tokens invalidated | MEDIUM |
| RISK-008 | JWT_PRIVATE_KEY required in production for stable RS256 | HIGH |
| RISK-003 | Sessions in InMemoryAuthStore — lost on restart | HIGH |

---

## Related Documents

- `docs/anchors/tenant-contract.md` — canonical 6-field tenant contract (PROTECTED)
- `docs/anchors/capability-resolution.md` — capability gating
- `docs/designs/auth-rsa-key-design.md` — RSA key design decisions
- `docs/03_fullstack_contracts/USER_ROLES_AND_PERMISSIONS.md` — RBAC contract
- `docs/08_reports/SECURITY_DISCOVERY_REPORT.md` — security findings
