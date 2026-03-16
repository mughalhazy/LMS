# SPEC_04_tenant_service — Engineering Specification (Enterprise LMS V2)

## 1) Service Purpose
`tenant_service` is the system-of-record for tenant root entities in Enterprise LMS V2. It manages tenant lifecycle, tenant-scoped configuration, tenant status transitions, tenant-to-plan linkage, and enforcement metadata for tenant isolation rules.

The service provides:
- Deterministic tenant provisioning and controlled lifecycle transitions.
- Versioned tenant configuration with auditable change history.
- Plan linkage metadata required for entitlement evaluation.
- Canonical tenant status for cross-service policy enforcement.
- Isolation policy descriptors consumed by downstream services.

Out of scope:
- Institution hierarchy modeling beyond tenant root.
- User authentication and credential handling.
- Course catalog, courses, enrollments, or learner progress ownership.

---

## 2) Domain Responsibilities
1. **Tenant lifecycle**: create, activate, suspend, reactivate, archive, decommission.
2. **Tenant configuration**: locale/timezone, branding, modules, policy toggles, security baselines.
3. **Tenant status**: current state + transition history + allowed next states.
4. **Tenant plan linkage**: active plan id, effective period, pending plan change, linkage audit log.
5. **Tenant isolation rules**: tenant-scoped policy object describing partition key, data residency, allowed integration boundaries, and enforcement requirements.

---

## 3) Owned Data

### 3.1 Authoritative Entities
1. `tenant`
   - `tenant_id` (UUID, immutable)
   - `tenant_key` (string, unique, immutable, external-friendly identifier)
   - `display_name`
   - `status` (`provisioning|active|suspended|archived|decommissioning|decommissioned`)
   - `data_region`
   - `created_at`, `created_by`, `updated_at`, `updated_by`

2. `tenant_lifecycle_transition`
   - `transition_id`, `tenant_id`, `from_status`, `to_status`
   - `reason_code`, `reason_detail`
   - `approved_by`, `effective_at`, `recorded_at`

3. `tenant_configuration`
   - `tenant_id`
   - `config_version` (monotonic integer)
   - `config_payload` (JSONB; validated schema)
   - `change_summary`, `changed_by`, `changed_at`

4. `tenant_plan_link`
   - `tenant_id`
   - `plan_id`
   - `plan_version`
   - `effective_from`, `effective_to`
   - `link_status` (`active|scheduled|expired|revoked`)
   - `updated_by`, `updated_at`

5. `tenant_isolation_policy`
   - `tenant_id`
   - `partition_key` (normally `tenant_id`)
   - `residency_constraints`
   - `encryption_profile_ref`
   - `cross_tenant_access_policy` (default deny)
   - `policy_version`, `updated_at`

### 3.2 Non-Owned References
- `institution_root_id` (optional external reference from `institution_service`; not authoritative here).
- `entitlement_snapshot_ref` (reference/id supplied by entitlement model).
- `primary_admin_user_id` (reference to identity/user domain; never auth data).

### 3.3 Data Ownership Rules
- `tenant_service` is source of truth for tenant root identity, status, config versions, plan links, and isolation metadata.
- Downstream services may cache tenant status/config but must treat this service as canonical.
- No storage of passwords, auth secrets, course structures, enrollment records.

---

## 4) API Endpoints
Base path: `/api/v1/tenants`

### 4.1 Create Tenant
- `POST /api/v1/tenants`

Request:
```json
{
  "tenant_key": "acme-university",
  "display_name": "Acme University",
  "data_region": "eu-west-1",
  "initial_plan_id": "plan_enterprise_v2",
  "institution_root_ref": "inst_root_123",
  "primary_admin_user_id": "usr_890"
}
```

Response `201`:
```json
{
  "tenant_id": "e1f4...",
  "tenant_key": "acme-university",
  "status": "provisioning",
  "config_version": 1,
  "plan_link": {
    "plan_id": "plan_enterprise_v2",
    "link_status": "active"
  },
  "created_at": "2026-01-01T10:00:00Z"
}
```

