# SECURITY_DISCOVERY_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture

Source: Direct code inspection of backend/services/

---

## Purpose

Security findings from Phase 2 Backend Authority Capture. Documents the implemented security posture as-found. Not a penetration test — these are observations from source code inspection.

---

## Authentication Implementation

### JWT Signing

| Service | Signing Algorithm | Validation Algorithm | Notes |
|---|---|---|---|
| auth-service (issue) | RS256 (primary), HS256 (fallback) | RS256 + HS256 both handled | Falls back to HS256 if `cryptography` package unavailable |
| auth-service (self-validate) | — | RS256 + HS256 | `validate_token()` handles both |
| rbac-service | — | RS256 + HS256 | `_validate_rs256_jwt()` + alg-routing added (Task 7) |
| checkout-service | — | HS256 only | Inline `_jwt_valid()` — stdlib handler, no alg-routing |
| tenant-service | — | RS256 + HS256 | alg-routing added (Task 7) |
| progress-service | — | RS256 + HS256 | alg-routing added (Task 7) |
| enrollment-service | — | RS256 + HS256 | alg-routing added (Task 7) |

**Security debt (R-012): RESOLVED (Task 7 — 2026-06-23).** 33 consuming services updated. All use JWT header `alg` claim routing: RS256 → `JWT_PUBLIC_KEY`; HS256 → `JWT_SHARED_SECRET`. Canonical implementation at `backend/services/shared/security.py`.

### JWT Secret Management

- `JWT_SHARED_SECRET` env var required by all services for HS256 validation
- `JWT_PRIVATE_KEY` env var required by auth-service for stable RS256 signing
- If `JWT_PRIVATE_KEY` not set: ephemeral RSA key generated at startup (development mode)
- `get_required_secret("JWT_SHARED_SECRET")` in auth-service raises `SecretConfigurationError` (→ 503) if not set

### RSA Key Characteristics

- Algorithm: RSA 2048 bits
- Signing padding: PKCS1v15
- Hash: SHA-256
- `kid`: SHA-256 of DER-encoded public key, first 16 hex chars
- JWKS published at: `GET /.well-known/jwks.json`

---

## Password Security

### Hashing Algorithm

| Algorithm | When Used | Parameters |
|---|---|---|
| Argon2id | Primary — when `argon2-cffi` package installed | time_cost=3, memory_cost=65536 KiB (64 MB), parallelism=2 |
| PBKDF2-HMAC-SHA256 | Fallback — when argon2-cffi unavailable | 200,000 iterations |

**Note**: PBKDF2 is used as fallback. Production should ensure `argon2-cffi` is installed. Legacy PBKDF2 hashes are verified during migration window.

Password storage: `password_hash` field on `UserCredential`. Argon2id hashes prefixed with `"argon2:"`.

### Password Policy

Enforced by `POST /api/v2/auth/password/policy/validate`:
- Minimum 8 characters
- At least one uppercase character
- At least one numeric digit

**Note**: Password policy validation is an advisory endpoint (client submits password for validation). Whether the policy is also enforced server-side on actual password set operations must be verified in auth-service service.py.

---

## Tenant Isolation

| Control | Implemented | Notes |
|---|---|---|
| `X-Tenant-Id` header required | Yes — all services | JWT + header must match |
| JWT `tenant_id` claim validation | Yes — all inspected services | Mismatch → 401/403 |
| Cross-tenant data filtering | Yes — all stores filter by tenant_id | In-memory stores filter by tenant |
| SUSPENDED tenant write block | Yes — tenant-service enforces | State machine checked |
| ARCHIVED/DECOMMISSIONED immutability | Yes — tenant-service enforces | No writes permitted |

Tenant isolation is PROHIBITED to remove per governance.

---

## Security Headers

All FastAPI services apply via `apply_security_headers(app)`:

| Header | Value | Status |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Implemented |
| `X-Frame-Options` | `DENY` | Implemented |
| `Referrer-Policy` | `no-referrer` | Implemented |
| `Cache-Control` | `no-store` | Implemented |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | Implemented |

