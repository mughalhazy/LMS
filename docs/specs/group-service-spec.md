# Group Service — Spec

**Service:** `group-service` | **Gateway:** `/api/v1/group` | **Port:** varies

## Purpose

Manages learner groups within a tenant organisation — group CRUD, status lifecycle, membership, and learning assignments to groups. Implements `org_hierarchy_spec.md`.

## Responsibilities

- Group CRUD with organisation scoping
- Group status lifecycle management
- Cascade-safe archiving (blocked if active memberships exist)
- Membership management (add, remove, role assignment)
- Learning assignment to groups (course, path, or assessment → all members or targeted subset)
- Audit trail for archive operations

## Out of scope

- Department management (owned by `department-service`)
- Course/path content (owned by `course-service`, `learning-path-service`)
- Enrollment execution (owned by `enrollment-service`)

## Data model

| Entity | Fields |
|---|---|
| `Group` | group_id, tenant_id, organization_id, name, code, description, status, created_by, metadata{}, created_at, updated_at |
| `GroupMembership` | membership_id, tenant_id, group_id, user_id, role, added_by, joined_at, status |
| `LearningAssignment` | assignment_id, tenant_id, group_id, assignment_type, learning_object_id, target, assigned_by, due_at, metadata{}, created_at |

## Status lifecycle

`DRAFT → ACTIVE → INACTIVE → ARCHIVED`

- Archiving blocked if active memberships exist
- INACTIVE suspends group without removing members

## Assignment types

`COURSE` | `LEARNING_PATH` | `ASSESSMENT`

## Assignment targets

`ALL_MEMBERS` | `ACTIVE_MEMBERS` | `SPECIFIC_ROLE`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/group` | Create group |
| GET | `/api/v1/group/{groupId}` | Get group (tenant-scoped) |
| PATCH | `/api/v1/group/{groupId}` | Update name, description, metadata |
| POST | `/api/v1/group/{groupId}/activate` | Transition to ACTIVE |
| POST | `/api/v1/group/{groupId}/deactivate` | Transition to INACTIVE |
| POST | `/api/v1/group/{groupId}/archive` | Archive group (blocks if active members) |
| GET | `/api/v1/group` | List groups (filter by org, status) |
| POST | `/api/v1/group/{groupId}/members` | Add member with role |
| DELETE | `/api/v1/group/{groupId}/members/{userId}` | Remove member |
| GET | `/api/v1/group/{groupId}/members` | List members |
| POST | `/api/v1/group/{groupId}/assignments` | Assign learning object |
| GET | `/api/v1/group/{groupId}/assignments` | List assignments |

## Behavioral rules

- Group name must be unique per organisation per tenant (case-insensitive)
- Archive blocked if any active memberships exist — cascade archiving not supported (members must be removed manually)
- Audit entry written on archive with tenant_id and group_id
- Learning assignments do not trigger enrollment — they are intent records consumed by downstream services

## Spec reference

`docs/specs/org_hierarchy_spec.md` — canonical hierarchy rules
