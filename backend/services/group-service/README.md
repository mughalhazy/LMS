# Group Service

Implements:
- Group lifecycle (`draft -> active -> inactive -> archived`)
- Group membership management
- Group-based learning assignments for courses and learning paths

## Domain entities
- `groups`
- `group_memberships`
- `group_learning_assignments`

## API
See `openapi.yaml`.

## Python service module
`src/group_service.py` provides in-memory business logic for:
- group creation and lifecycle transition
- member add/remove/list
- group learning assignment add/list

## Design alignment
- Follows hierarchy constraints from `/docs/specs/features/org-hierarchy-spec.md` by enforcing uniqueness of names/codes within organization scope and lifecycle controls.
- Extends core LMS schema from `/docs/data/core-lms-schema.md` with group-focused tables in `schema.sql`.
