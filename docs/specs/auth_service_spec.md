> **DEPRECATED** — Superseded by: `docs/specs/SPEC_01_auth_service.md`
> Reason: SPEC_ prefixed doc is the canonical spec. This legacy spec is retained for historical reference only.
> Last reviewed: 2026-04-04

# Auth Service Engineering Specification (GEN_01_auth_service)

## 1) Service Purpose and Boundary

`auth_service` is the authentication and session-security domain for Enterprise LMS V2. It extends the existing Rails LMS identity model centered on `User` by *referencing* user identity records, while avoiding ownership of user profile data, RBAC policy logic, and tenant source-of-truth data.

### In-scope responsibilities
- Credential and assertion authentication (`password`, federated assertion exchange hooks).
- Session lifecycle management (issue, refresh, revoke, expire, validate).
- Access token and refresh token issuance/validation.
- Password reset challenge flow and secure completion.
- Login/security audit trail.
- Auth lifecycle event publication.
- Health and observability instrumentation for auth pathways.

### Explicit non-goals (hard constraints)
- Does **not** own user profile lifecycle fields (`first_name`, `department`, `manager_id`, etc.).
- Does **not** own RBAC policy evaluation or role assignment decisions.
- Does **not** own tenant definitions or tenant status authority.
- Does **not** perform shared database writes into user, RBAC, or tenant service databases.
- Cross-service interaction only via API calls and event publication/consumption.

---

## 2) Rails LMS Compatibility Strategy

`auth_service` remains compatible with the existing Rails LMS identity model by preserving stable identifiers and claim contracts.

### Compatibility guarantees
- Uses `user_id` as the immutable subject key in all tokens/events.
- Uses `tenant_id` as mandatory context for every auth command/query.
- Resolves user/account status from `user_service` API before issuing active session credentials.
- Keeps token claim names backward-compatible with current LMS integrations: `sub`, `tid`, `sid`, `scp`, `iat`, `exp`, `iss`, `aud`.
- Supports existing login primitives:
  - username/email + password
  - SSO assertion exchange (OIDC/SAML brokered by dedicated integration endpoints)

---

## 3) Service Module Structure

```text
auth_service/
  app/
    api/
      v1/
        auth_controller.rb
        sessions_controller.rb
        tokens_controller.rb
        passwords_controller.rb
        health_controller.rb
    middleware/
      tenant_context_middleware.rb
      authentication_middleware.rb
      correlation_middleware.rb
    domain/
      models/
        auth_session.rb
        refresh_token.rb
        password_reset_challenge.rb
        auth_audit_event.rb
      value_objects/
        token_claim_set.rb
        tenant_context.rb
      services/
        authenticate_user.rb
        issue_token_pair.rb
        validate_token.rb
        rotate_refresh_token.rb
        revoke_session.rb
        initiate_password_reset.rb
        complete_password_reset.rb
    infra/
      repositories/
        auth_session_repository.rb
        refresh_token_repository.rb
        password_reset_repository.rb
        audit_log_repository.rb
      crypto/
        jwt_signer.rb
        secret_hasher.rb
      events/
        event_publisher.rb
      observability/
        metrics.rb
        tracing.rb
    clients/
      user_service_client.rb
      tenant_service_client.rb
      rbac_service_client.rb
    config/
      routes.rb
      initializers/
        telemetry.rb
        key_rotation.rb
  spec/
    requests/
    domain/
    contract/
    integration/
```

---

## 4) Versioned REST API Routes

