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
- `POST /organizations`
- `PATCH /organizations/{organization_id}`
- `POST /organizations/{organization_id}/deactivate`
- `GET /organizations/{organization_id}/hierarchy`
- `POST /departments`
- `PATCH /departments/{department_id}`
- `POST /teams`
- `PATCH /teams/{team_id}`
- `GET /audit/reparent-events`

## Domain Rules Enforced
- Parent existence required for child entities (no orphan departments/teams).
- Department names unique per organization.
- Team names unique per department.
- Deactivating organization requires `cascade=true` when active children exist.
- Re-parent operations append audit entries with actor + before/after parent IDs.
