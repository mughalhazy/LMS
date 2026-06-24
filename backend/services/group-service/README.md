# Group Service

FastAPI microservice for tenant-scoped group management — creation, membership, status lifecycle, and learning assignments. Spec: `Repo/docs/specs/features/org-hierarchy-spec.md`.

## REST API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/groups` | Create a group (starts at DRAFT) |
| `GET` | `/api/v1/groups` | List groups (filter: `organization_id`, `status`) |
| `GET` | `/api/v1/groups/{group_id}` | Get a group |
| `PATCH` | `/api/v1/groups/{group_id}` | Update name/description/metadata |
| `POST` | `/api/v1/groups/{group_id}:activate` | Transition DRAFT→ACTIVE |
| `POST` | `/api/v1/groups/{group_id}:deactivate` | Transition ACTIVE→INACTIVE |
| `POST` | `/api/v1/groups/{group_id}:archive` | Transition to ARCHIVED (blocked if active members) |
| `POST` | `/api/v1/groups/{group_id}/members` | Add a member |
| `GET` | `/api/v1/groups/{group_id}/members` | List members |
| `DELETE` | `/api/v1/groups/{group_id}/members/{user_id}` | Remove a member |
| `POST` | `/api/v1/groups/{group_id}/assignments` | Assign course/learning-path to group |
| `GET` | `/api/v1/groups/{group_id}/assignments` | List learning assignments |

Tenant via `X-Tenant-Id` header; actor via `X-Actor-Id`.

## Status lifecycle

`DRAFT → ACTIVE → INACTIVE → ARCHIVED`

Archiving blocked if active memberships exist (cascade-safe rule per spec).

## Domain entities

- `groups`, `group_memberships`, `group_learning_assignments`
- `GroupStatus`: draft / active / inactive / archived
- `AssignmentType`: course / learning_path
- `AssignmentTarget`: current_members / current_and_future_members

## Structure

- `src/models.py` + `src/group_service.py`: domain models and business logic
- `app/service.py`: `GroupManagementService` — tenant-scoped facade
- `app/schemas.py`: Pydantic request schemas
- `app/main.py`: FastAPI app
- `openapi.yaml`: OpenAPI spec

## Run

```bash
uvicorn app.main:app --port 8093
```
