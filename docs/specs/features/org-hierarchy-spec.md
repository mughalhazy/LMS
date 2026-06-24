# Org Hierarchy Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-30

Data model and business rules for the organization hierarchy. Hierarchy depth: Organization → Department → Team. Implemented across two services with non-overlapping scope — see §Service Scope Partition below.

---

## Service Scope Partition

The org hierarchy domain is implemented by two services. Their scopes are deliberately non-overlapping; neither is a replacement for the other.

### org-service — Hierarchy View

`org-service` owns the static structure of the hierarchy: entities, their parent-child relationships, metadata, and the audit trail of reparenting events. It is the system of record for what the hierarchy looks like.

**What org-service owns:**
- Organization creation, metadata updates, and deactivation.
- Department and team creation and metadata updates (as structural members of the hierarchy).
- Hierarchy traversal — `GET /api/v1/organizations/{organization_id}/hierarchy` returns the full org → department → team tree.
- Reparent audit log — `GET /api/v1/audit/reparent-events` provides an immutable record of before/after parent changes.

**org-service routes:**

| Route | Method | Scope |
|---|---|---|
| `/api/v1/organizations` | POST | Create organization |
| `/api/v1/organizations/{id}` | PATCH | Update organization metadata |
| `/api/v1/organizations/{id}/deactivate` | POST | Deactivate organization (requires cascade or pre-deactivated children) |
| `/api/v1/organizations/{id}/hierarchy` | GET | Full hierarchy tree (org → departments → teams) |
| `/api/v1/departments` | POST | Create department (as a hierarchy member) |
| `/api/v1/departments/{id}` | PATCH | Update department metadata |
| `/api/v1/teams` | POST | Create team (as a hierarchy member) |
| `/api/v1/teams/{id}` | PATCH | Update team metadata |
| `/api/v1/audit/reparent-events` | GET | Reparent audit log |

**What org-service does NOT own:**
- Department operational lifecycle (cascade deactivation, reactivation, reparenting with membership impact).
- Department membership assignment and management.
- Department child listing (operational query).
- Full department CRUD from an operational/management perspective.

---

### department-service — Operational Lifecycle

`department-service` owns the operational management of departments: status transitions, membership, and structural moves. It is the service through which administrators manage the living operation of departments — not just their place in a hierarchy, but their staffing, activation state, and reporting relationships.

**What department-service owns:**
- Full department CRUD from an operational perspective (create, list, get, update).
- Deactivation with cascade policy — `POST /api/v1/departments/{id}:deactivate` accepts `cascade` flag; propagates deactivation to child departments.
- Reactivation — `POST /api/v1/departments/{id}:reactivate`.
- Reparenting — `POST /api/v1/departments/{id}:reparent` with `new_parent_department_id`; actor-attributed and audit-logged.
- Child listing — `GET /api/v1/departments/{id}/children`.
- Department membership — `MapMembershipRequest` for assigning learners/staff to departments.

**department-service routes:**

| Route | Method | Scope |
|---|---|---|
| `/api/v1/departments` | POST | Create department (operational creation with full field set) |
| `/api/v1/departments` | GET | List departments (filterable by `organization_id`, `status`) |
| `/api/v1/departments/{id}` | GET | Get department by ID |
| `/api/v1/departments/{id}` | PATCH | Update department (name, code, head, cost_center) |
| `/api/v1/departments/{id}:deactivate` | POST | Deactivate with optional cascade |
| `/api/v1/departments/{id}:reactivate` | POST | Reactivate department |
| `/api/v1/departments/{id}:reparent` | POST | Move department to new parent; actor-attributed |
| `/api/v1/departments/{id}/children` | GET | List direct child departments |

**What department-service does NOT own:**
- Organization-level entities (organizations, teams) — those are org-service domain.
- Hierarchy traversal and tree view — org-service's `GET /hierarchy` is the authoritative tree view.
- Reparent audit log — org-service owns `/api/v1/audit/reparent-events` as the canonical audit trail.

---

### Scope Boundary Note

Both services expose `/api/v1/departments` routes. This is intentional — they run on separate ports/hostnames as distinct microservices. The API gateway routes to each based on the calling context:
- Hierarchy setup and tree traversal → org-service.
- Operational management, lifecycle transitions, membership → department-service.

When creating a department as part of initial hierarchy setup (e.g., during org bootstrap), use org-service. When managing an existing department's operational state (activation, membership, reporting line changes), use department-service.

---

## Entities

### organizations
`organization_id` (PK), `tenant_id` (FK), `name`, `code`, `status` (active/inactive), `parent_organization_id` (nullable FK for multi-org enterprises), `primary_admin_user_id`, `timezone`, `locale`, `created_at`, `updated_at`

### departments
`department_id` (PK), `tenant_id` (FK), `organization_id` (FK), `name`, `code`, `status` (active/inactive), `parent_department_id` (nullable FK), `department_head_user_id`, `cost_center`, `created_at`, `updated_at`

### teams
`team_id` (PK), `tenant_id` (FK), `department_id` (FK), `name`, `code`, `status` (active/inactive), `team_lead_user_id`, `capacity`, `created_at`, `updated_at`

---

## Relationships

| source_entity | relationship | target_entity | cardinality | notes |
|---|---|---|---|---|
| organizations | contains | departments | 1:N | Every department must belong to exactly one organization and match organization.tenant_id. |
| departments | contains | teams | 1:N | Every team must belong to exactly one department and match department.tenant_id. |
| organizations | may_have_parent | organizations | N:1 (optional) | Supports enterprise group structures while preserving tenant isolation. |
| departments | may_have_parent | departments | N:1 (optional) | Supports nested departments (e.g., Engineering > Platform). |

---

## Business Rules

- Hierarchy depth is fixed at Organization → Department → Team for operational ownership and reporting.
- A child entity cannot exist without its direct parent (no orphan departments or teams).
- Deactivating an organization requires all child departments and teams to be deactivated first, or a cascading deactivation policy must be applied.
- Department and team names must be unique within their direct parent scope.
- Users can be assigned memberships at any level; effective access is resolved by least-privilege plus inherited visibility from parent entities.
- Cross-organization team membership is not allowed unless explicitly enabled through inter-organization collaboration policy.
- Re-parenting departments or teams must be audit logged with before/after parent IDs and actor metadata.
- Tenant integrity is mandatory: all entities must carry `tenant_id` and all joins/mutations must enforce `tenant_id` equality.
