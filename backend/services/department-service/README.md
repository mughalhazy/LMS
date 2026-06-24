# Department Service

FastAPI microservice for tenant-scoped department management — creation, hierarchy, cascade deactivation, reparenting with audit trail. Spec: `Repo/docs/specs/features/org-hierarchy-spec.md`.

## REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/departments` | Create a department |
| `GET` | `/api/v1/departments` | List departments (filter: `organization_id`, `status`) |
| `GET` | `/api/v1/departments/{department_id}` | Get a department |
| `PATCH` | `/api/v1/departments/{department_id}` | Update name/code/head/cost_center |
| `POST` | `/api/v1/departments/{department_id}:deactivate` | Deactivate (cascade optional) |
| `POST` | `/api/v1/departments/{department_id}:reactivate` | Reactivate (parent must be active) |
| `POST` | `/api/v1/departments/{department_id}:reparent` | Reparent with before/after audit trail |
| `GET` | `/api/v1/departments/{department_id}/children` | List direct child departments |

Tenant via `X-Tenant-Id` header; actor via `X-Actor-Id`. JWT required.

## Status lifecycle

`active ↔ inactive`

Deactivation blocked if active children exist unless `cascade=true`.
Reactivation blocked if parent is inactive (no orphan reactivation).

## Domain entities

- `Department`: department_id, tenant_id, organization_id, name, code, status, parent_department_id, department_head_user_id, cost_center
- `DepartmentMembership`: membership_id, tenant_id, organization_id, department_id, user_id, role

## Structure

- `src/models.py` + `src/service.py`: domain models and business logic
- `app/service.py`: `DepartmentManagementService` — tenant-scoped facade with audit log
- `app/schemas.py`: Pydantic request schemas
- `app/security.py`: JWT validation
- `app/main.py`: FastAPI app with all routes

## Run

```bash
uvicorn app.main:app --port 8094
```