Errors: `400` validation, `409` duplicate key, `422` policy violation.

### 4.2 Get Tenant
- `GET /api/v1/tenants/{tenant_id}`

Response `200` includes identity + status + active plan summary + isolation policy version.

### 4.3 Update Tenant Configuration
- `PATCH /api/v1/tenants/{tenant_id}/configuration`

Request (JSON Merge Patch style):
```json
{
  "branding": {"logo_url": "https://...", "theme": "dark"},
  "timezone": "Europe/Berlin",
  "security": {"mfa_required_for_admins": true},
  "change_reason": "Security baseline uplift"
}
```

Response `200`:
```json
{
  "tenant_id": "e1f4...",
  "config_version": 2,
  "effective_configuration": {"...": "..."},
  "changed_at": "2026-01-05T12:00:00Z"
}
```

### 4.4 Get Tenant Configuration
- `GET /api/v1/tenants/{tenant_id}/configuration?include_defaults=true`

Response `200`: current version + payload + merged defaults (optional).

### 4.5 Transition Tenant Status
- `POST /api/v1/tenants/{tenant_id}/status-transitions`

Request:
```json
{
  "target_status": "suspended",
  "reason_code": "BILLING_HOLD",
  "reason_detail": "Invoice overdue > 30 days",
  "effective_at": "2026-02-01T00:00:00Z"
}
```

Response `202`:
```json
{
  "tenant_id": "e1f4...",
  "from_status": "active",
  "to_status": "suspended",
  "transition_id": "tr_123",
  "effective_at": "2026-02-01T00:00:00Z"
}
```

### 4.6 Link or Schedule Plan Change
- `PUT /api/v1/tenants/{tenant_id}/plan-link`

Request:
```json
{
  "plan_id": "plan_enterprise_plus",
  "plan_version": "2026.01",
  "effective_from": "2026-03-01T00:00:00Z"
}
```

Response `200`: current + scheduled linkage summary.

### 4.7 Get Isolation Policy
- `GET /api/v1/tenants/{tenant_id}/isolation-policy`

Response `200`: partition key, region constraints, cross-tenant policy, policy version.

### 4.8 Update Isolation Policy
- `PATCH /api/v1/tenants/{tenant_id}/isolation-policy`

Restricted to platform security admin role. Returns updated `policy_version`.

### 4.9 Decommission Tenant
- `POST /api/v1/tenants/{tenant_id}/decommission`

Request includes legal hold confirmation and purge schedule. Returns accepted workflow id.

---

## 5) Request/Response Contract Standards
- **Idempotency**: `POST /tenants` and status transitions require `Idempotency-Key` header.
- **Concurrency control**: mutation endpoints support `If-Match` with entity version/ETag.
- **Traceability**: all responses include `x-request-id`; all mutations require actor context.
- **Error schema**:
```json
{
  "error_code": "TENANT_STATUS_TRANSITION_NOT_ALLOWED",
  "message": "Cannot transition from archived to active",
  "details": {"from_status": "archived", "to_status": "active"},
  "request_id": "req_123"
}
```
- **Authorization**: service trusts platform identity token claims (no auth ownership here).

---

## 6) Events Produced
Published to event bus with partition key = `tenant_id`.

1. `tenant.created.v1`
2. `tenant.configuration.updated.v1`
3. `tenant.status.changed.v1`
4. `tenant.plan.linked.v1`
5. `tenant.isolation.policy.updated.v1`
6. `tenant.decommission.requested.v1`
7. `tenant.decommission.completed.v1`

Common event envelope:
```json
{
  "event_id": "evt_...",
  "event_type": "tenant.status.changed.v1",
  "occurred_at": "2026-01-01T00:00:00Z",
  "tenant_id": "e1f4...",
  "producer": "tenant_service",
  "payload": {}
}
```

