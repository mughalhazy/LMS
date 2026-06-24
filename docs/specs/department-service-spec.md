# Department Service — Spec

**Service:** `department-service` | **Gateway:** `/api/v1/department` | **Port:** varies

## Purpose

Manages organisational department hierarchy within a tenant — department CRUD, parent-child relationships, membership, cascade-safe deactivation, and reparenting with audit trail. Implements `org_hierarchy_spec.md`.

## Responsibilities

- Department CRUD with optional parent linkage
- Tenant + organisation scoped operations
- Cascade-safe deactivation: active children must be deactivated first (or cascade=True)
- Reactivation blocked if parent is inactive
- Reparenting with cycle detection and audit trail (before/after parent IDs + actor)
- Department membership management (user → department role)
- Audit log of all deactivation and reparenting operations

## Out of scope

- Organisation entity management (owned by `org-service`)
- User profile management (owned by `user-service`)
- Group management (owned by `group-service`)

## Data model

| Entity | Fields |
|---|---|
| `Department` | department_id, tenant_id, organization_id, name, code, parent_department_id, department_head_user_id, cost_center, status, created_at, updated_at |
| `DepartmentMembership` | membership_id, tenant_id, organization_id, department_id, user_id, role |

## Status values

`active` | `inactive`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/department` | Create department |
| GET | `/api/v1/department/{departmentId}` | Get department (tenant-scoped) |
| PATCH | `/api/v1/department/{departmentId}` | Update name, code, head, cost center |
| POST | `/api/v1/department/{departmentId}/deactivate` | Deactivate (cascade optional) |
| POST | `/api/v1/department/{departmentId}/reactivate` | Reactivate |
| POST | `/api/v1/department/{departmentId}/reparent` | Reparent with audit |
| GET | `/api/v1/department` | List departments (filter by org, status) |
| GET | `/api/v1/department/{departmentId}/children` | List direct children |
| POST | `/api/v1/department/{departmentId}/members` | Add member |
| GET | `/api/v1/department/{departmentId}/members` | List members |
| GET | `/api/v1/department/audit-log` | Tenant audit log |

## Behavioral rules

- Name and code must be unique within organisation scope (case-insensitive)
- Deactivate blocked if active children exist and cascade=False
- cascade=True recursively deactivates all active children
- Reactivate blocked if parent is inactive
- Reparent writes audit entry with before/after parent IDs and actor_id
- Cycle detection on reparent — rejected if reparent would create a cycle

## Spec reference

`docs/specs/org_hierarchy_spec.md` — canonical hierarchy rules