Base path: `/api/v1/auth`

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/auth/login` | `POST` | Authenticate principal and create session/token pair. |
| `/api/v1/auth/token` | `POST` | Issue token pair using grant (`refresh_token`, `client_credentials`, `assertion_exchange`). |
| `/api/v1/auth/token/validate` | `POST` | Validate token signature, expiry, revocation, tenant binding. |
| `/api/v1/auth/sessions/{session_id}` | `GET` | Retrieve session metadata (tenant scoped). |
| `/api/v1/auth/sessions/{session_id}/revoke` | `POST` | Revoke one session and associated refresh lineage. |
| `/api/v1/auth/sessions/revoke-all` | `POST` | Revoke all active sessions for `user_id` in tenant. |
| `/api/v1/auth/password/forgot` | `POST` | Initiate reset challenge workflow. |
| `/api/v1/auth/password/reset` | `POST` | Complete reset challenge with new password. |
| `/api/v1/auth/password/policy/validate` | `POST` | Validate candidate password against policy controls. |
| `/api/v1/auth/health` | `GET` | Liveness/readiness details for auth dependencies. |

---

## 5) Request/Response Schemas

## 5.1 Common envelope requirements
- Required header: `X-Tenant-ID` (must match token/request body tenant, or reject `403`).
- Required header: `X-Correlation-ID` (generated if absent, echoed in response).
- Required header for protected routes: `Authorization: Bearer <access_token>`.

### Standard error schema
```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "Credentials rejected.",
    "correlation_id": "corr-123",
    "details": {"remaining_attempts": 2}
  }
}
```

## 5.2 Login (`POST /api/v1/auth/login`)

**Request**
```json
{
  "tenant_id": "tenant-acme",
  "identifier": "ava.stone@acme.edu",
  "secret": "PlaintextOnlyOverTLS",
  "auth_method": "password",
  "device": {
    "ip": "203.0.113.10",
    "user_agent": "Mozilla/5.0",
    "device_id": "web-1"
  }
}
```

**Response 200**
```json
{
  "session_id": "ses_01J9...",
  "token_type": "Bearer",
  "access_token": "eyJ...",
  "expires_in": 900,
  "refresh_token": "rfr_01J9...",
  "refresh_expires_in": 1209600,
  "tenant_id": "tenant-acme",
  "subject": {
    "user_id": "usr_321",
    "status": "active"
  }
}
```

## 5.3 Token validation (`POST /api/v1/auth/token/validate`)

**Request**
```json
{
  "tenant_id": "tenant-acme",
  "token": "eyJ...",
  "expected_audience": "lms-api"
}
```

**Response 200**
```json
{
  "active": true,
  "claims": {
    "sub": "usr_321",
    "tid": "tenant-acme",
    "sid": "ses_01J9...",
    "scp": ["lms.read"],
    "exp": 1732542000
  }
}
```

## 5.4 Forgot password (`POST /api/v1/auth/password/forgot`)

Always returns `202` to avoid account enumeration.

---

## 6) Domain Models

## 6.1 `AuthSession`
- Keys: `session_id`, `tenant_id`, `user_id`.
- State: `active`, `revoked`, `expired`.
- Fields: `issued_at`, `expires_at`, `last_seen_at`, `auth_method`, `assurance_level`, `client_id`, `ip_hash`, `user_agent_hash`, `revoked_at`, `revoked_reason`.

## 6.2 `RefreshToken`
- Keys: `token_id`, `session_id`, `tenant_id`, `user_id`.
- Rotation lineage: `parent_token_id`, `replaced_by_token_id`.
- Fields: `hashed_secret`, `issued_at`, `expires_at`, `used_at`, `revoked_at`, `revocation_reason`.

## 6.3 `PasswordResetChallenge`
- Keys: `challenge_id`, `tenant_id`, `user_id`.
- Fields: `challenge_hash`, `delivery_channel`, `requested_at`, `expires_at`, `consumed_at`, `attempt_count`, `max_attempts`, `request_ip_hash`.

## 6.4 `AuthAuditEvent`
- Keys: `event_id`, `tenant_id`, `timestamp`.
- Fields: `event_type`, `severity`, `actor_user_id`, `subject_user_id`, `session_id`, `result`, `reason_code`, `correlation_id`, `trace_id`, `metadata` (json).

---

## 7) Service Logic (Critical Flows)

## 7.1 Authentication flow
1. Resolve tenant context from `X-Tenant-ID`; reject missing/invalid tenant.
2. Rate-limit login attempts by tenant + identifier + IP.
3. Fetch identity/auth eligibility from `user_service` (`active`, `not_locked`, `not_terminated`).
4. Verify credential (bcrypt/argon2id hash) or assertion exchange.
5. Create `AuthSession`; issue short-lived access token + rotating refresh token.
6. Write immutable audit record.
7. Publish `auth.login.succeeded` or `auth.login.failed` event.

## 7.2 Refresh flow
1. Validate refresh token hash and lineage state.
2. Enforce one-time use rotation (replay == revoke session chain).
3. Issue new pair, revoke prior refresh token node.
4. Emit `auth.token.refreshed` event and trace span.

## 7.3 Password reset flow
1. Accept forgot request without leaking user existence.
2. Create one-time challenge; send via out-of-band notifier integration.
3. Validate challenge + policy + anti-replay checks.
4. Call `user_service` credential endpoint (API) to update password hash ownership boundary.
5. Revoke all existing sessions post-reset.
6. Publish `auth.password.reset.completed`.

---

## 8) Storage Contract (Auth-owned datastore only)

No writes are allowed to shared or external service databases.

### Auth-owned tables
- `auth_sessions`
- `auth_refresh_tokens`
- `auth_password_reset_challenges`
- `auth_audit_log`
- `auth_outbox_events`

### Required indexes
- `auth_sessions (tenant_id, user_id, state)`
- `auth_refresh_tokens (tenant_id, token_fingerprint)` unique
- `auth_password_reset_challenges (tenant_id, challenge_hash)` unique
- `auth_audit_log (tenant_id, timestamp desc)`

### Retention
- Audit log: 400 days hot + archive.
- Session metadata: 90 days.
- Reset challenges: 30 days.

---

## 9) Event Definitions (Published)

Envelope fields for all events:
`event_id`, `event_type`, `timestamp`, `tenant_id`, `subject_user_id`, `actor_user_id`, `correlation_id`, `trace_id`, `schema_version`, `payload`.

- `auth.login.succeeded`
- `auth.login.failed`
- `auth.session.revoked`
- `auth.token.refreshed`
- `auth.password.reset.requested`
- `auth.password.reset.completed`
- `auth.risk.detected`

Partition key: `tenant_id`.
Delivery semantics: at-least-once + idempotency key = `event_id`.

---

## 10) Tenant-Aware Request Context and Middleware

`tenant_context_middleware` responsibilities:
- Resolve `tenant_id` from trusted header/token claim.
- Enforce strict match between route/body/header/token tenant identifiers.
- Attach context object (`tenant_id`, `correlation_id`, `trace_id`, `principal`) to request scope.
- Reject cross-tenant access attempts with `403 AUTH_TENANT_MISMATCH`.

`authentication_middleware` responsibilities:
- Validate JWT signature via active key set.
- Validate issuer/audience/time window/nonce.
- Validate revocation status from session cache + persistent store fallback.
- Attach principal to request context.

---

## 11) Observability Hooks

### Metrics
- `auth_login_attempt_total{tenant_id,result,method}`
- `auth_token_issued_total{tenant_id,grant_type}`
- `auth_token_validation_total{tenant_id,result}`
- `auth_password_reset_total{tenant_id,phase,result}`
- `auth_session_active_gauge{tenant_id}`

### Tracing
- Span names: `auth.login`, `auth.token.issue`, `auth.token.validate`, `auth.password.reset`, `auth.session.revoke`.
- Mandatory span attrs: `tenant_id`, `user_id` (if known), `session_id`, `correlation_id`, `auth_method`, `result`.

### Logging
- Structured JSON logs with redaction for secrets.
- PII minimization and deterministic hashing for IP/user-agent in persistent audit records.

---

## 12) Migration Notes

1. Introduce `auth_service` behind gateway shadow mode (`/api/v1/auth` mirrored, non-authoritative).
2. Start dual-run token validation against legacy auth checks; compare divergence metrics.
3. Migrate active sessions via forced re-auth window (rolling by tenant cohorts).
4. Enable refresh-token rotation and revoke legacy long-lived tokens.
5. Cut over password reset endpoints; keep legacy endpoint forwarding for one release cycle.
6. Decommission old auth codepaths after 0 critical discrepancies over 14 days.

Rollback strategy:
- Feature-flag by tenant.
- Preserve signing key ring compatibility for rollback token validation.

---

## 13) Test Deliverables

- Request specs: auth endpoints success/failure, tenant mismatch, schema validation.
- Domain specs: token rotation replay detection, session revocation cascade, reset challenge expiry.
- Contract tests: `auth_service` <-> `user_service` API compatibility.
- Event contract tests: schema evolution checks (`schema_version`, required payload keys).
- Security tests: brute-force throttling, JWT tampering, stale refresh replay, cross-tenant token misuse.
- Performance checks: p95 login latency under configured concurrency budget.
