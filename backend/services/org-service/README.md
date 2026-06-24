# Organization Service

Organization Service implements LMS organization hierarchy, metadata, and lifecycle management.

## Scope
- Hierarchy: `Organization -> Department -> Team`
- Metadata: mutable metadata maps on all entities
- Lifecycle: deactivation with optional cascade policy
- Re-parent audit logging for departments and teams

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## API Endpoints

Scope: hierarchy view — creation, updates, deactivation, tree traversal, reparent audit. (Operational department lifecycle — cascade deactivate, reparent, membership — lives in `department-service`.)

### Organizations
- `POST /api/v1/organizations`
- `GET /api/v1/organizations` — list (optional `?tenant_id=` filter)
- `GET /api/v1/organizations/{organization_id}`
- `PATCH /api/v1/organizations/{organization_id}`
- `POST /api/v1/organizations/{organization_id}/deactivate`
- `DELETE /api/v1/organizations/{organization_id}`
- `GET /api/v1/organizations/{organization_id}/hierarchy`

### Departments
- `POST /api/v1/departments`
- `GET /api/v1/departments/{department_id}`
- `PATCH /api/v1/departments/{department_id}`
- `DELETE /api/v1/departments/{department_id}`

### Teams
- `POST /api/v1/teams`
- `GET /api/v1/teams` — list (optional `?department_id=` filter)
- `GET /api/v1/teams/{team_id}`
- `PATCH /api/v1/teams/{team_id}`
- `DELETE /api/v1/teams/{team_id}`

### Audit
- `GET /api/v1/audit/reparent-events`

## Domain Rules Enforced
- Parent existence required for child entities (no orphan departments/teams).
- Department names unique per organization.
- Team names unique per department.
- Deactivating organization requires `cascade=true` when active children exist.
- Re-parent operations append audit entries with actor + before/after parent IDs.
