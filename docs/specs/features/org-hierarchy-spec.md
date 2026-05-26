# Org Hierarchy Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-26

Data model and business rules for the organization hierarchy service. Hierarchy depth: Organization → Department → Team.

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
