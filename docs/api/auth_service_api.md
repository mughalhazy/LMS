# Auth Service API Contract (v1)

Base URL: `/api/v1/auth`

## Route Table

| Route | Method | Auth Required | Description |
|---|---|---|---|
| `/login` | POST | No | Primary authentication endpoint. |
| `/token` | POST | Conditional (grant-specific) | Token issuance + refresh. |
| `/token/validate` | POST | Service auth | Token introspection/validation. |
| `/sessions/{session_id}` | GET | Yes | Fetch session metadata for owning principal/admin scope. |
| `/sessions/{session_id}/revoke` | POST | Yes | Revoke specific session. |
| `/sessions/revoke-all` | POST | Yes | Revoke all subject sessions in tenant. |
| `/password/forgot` | POST | No | Begin password reset. |
| `/password/reset` | POST | No | Complete password reset challenge. |
| `/password/policy/validate` | POST | No | Validate password strength/policy. |
| `/health` | GET | No | Liveness/readiness endpoint. |

## Login schema summary

### Request
- `tenant_id` (string, required)
- `identifier` (string, required)
- `secret` (string, required for password flow)
- `auth_method` (`password|assertion_exchange`, required)
- `device.ip`, `device.user_agent`, `device.device_id` (optional but recommended)

### Response 200
- `session_id` (string)
- `token_type` (`Bearer`)
- `access_token` (JWT)
- `expires_in` (seconds)
- `refresh_token` (opaque)
- `refresh_expires_in` (seconds)
- `tenant_id` (string)
- `subject.user_id`, `subject.status`

## Error status matrix

- `400` malformed payload / unsupported grant.
- `401` invalid credential or token.
- `403` tenant mismatch or policy block.
- `404` scoped resource not found.
- `409` refresh token reuse/replay conflict.
- `422` password policy violation.
- `429` throttling active.

## Health endpoint response

`GET /api/v1/auth/health`

```json
{
  "status": "ok",
  "checks": {
    "db": "ok",
    "key_store": "ok",
    "event_bus": "ok",
    "user_service": "ok"
  },
  "version": "1.0.0",
  "timestamp": "2026-01-15T10:12:00Z"
}
```
