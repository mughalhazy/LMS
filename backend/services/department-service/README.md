# Department Service

Department Service implements:

- Department creation with uniqueness validation by organization scope.
- Department hierarchy management (parent/child, re-parenting, cycle prevention).
- Department membership mapping between users and departments.

## Domain entities

- `Department`
  - `department_id`, `tenant_id`, `organization_id`, `name`, `code`, `status`
  - `parent_department_id`, `department_head_user_id`, `cost_center`
  - `created_at`, `updated_at`
- `DepartmentMembership`
  - `membership_id`, `tenant_id`, `organization_id`, `department_id`, `user_id`, `role`, `created_at`

## API endpoints

- `POST /api/v1/departments`
- `GET /api/v1/departments`
- `GET /api/v1/departments/{departmentId}`
- `GET /api/v1/departments/{departmentId}/children`
- `PATCH /api/v1/departments/{departmentId}/parent`
- `POST /api/v1/departments/{departmentId}/memberships`
- `GET /api/v1/departments/{departmentId}/memberships`

See `openapi.yaml` for request/response schemas.
