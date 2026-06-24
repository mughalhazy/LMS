# Learning Path Service

This service implements the **learning_path_service** bounded context and owns curriculum composition, sequencing rules, prerequisites, path publishing lifecycle, and tenant-scoped path assignment.

## Scope implemented

- Learning path creation (draft-first lifecycle).
- Course sequencing through DAG-based path nodes/edges.
- Completion rules configuration and evaluation.
- Learning path publishing with validation gates.
- Tenant-scoped paths and tenant-bound operations.

## Structure

- `src/models.py`: core entities — `LearningPath`, `PathNode`, `PathEdge`, `CompletionRules`, `NodeProgress`, `LearningPathProgress`
- `src/service.py`: domain logic — creation, sequencing validation, completion evaluation, tenant isolation, publish validation
- `app/service.py`: `LearningPathManagementService` — tenant-scoped facade; also handles assignment scopes and audit log
- `app/schemas.py`: Pydantic request schemas for all API operations
- `app/main.py`: FastAPI app with all 14 routes and JWT security
- `tests/test_learning_path_service.py`: unit tests — tenant isolation, cycle checks, publish gates, completion rules

**Import note:** `src/` uses relative imports; import it as a package (`from src.models import ...`) not as bare modules. `app/service.py` and `app/main.py` add the service root (not `src/`) to `sys.path` to preserve this.

Run tests:

```bash
cd backend/services/learning-path-service
pytest -q
```

## Responsibilities

- Persist and version path metadata (`learning_paths`).
- Persist ordered/branched structure (`learning_path_nodes`, `learning_path_edges`, `learning_path_elective_groups`).
- Validate sequence integrity (acyclic graph, required-node coverage, explicit merge points).
- Publish immutable path versions for consumption by enrollment/progress services.
- Enforce tenant isolation on all reads/writes via required `tenant_id` request context.

## Service boundaries

The service does **not** own course metadata or assessment authoring.

- Course status and publishability are resolved via `course_catalog_service`.
- Assessment validity is resolved via `assessment_service`.
- Assignment execution and learner state transitions are executed by `enrollment_service` and `progress_tracking_service`.

## REST API

Spec: `Repo/docs/specs/features/learning-path-spec.md` | `Repo/backend/services/learning-path-service/service_rules.md`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/learning-paths` | Create a draft learning path |
| `GET` | `/api/v1/learning-paths` | List paths (filter: `status`, `owner_id`) |
| `GET` | `/api/v1/learning-paths/{path_id}` | Get a single learning path |
| `POST` | `/api/v1/learning-paths/{path_id}:publish` | Publish path (requires `change_reason`) |
| `POST` | `/api/v1/learning-paths/{path_id}:archive` | Archive path |
| `PUT` | `/api/v1/learning-paths/{path_id}/completion-rules` | Configure completion rules |
| `PUT` | `/api/v1/learning-paths/{path_id}/nodes` | Replace node set |
| `GET` | `/api/v1/learning-paths/{path_id}/nodes` | Get node set |
| `PUT` | `/api/v1/learning-paths/{path_id}/edges` | Replace edge set |
| `GET` | `/api/v1/learning-paths/{path_id}/edges` | Get edge set |
| `POST` | `/api/v1/learning-paths/{path_id}/assignments` | Assign path to role/department/location/manual scope |
| `GET` | `/api/v1/learning-paths/{path_id}/assignments` | List assignment scopes |
| `POST` | `/api/v1/learning-paths/{path_id}:evaluate-completion` | Evaluate completion against progress snapshot |
| `GET` | `/api/v1/learning-paths/{path_id}/audit-log` | Get audit log entries |
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Service metrics |

Tenant via `X-Tenant-Id` header; actor via `X-Actor-Id`. JWT required (same `JWT_SHARED_SECRET` as auth-service).

## Data model

See `schema.sql`.

Key entities:

- `learning_paths`
- `learning_path_nodes`
- `learning_path_edges`
- `learning_path_elective_groups`
- `learning_path_assignments`
- `learning_path_audit_log`

## Publishing validation rules

A path can transition from `draft` to `published` only when:

1. Path has at least one required node.
2. All referenced courses/assessments are active and publishable.
3. Graph is acyclic.
4. Every non-entry required node has at least one upstream node.
5. Branch merge points are explicit (`relation='branch_merge'`).
6. Completion mode and elective constraints are internally consistent.

## Tenant isolation

- Every table includes `tenant_id` and indexes are tenant-leading.
- API requires `X-Tenant-Id` and validates auth token tenant claim.
- Composite uniqueness is tenant-scoped.

## Events emitted

- `learning.path.created`
- `learning.path.updated`
- `learning.path.published`
- `learning.path.archived`

Events include `tenant_id`, `path_id`, `version`, `actor_id`, and timestamp fields for audit/compliance use.