**Note**: auth-service and checkout-service use stdlib `http.server` and set headers manually on responses. They do not go through `apply_security_headers()`. Verify that all stdlib service responses include these headers.

---

## Session Security

| Control | Implemented | Notes |
|---|---|---|
| Session revocation | Yes — STORE.get_session → check revoked flag | Targeted and global revocation |
| Session expiry | Yes — `expires_at` checked in `state` property | |
| Refresh token rotation | Yes — endpoint at `/tokens/refresh` | |
| Reset challenge: token hashing | Yes — `challenge_hash` stored, not plain token | Delivery channel configurable |
| Reset challenge: attempt limiting | Yes — `max_attempts=5` on `ResetChallenge` | |
| JTI revocation | Yes — `is_jti_revoked` callback in `validate_token()` | |

**Gap**: Sessions in `InMemoryAuthStore` — revocation list also in-memory. Restart clears revocation state.

---

## RBAC Security Controls

| Control | Implemented | Notes |
|---|---|---|
| Audit log for authorization decisions | Yes — `AuthorizationDecisionLog` | Includes `decision`, `reason_codes`, `policy_trace` |
| Audit log access control | Yes — requires `audit.view_tenant` permission | Checked via `build_authorization_dependency` |
| Explicit deny | Yes — `effect="deny"` on RolePermissionBinding | |
| Separation of Duties rules | Yes — `RuleType.SOD_CONFLICT` policy rule | |
| Step-up auth enforcement | Yes — `RuleType.STEP_UP_REQUIRED` | Evaluation logic in service.py |
| Time-window access | Yes — `RuleType.TIME_WINDOW` | |
| Network boundary | Yes — `RuleType.NETWORK_BOUNDARY` | |
| Role soft-delete only | Yes — DELETE sets `status=disabled` | Hard deletion not implemented |
| Branch scope isolation | Yes — `branch_ids[]` for BRANCH scope | BC-BRANCH-01 / MO-026 |

---

## Checkout / Payment Security

| Control | Implemented | Notes |
|---|---|---|
| Idempotency check on submit | Yes — `CheckoutService.submit_session()` | PROHIBITED to remove per governance |
| JWT validation | Yes — inline `_jwt_valid()` in checkout-service | HS256 only |
| Tenant header enforcement | Yes — `X-Tenant-Id` read from request | |

**Note**: `_jwt_valid()` in checkout-service returns `True` if `JWT_SHARED_SECRET` env var is not set (fails open). This is a security gap in the fallback behavior.

---

## Security Findings Summary

| Finding | Severity | Type |
|---|---|---|
| RS256/HS256 algorithm mismatch between issuer and validators | HIGH | Token security |
| Ephemeral RSA key on restart (if JWT_PRIVATE_KEY not set) | HIGH | Key management |
| Sessions in-memory — revocation state lost on restart | HIGH | Session management |
| checkout-service `_jwt_valid()` returns `True` if secret not configured | HIGH | Auth bypass risk |
| Argon2id package may not be installed (PBKDF2 fallback) | MEDIUM | Password security |
| stdlib services may not apply full security header set | MEDIUM | Response headers |
| Password policy validate endpoint is advisory only | LOW | Policy enforcement |
| No rate limiting found in any service | MEDIUM | Brute force risk |
| No CORS configuration found during inspection | MEDIUM | Browser security |

---

## Not Inspected

The following security areas were not directly inspected during Phase 2:

- API gateway authentication/rate limiting (`infrastructure/api-gateway/`)
- Observability security (`infrastructure/observability/`)
- TLS/mTLS configuration (deployment-level)
- Secrets management infrastructure (env var injection mechanism)
- Network segmentation between services
- Node.js services (prerequisite-engine-service, scorm-service)

---

## Related Documents

- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — auth contract
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk register
- `docs/designs/auth-rsa-key-design.md` — RSA key design
- `workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md` — security blockers