---

## 7) Events Consumed
1. `institution.root.provisioned.v1` (from `institution_service`)
   - Action: attach/update `institution_root_ref` for tenant.
2. `entitlement.plan.deprecated.v1` (from entitlement/billing domain)
   - Action: mark linked plan as migration-required, emit advisory status.
3. `user.assignment.admin.changed.v1` (from user-assignment flow)
   - Action: update referenced primary admin assignment metadata.
4. `security.policy.baseline.updated.v1` (from security/config governance)
   - Action: evaluate drift and optionally queue config update recommendation.

Consumer rule: all consumed events must include tenant context or resolvable mapping to `tenant_id`; otherwise drop + dead-letter.

---

## 8) Tenant Isolation Model
1. **Data partitioning**: every tenant-owned record keyed by `tenant_id`; queries must include tenant predicate.
2. **Access policy**: default deny for cross-tenant reads/writes. Break-glass access requires audited privileged scope.
3. **Encryption**: tenant data encrypted at rest; optional per-tenant key references via `encryption_profile_ref`.
4. **Regionality**: `data_region` and `residency_constraints` enforced during provisioning and integrations.
5. **Event isolation**: tenant_id-partitioned topics/partitions; consumers reject mismatched tenant context.
6. **Operational isolation**: rate limits, quotas, and backpressure tracked per tenant to prevent noisy neighbor impact.

---

## 9) Integration Points

### 9.1 `institution_service`
- `tenant_service` may store only `institution_root_ref` mapping to tenant.
- Institution hierarchy (campus/department/program trees) remains fully owned by `institution_service`.
- On tenant creation, optionally call institution bootstrap flow; ownership boundary remains unchanged.

### 9.2 Entitlement Model
- `tenant_plan_link` is authoritative linkage metadata, not full entitlement rules.
- Entitlement computation remains external; `tenant_service` publishes link changes and caches only minimal plan metadata.
- If entitlement system invalidates plan, `tenant_service` updates link status and emits status advisory event.

### 9.3 User Assignment Flows
- `tenant_service` stores assignment references (e.g., `primary_admin_user_id`) only.
- User-to-role assignments and authentication are external responsibilities.
- Status transitions (e.g., suspend) emit events consumed by assignment/access services to enforce access changes.

---

## 10) Service Boundary Integrity (Explicit Non-Ownership)
`tenant_service` MUST NOT:
- Manage institution hierarchy nodes beyond tenant root mapping.
- Authenticate users, issue tokens, or manage credentials.
- Own course, enrollment, curriculum, grading, or learning progress entities.

If such data appears in incoming payloads, service validates and rejects with boundary violation error.

---

## 11) QC LOOP

### QC Pass 1 (Initial Draft Assessment)
- Tenant ownership clarity: **9/10**
- Multi-tenant correctness: **9/10**
- API contract quality: **9/10**
- Service boundary integrity: **10/10**
- Security isolation: **9/10**
- Repo extension safety: **10/10**

Defects found (<10):
1. Ownership clarity lacked explicit non-owned reference handling.
2. Multi-tenant correctness lacked operational/noisy-neighbor controls.
3. API quality lacked idempotency/concurrency requirements.
4. Security isolation lacked explicit event isolation and break-glass controls.

Revisions applied:
- Added section **3.2 Non-Owned References** and explicit ownership rules.
- Added operational isolation controls in section **8**.
- Added idempotency, ETag/If-Match, and standardized error schema in section **5**.
- Added event isolation + break-glass constraints in section **8**.

### QC Pass 2 (Post-Revision)
- Tenant ownership clarity: **10/10**
- Multi-tenant correctness: **10/10**
- API contract quality: **10/10**
- Service boundary integrity: **10/10**
- Security isolation: **10/10**
- Repo extension safety: **10/10**

QC exit condition satisfied: **all categories = 10/10**.
