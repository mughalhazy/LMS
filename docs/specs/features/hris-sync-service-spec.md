# HRIS Sync Service Spec

**Type:** Feature Specification
**Service:** `hris-sync-service` (`Repo/backend/services/hris-sync-service/`)
**Version:** 1.0.0
**Anchor:** `doc-catalogue.md` B15a
**Field mapping reference:** `docs/integrations/hris-sync-spec.md`

---

## 1) Service Purpose

`hris-sync-service` ingests employee, department, and role data from external HRIS systems and synchronises it into the LMS data model. It manages sync sessions, maintains an audit log of all sync operations, and provides a job scheduler for automated periodic syncs.

Scope:
- Three sync operations: role mapping, department/org hierarchy mapping, employee sync.
- Full sync orchestration in dependency order (roles → departments → employees).
- Sync session lifecycle (start, track, complete).
- Scheduled job management (upsert, list, run-due).
- Audit trail for every sync operation.
- Read access to synced data snapshots (users, departments, roles).

Out of scope:
- Auth-service credential management.
- Course enrollment or learning progress (owned by enrollment-service / progress-service).
- Direct database writes to authoritative user records (sync output feeds the LMS user store via events or import pipelines).

---

## 2) Multi-Tenant Context

All routes require `X-Tenant-Id` header. Missing header → `400 missing_tenant_id`.

All sync data, sessions, audit entries, and job registrations are scoped to the `tenant_id` derived from this header. No cross-tenant reads or writes.

---

## 3) Sync Operations

### 3.1 Field Mapping (from `hris-sync-spec.md`)

| Operation | HRIS Source Fields | LMS Destination Fields |
|---|---|---|
| employee sync | `employee_id`, `first_name`, `last_name`, `work_email`, `employment_status`, `job_title`, `manager_employee_id`, `department_code`, `role_code`, `hire_date`, `termination_date` | `users.external_hris_id`, `users.first_name`, `users.last_name`, `users.email`, `users.status`, `users.title`, `users.manager_user_id`, `users.department_id`, `user_roles.role_id`, `users.hire_date`, `users.deactivated_at` |
| department mapping | `department_code`, `department_name`, `parent_department_code`, `cost_center`, `active_flag` | `departments.external_hris_code`, `departments.name`, `departments.parent_department_id`, `departments.cost_center`, `departments.is_active` |
| role mapping | `role_code`, `role_name`, `role_type`, `permission_bundle`, `active_flag` | `roles.external_hris_code`, `roles.name`, `roles.category`, `roles.permission_set`, `roles.is_active` |

### 3.2 Dependency Order

Employees reference `department_code` and `role_code`. Full sync must run in this order:
```
roles → departments → employees
```

Use `POST /api/v1/hris/sync/full` to run all three in the correct order within one session.

---

## 4) API Endpoints

Base path: `/api/v1/hris`

Required header on all routes: `X-Tenant-Id`

### 4.1 Sync Operations

#### Sync Roles
`POST /api/v1/hris/sync/roles`

```json
{
  "role_records": [
    {"role_code": "ENG_L3", "role_name": "Engineer L3", "role_type": "individual_contributor", "permission_bundle": "standard", "active_flag": true}
  ],
  "actor": "system",
  "session_id": null
}
```

Response `200`: sync summary `{operation, tenant_id, records_processed, created, updated, synced_at}`.

#### Sync Departments
`POST /api/v1/hris/sync/departments`

```json
{
  "department_records": [
    {"department_code": "ENG", "department_name": "Engineering", "parent_department_code": null, "cost_center": "CC-100", "active_flag": true}
  ],
  "actor": "system",
  "session_id": null
}
```

Response `200`: sync summary.

#### Sync Employees
`POST /api/v1/hris/sync/employees`

```json
{
  "employee_records": [
    {"employee_id": "EMP001", "first_name": "Ali", "last_name": "Ahmed", "work_email": "ali@example.com", "employment_status": "active", "job_title": "Engineer", "manager_employee_id": "EMP000", "department_code": "ENG", "role_code": "ENG_L3", "hire_date": "2025-01-15", "termination_date": null}
  ],
  "actor": "system",
  "session_id": null
}
```

Response `200`: sync summary.

#### Full Sync
`POST /api/v1/hris/sync/full`

Runs roles → departments → employees in one session. Rolls the session to `failed` on any error.

```json
{
  "role_records": [...],
  "department_records": [...],
  "employee_records": [...],
  "actor": "system"
}
```

Response `200`: `{session_id, status, roles: {...}, departments: {...}, employees: {...}}`.

### 4.2 Sync Sessions

| Route | Method | Notes |
|---|---|---|
| `/api/v1/hris/sessions` | POST | Start session — body: `{triggered_by, sync_mode}`. Returns session with `session_id`. |
| `/api/v1/hris/sessions` | GET | List all sessions for tenant. |
| `/api/v1/hris/sessions/{session_id}` | GET | Get session by ID. `404` if not found. |
| `/api/v1/hris/sessions/{session_id}/complete` | POST | Complete session — body: `{status}`. `404` if not found. |

Session statuses: `in_progress` | `completed` | `failed`.

### 4.3 Job Management

| Route | Method | Notes |
|---|---|---|
| `/api/v1/hris/jobs/{job_name}` | PUT | Upsert sync job — body: `{interval_minutes, enabled}`. |
| `/api/v1/hris/jobs` | GET | List all registered sync jobs for tenant. |
| `/api/v1/hris/jobs/run-due` | POST | Execute all jobs whose `next_run_at` is in the past. |

### 4.4 Data Reads

| Route | Method | Notes |
|---|---|---|
| `/api/v1/hris/users` | GET | List all synced user records for tenant. |
| `/api/v1/hris/departments` | GET | List all synced department records for tenant. |
| `/api/v1/hris/roles` | GET | List all synced role records for tenant. |

### 4.5 Audit Log

`GET /api/v1/hris/audit?operation={op}`

Optional `operation` query param: `role_mapping` | `department_mapping` | `employee_sync`.

Returns list of audit entries, each containing: `audit_id`, `tenant_id`, `actor`, `operation`, `records_processed`, `created`, `updated`, `synced_at`.

---

## 5) Sync Summary Response Shape

All individual sync operations return:

```json
{
  "operation": "role_mapping",
  "tenant_id": "tenant_a",
  "records_processed": 5,
  "created": 3,
  "updated": 2,
  "synced_at": "2026-01-01T10:00:00Z"
}
```

---

## 6) Integration Points

### 6.1 `hris-sync-spec.md`
Canonical field mapping reference. This spec implements all three operations defined there.

### 6.2 `org-service` / `department-service`
Department hierarchy data synced by this service feeds org-service and department-service entity stores via import or event pipelines. Direct API calls to org-service are outside hris-sync-service scope.

### 6.3 `docs/designs/platform-integration-layer-design.md`
Platform integration architecture reference for how HRIS connectors fit into the broader integration layer.

---

## See also

- `docs/integrations/hris-sync-spec.md` — field mapping reference
- `docs/integrations/standards-support.md` — integration standards
- `docs/api/integration-api.md` — integration API surface
- `Repo/backend/services/hris-sync-service/app/main.py` — route implementation
- `Repo/backend/services/hris-sync-service/app/service.py` — HRISSyncManagementService
- `doc-catalogue.md` B15a — spec registration
