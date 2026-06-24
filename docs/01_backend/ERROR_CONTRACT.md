# ERROR_CONTRACT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Documents the error response shapes and HTTP status code conventions as implemented across `backend/services/`. Derived from direct code inspection.

---

## Error Response Shape

### FastAPI Services (standard)

FastAPI's default error shape — HTTPException raises:

```json
{
  "detail": "<error_code_or_message>"
}
```

Examples from observed code:
```json
{"detail": "role_not_found"}
{"detail": "permission_not_found"}
{"detail": "tenant_mismatch"}
{"detail": "missing_bearer_token"}
{"detail": "invalid_signature"}
{"detail": "token_expired"}
{"detail": "malformed_jwt"}
{"detail": "jwt_secret_not_configured"}
{"detail": "tenant_header_jwt_mismatch"}
{"detail": "version_conflict"}
{"detail": "already_enrolled"}
{"detail": "course_progress_not_found"}
{"detail": "session_not_found"}
```

### Stdlib HTTP Services (auth-service, checkout-service)

Manual JSON error body:

```json
{"error": "<error_code>"}
{"error": "<error_code>", "detail": "<message>"}
```

Examples:
```json
{"error": "not_found"}
{"error": "invalid_request", "detail": "..."}
{"error": "invalid_json"}
{"error": "secret_not_configured", "detail": "..."}
{"error": "unauthorized"}
{"error": "session_not_found"}
{"error": "domain_required"}
```

### Validation Errors (FastAPI 422)

FastAPI automatic request validation failures:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Password Policy Validation (auth-service specific)

`POST /api/v2/auth/password/policy/validate`

```json
{"valid": false, "violations": ["min_length_8", "requires_uppercase", "requires_digit"]}
{"valid": true, "violations": []}
```

---

## HTTP Status Code Conventions

| Status Code | Meaning | Used When |
|---|---|---|
| `200 OK` | Success | GET, POST (most auth endpoints), PATCH |
| `201 Created` | Resource created | POST /enrollments, POST /roles, POST /assignments, POST /policy-rules |
| `202 Accepted` | Async accepted | POST /enrollments/bulk-assign, POST /learning-paths/{id}/assignments |
| `204 No Content` | Success, no body | DELETE /roles/{id}, DELETE /assignments/{id}, PUT /roles/{id}/permissions |
| `400 Bad Request` | Malformed request | Invalid JSON, missing required body fields, domain_required |
| `401 Unauthorized` | Auth failure | Missing/invalid Bearer token, tenant_header_jwt_mismatch |
| `403 Forbidden` | Authorization failure | tenant_mismatch, missing permission |
| `404 Not Found` | Resource not found | role_not_found, session_not_found, course_progress_not_found |
| `409 Conflict` | Duplicate / conflict | already_enrolled, version_conflict |
| `422 Unprocessable Entity` | Validation failure | FastAPI Pydantic validation error, password policy violations |
| `503 Service Unavailable` | Config missing | jwt_secret_not_configured, secret_not_configured |

---

## Known Error Code Registry

The following error codes appear in the codebase:

### Auth Error Codes

| Error Code | Status | Description |
|---|---|---|
| `unauthorized` | 401 | Missing or invalid JWT |
| `missing_bearer_token` | 401 | Authorization header not a Bearer token |
| `invalid_signature` | 401 | JWT signature mismatch |
| `token_expired` | 401 | JWT exp claim in the past |
| `malformed_jwt` | 401 | Cannot split JWT into 3 parts |
| `invalid_format` | 401 | JWT format error (validate_token) |
| `invalid_header` | 401 | JWT header undecodable |
| `invalid_payload` | 401 | JWT payload undecodable |
| `token_revoked` | 401 | JTI is in revocation list |
| `expired` | 401 | Token expired (validate_token) |
| `tenant_mismatch` | 403 | JWT tenant_id ≠ X-Tenant-Id header |
| `tenant_header_jwt_mismatch` | 401 | X-Tenant-Id header ≠ JWT tenant claim |
| `secret_not_configured` | 503 | JWT_SHARED_SECRET env var missing |
| `jwt_secret_not_configured` | 503 | JWT secret not configured (rbac variant) |

### Session Error Codes

| Error Code | Status | Description |
|---|---|---|
| `session_not_found` | 404 | Session ID not in store |
| `domain_required` | 400 | Tenant discovery missing `domain` query param |

### Resource Error Codes

| Error Code | Status | Description |
|---|---|---|
| `role_not_found` | 404 | Role ID not in store |
| `permission_not_found` | 404 | Permission key not in store |
| `course_progress_not_found` | 404 | No progress record for learner+course |
| `not_found` | 404 | Generic not found (stdlib services) |

### Enrollment Error Codes

| Error Code | Status | Description |
|---|---|---|
| `already_enrolled` | 409 | Learner already enrolled in course |
| `version_conflict` | 409 | Optimistic locking version mismatch |
| `enrollment_inactive` | 409 | Cannot update progress for inactive enrollment |

### Request Error Codes

| Error Code | Status | Description |
|---|---|---|
| `invalid_request` | 400 | TypeError on schema parse (stdlib services) |
| `invalid_json` | 400 | JSON decode error |

---

## Tenant Service Error Model

tenant-service has a custom exception class:

```python
class TenantServiceError(Exception):
    status_code: int
    detail: str
```

Handled by: `@app.exception_handler(TenantServiceError)` → JSONResponse with `{"detail": exc.detail}`

---

## No Global Error Handler

FastAPI services do not implement a uniform global error handler. Each endpoint raises `HTTPException` directly. The result is that error format is consistent for HTTPException but may vary for:
- Unexpected Python exceptions (500 with FastAPI's default shape)
- Pydantic validation errors (422, standard FastAPI shape)
- Custom exception handlers (tenant-service)

---

## Related Documents

- `docs/01_backend/API_CONTRACT.md` — endpoint definitions
- `docs/01_backend/BACKEND_ARCHITECTURE.md` — service architecture
- `docs/08_reports/API_DISCOVERY_REPORT.md` — API discovery findings
