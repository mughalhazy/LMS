# Authentication Service

Tenant-aware authentication microservice for LMS.

## Implemented capabilities

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/token`
- `POST /api/v1/auth/sessions/validate`
- `POST /api/v1/auth/password/forgot`
- `POST /api/v1/auth/password/reset`

## Design highlights

- Enforces tenant context (`tenant_id`) at login, token issuance, token validation, and password reset.
- Uses signed JWT-like tokens (`HS256`) with `tenant_id`, `session_id`, and role claims.
- Uses session tracking with revocation checks.
- Includes one-time reset challenge lifecycle with expiry and single-use semantics.
- Uses in-memory store seeded with test users and tenants.

## Run

```bash
cd backend/services/auth-service
python -m app.main
```

Service starts on `http://0.0.0.0:8081`.

## Seed users

- `tenant-acme` + `admin@acme.test` / `AcmePass#123`
- `tenant-globex` + `learner@globex.test` / `GlobexPass#123`

## Notes

- Replace the static signing secret in `app/main.py` with a KMS-managed secret.
- Wire `InMemoryAuthStore` to persistent data storage for production use.
