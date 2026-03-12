# Learning Path Service

This service implements the **learning_path_service** bounded context and owns curriculum composition, sequencing rules, prerequisites, path publishing lifecycle, and tenant-scoped path assignment.

## Scope implemented

- Learning path creation (draft-first lifecycle).
- Course sequencing through DAG-based path nodes/edges.
- Learning path publishing with validation gates.
- Tenant-scoped paths and tenant-bound operations.

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

## API

See `openapi.yaml` for HTTP contract.

Primary resources:

- `/api/v1/learning-paths`
- `/api/v1/learning-paths/{pathId}/nodes`
- `/api/v1/learning-paths/{pathId}/edges`
- `/api/v1/learning-paths/{pathId}/publish`

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
