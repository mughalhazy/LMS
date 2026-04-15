# Enterprise LMS V2 User Service

Production-oriented user profile service for LMS V2. This service extends (does not replace) the canonical Rails `User` identity entity by managing tenant-scoped profile lifecycle data.

## Scope

Owned by this service:
- profile lifecycle CRUD projection for existing Rails users
- tenant-safe user status and profile updates
- identity attributes mirror (email/username/external subject)
- role linkage references (link/unlink only)
- audit log entries
- lifecycle event publishing
- observability counters

Explicitly **not** owned by this service:
- authentication (passwords, JWT issuance, session management)
- RBAC policy decisions
- institution ownership / tenancy provisioning
- shared database writes back to Rails primary DB

## API

Base path: `/api/v1`

- `POST /api/v1/users`
- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}/status`
- `POST /api/v1/users/{user_id}/role-links`
- `DELETE /api/v1/users/{user_id}/role-links`
- `DELETE /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}/audit`
- `GET /api/v1/events/users`
- `GET /health`
- `GET /metrics`

All tenant-scoped endpoints require `X-Tenant-Id` header. Requests also carry `tenant_id` in query/body and must match header context.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8081
```

## Test

```bash
pytest -q
```

## Storage Contract

`app/store.py` defines `UserStore` and `AuditLogStore` protocols. Replace the in-memory adapter with a dedicated user-service datastore (e.g., Postgres schema owned by this service). Never write to Rails shared database tables.

## Migration Notes

See `migrations/0002_user_service_projection_notes.md` for rollout guidance.
