# RBAC Service (Enterprise LMS V2)

Production-ready tenant-scoped `rbac_service` with:
- versioned REST API (`/api/v1/rbac`)
- roles, permissions, assignments
- authorization checks and middleware integration
- policy enforcement support (explicit deny baseline)
- audit decision logging
- health endpoint + observability counters
- RBAC change event publishing hooks

## Service module structure

- `app/main.py` — FastAPI app and versioned routes
- `app/models.py` — domain models
- `app/schemas.py` — request/response schemas
- `app/service.py` — RBAC domain/application logic
- `app/store.py` — tenant-partitioned storage adapter
- `app/contracts.py` — storage and publisher contracts
- `app/events.py` — event type constants and in-memory publisher/metrics hooks
- `app/security.py` — JWT and tenant claim checks
- `app/middleware.py` — route-level authorization dependency
- `events/rbac_events.yaml` — event definitions
- `tests/` — API and security tests

## API routes

Base: `/api/v1/rbac`

- `GET /health`
- `POST /roles`
- `GET /roles`
- `PATCH /roles/{role_id}`
- `PUT /roles/{role_id}/permissions`
- `GET /permissions`
- `POST /assignments`
- `GET /assignments`
- `PATCH /assignments/{assignment_id}`
- `DELETE /assignments/{assignment_id}`
- `GET /subjects/{subject_type}/{subject_id}/effective-permissions`
- `POST /authorize`
- `POST /authorize/batch`
- `POST /policy-rules`
- `GET /policy-rules`
- `PATCH /policy-rules/{policy_rule_id}`
- `DELETE /policy-rules/{policy_rule_id}`
- `GET /audit-log` (protected by middleware requiring `audit.view_tenant`)
- `GET /metrics`

## Migration notes

1. **Route migration**: old unversioned paths (`/roles`, `/assignments`, `/authorize`) moved to `/api/v1/rbac/...`.
2. **Tenant safety hardening**: mutating/listing endpoints now require `X-Tenant-Id` matching JWT `tenant_id` claim.
3. **Data model migration**: roles, assignments, policy rules partitioned by tenant; no cross-tenant writes.
4. **Authorization response**: now returns `decision`, `reason_codes`, and `policy_trace`.
5. **Events**: publish RBAC change events through `EventPublisher` contract.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```
