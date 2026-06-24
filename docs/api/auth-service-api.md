# Auth Service API Contract (v2)

> **CAT-003 fix 2026-05-31:** Base URL corrected from `/api/v1/auth` to `/api/v2/auth` to match
> implementation. `docs/specs/auth-service-spec.md §4` is the canonical spec; this doc is the
> quick-reference API surface.

Base URL: `/api/v2/auth`

## Route Table

| Route | Method | Auth Required | Description |
|---|---|---|---|
| `/sessions/login` | POST | No | Primary authentication endpoint (canonical). `/login` is a backward-compat alias. |
| `/tokens/refresh` | POST | No | Refresh token rotation — accepts `{tenant_id, refresh_token}`. |
| `/token` | POST | Conditional | Legacy session-based token issuance (backward compat). |
| `/sessions/validate` | POST | Service auth | Token introspection / session validation. |
| `/sessions/{session_id}` | GET | Yes | Fetch session metadata. **CAT-005** |
| `/sessions/{session_id}/revoke` | POST | Yes | Revoke specific session. **CAT-005** |
| `/sessions/logout` | POST | Yes | Revoke single session (alias for /sessions/{id}/revoke). |
| `/sessions/logout_all` | POST | Yes | Revoke all sessions for subject in tenant. |
| `/sessions/revoke-all` | POST | Yes | Alias for logout_all. **CAT-005** |
| `/password/reset/request` | POST | No | Begin password reset (anti-enumeration: always 202). |
| `/password/reset/confirm` | POST | No | Complete password reset challenge. |
| `/password/policy/validate` | POST | No | Validate password strength against tenant policy. **CAT-006** |
| `/password/forgot` | POST | No | Alias for /password/reset/request. |
| `/sso/initiate` | POST | No | Initiate SSO flow (SAML/OIDC). |
| `/sso/callback` | POST | No | Process SSO callback and create platform session. |
| `/tenant` | GET | No | Discover tenant by email domain (`?domain=`). |
| `/admin/users/{user_id}/reset-password` | POST | Yes (admin) | Admin-initiated password reset. |
| `/.well-known/jwks.json` | GET | No | Public signing keys (RS256 JWKS). |
| `/health` | GET | No | Liveness/readiness endpoint. |
| `/metrics` | GET | No | Service metrics. |

## Login schema summary

### Request (`POST /api/v2/auth/sessions/login`)
- `tenant_id` (string, required)
- `identifier` (string, required — email, username, or phone)
- `password` (string, required)
- `email` (string, backward-compat alias for identifier)
- `client.client_type`, `client.device_id`, `client.ip`, `client.user_agent` (optional)
- `auth_method` (`password|assertion_exchange`)

### Response 200
- `session_id` (string)
- `user.user_id`, `user.tenant_id` (CAT-007: API doc updated to match spec §4.1 — field is `user`, not `subject`)
- `access_token` (JWT, RS256)
- `token_type` (`Bearer`)
- `expires_in` (seconds, default 900)
- `refresh_token` (JWT with family_id for replay detection)
- `refresh_expires_in` (seconds)

### Error status matrix
- `400` malformed payload.
- `401` invalid credential / expired token / tenant mismatch.
- `409` refresh token replay conflict (family revoked).
- `422` password policy violation.
- `423` account locked (retry_after: 900s).
- `429` rate limited.

## Health endpoint response

`GET /api/v2/auth/health`

```json
{ "status": "ok", "service": "auth-service" }
```

---

## See also
- `docs/specs/auth-service-spec.md` — auth service canonical spec (base path `/api/v2/auth`)
- `docs/specs/sso-spec.md` — SSO spec
- `docs/integrations/auth-lifecycle-events.md` — auth event contracts
