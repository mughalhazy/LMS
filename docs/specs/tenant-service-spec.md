# Tenant Service Spec (SPEC_04)

**Type:** Service Specification | **Canonical version** — supersedes `docs/specs/tenant-service-spec-v0.md`
**Anchor:** `docs/anchors/tenant-contract.md` | **Related:** `docs/designs/tenant-extension-model.md`

---

## 1) Service Purpose

`tenant_service` is the system-of-record for tenant root entities. It manages tenant lifecycle, tenant-scoped configuration, tenant status transitions, tenant-to-plan linkage, and enforcement metadata for tenant isolation rules.

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
   - `name` (canonical — replaces deprecated `display_name`)
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

Base path: `/api/v1/tenants` (except §4.12 which uses `/api/v1/isolation`)

> **As-implemented (v2.0.0)** — routes below reflect the current service implementation.
> Routes present in the original spec intent but not yet built are listed in §4.13.

### 4.1 Validate Tenant Creation
- `POST /api/v1/tenants/validate`

Pre-creation validation. Returns pass/fail with error list before committing tenant creation.

Request:
```json
{
  "name": "Acme University",
  "country_code": "PK",
  "segment_type": "enterprise",
  "plan_type": "enterprise_v2",
  "addon_flags": ["lti", "sso"]
}
```

Response `200`:
```json
{
  "validation_passed": true,
  "errors": []
}
```

### 4.2 Create Tenant
- `POST /api/v1/tenants`

Creates tenant and provisions its namespace. Returns bootstrap status and isolation mode.

Request:
```json
{
  "name": "Acme University",
  "country_code": "PK",
  "segment_type": "enterprise",
  "plan_type": "enterprise_v2",
  "addon_flags": ["lti", "sso"],
  "admin_user": "usr_890"
}
```

Response `201`:
```json
{
  "tenant_id": "e1f4...",
  "bootstrap_status": "complete",
  "isolation_mode": "schema_per_tenant",
  "namespace_resource": "ns://tenant-e1f4"
}
```

Isolation modes: `schema_per_tenant` | `database_per_tenant`.

### 4.3 Initialize Tenant Configuration
- `PUT /api/v1/tenants/{tenant_id}/configuration`

Sets the initial full configuration for a newly created tenant. Use PATCH (§4.5) for subsequent partial updates.

Request:
```json
{
  "default_locale": "en-US",
  "timezone": "Asia/Karachi",
  "branding": {"logo_url": "https://...", "theme": "dark"},
  "enabled_modules": ["courses", "assessments", "lti"],
  "security_baseline": {"mfa_required_for_admins": true},
  "country_behavior_profiles": {}
}
```

Response `200`: `TenantConfigurationResponse` with `configuration` and `effective_settings`.

### 4.4 Get Tenant Configuration
- `GET /api/v1/tenants/{tenant_id}/configuration?include_defaults=true`

Response `200`: current config, raw payload, and effective settings (with defaults merged when `include_defaults=true`).

### 4.5 Update Tenant Configuration
- `PATCH /api/v1/tenants/{tenant_id}/configuration`

Partial update. Requires `actor_id` and `change_reason` for audit trail.

Request:
```json
{
  "config_patch": {
    "timezone": "Europe/Berlin",
    "security_baseline": {"mfa_required_for_admins": true}
  },
  "actor_id": "usr_admin_123",
  "change_reason": "Security baseline uplift"
}
```

Response `200`: `TenantConfigurationResponse`.

### 4.6 Manage Feature Flags
- `PATCH /api/v1/tenants/{tenant_id}/feature-flags`

Toggles individual feature flags without a full config patch. `actor_id` defaults to `"system"`.

Request:
```json
{
  "feature_flag_changes": {"new_course_editor": true, "beta_ai_tutor": false},
  "actor_id": "usr_admin_123"
}
```

Response `200`: `TenantConfigurationResponse`.

### 4.7 Suspend Tenant
- `POST /api/v1/tenants/{tenant_id}/lifecycle/suspend`

Request:
```json
{
  "suspension_reason": "Invoice overdue > 30 days",
  "suspended_by": "usr_billing_ops"
}
```

Response `200`:
```json
{
  "suspension_receipt": {
    "tenant_id": "e1f4...",
    "state": "suspended"
  }
}
```

### 4.8 Reactivate Tenant
- `POST /api/v1/tenants/{tenant_id}/lifecycle/reactivate`

Request:
```json
{
  "reactivation_reason": "Invoice cleared",
  "approved_by": "usr_billing_ops"
}
```

Response `200`:
```json
{
  "reactivation_receipt": {
    "tenant_id": "e1f4...",
    "state": "active"
  }
}
```

### 4.9 Archive Tenant
- `POST /api/v1/tenants/{tenant_id}/lifecycle/archive`

Request:
```json
{
  "archive_policy": "soft_delete",
  "retention_period": "7y",
  "requested_by": "usr_platform_admin"
}
```

Response `200`:
```json
{
  "archive_status": {
    "tenant_id": "e1f4...",
    "state": "archived"
  }
}
```

### 4.10 Decommission Tenant
- `POST /api/v1/tenants/{tenant_id}/lifecycle/decommission`

Request:
```json
{
  "legal_hold_status": false,
  "purge_after_date": "2030-01-01T00:00:00Z",
  "approved_by": "usr_platform_admin"
}
```

Response `200`:
```json
{
  "decommission_status": {
    "tenant_id": "e1f4...",
    "state": "decommissioned"
  }
}
```

### 4.11 Get Lifecycle Status
- `GET /api/v1/tenants/{tenant_id}/lifecycle`

Returns current lifecycle state, full transition history, and allowed next actions.

Response `200` (`LifecycleStatusResponse`):
- `lifecycle_state` — current `LifecycleState` value
- `state_history` — ordered list of events (state, reason, actor_id, effective_at, recorded_at)
- `pending_transitions` — allowed next state names
- `policy_constraints` — active enforcement rules
- `next_allowed_actions` — convenience alias for pending_transitions

Lifecycle state machine:

| State | Allowed transitions |
|---|---|
| `provisioning` | `activate` |
| `active` | `suspend`, `archive` |
| `suspended` | `reactivate`, `archive` |
| `archived` | `decommission` |
| `decommissioned` | (none) |

### 4.12 Evaluate Isolation Policy
- `POST /api/v1/isolation/evaluate`

Evaluates whether an actor is permitted to perform an action on behalf of a tenant. Used by downstream services to enforce cross-tenant access rules. Base path is `/api/v1/isolation`, not `/api/v1/tenants`.

Request (`IsolationContext`):
```json
{
  "tenant_id": "e1f4...",
  "actor_tenant_id": "e1f4...",
  "actor_id": "usr_admin_123",
  "action": "write_course"
}
```

Response `200` (`IsolationDecision`):
```json
{
  "allowed": true,
  "reason": "actor_tenant matches target_tenant"
}
```

### 4.13 Planned / Not Yet Implemented

The following routes appear in the original spec intent but are absent from the current v2.0.0 implementation:

| Route | Notes |
|---|---|
| `GET /api/v1/tenants/{tenant_id}` | Read tenant identity + status; not yet built |
| `PUT /api/v1/tenants/{tenant_id}/plan-link` | Plan linkage; currently handled by entitlement domain |
| `GET /api/v1/tenants/{tenant_id}/isolation-policy` | Isolation policy CRUD; evaluate endpoint (§4.12) is the current form |
| `PATCH /api/v1/tenants/{tenant_id}/isolation-policy` | Restricted admin endpoint; not yet built |

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
  "timestamp": "2026-01-01T00:00:00Z",
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

### 9.2 Entitlement Model
- `tenant_plan_link` is authoritative linkage metadata, not full entitlement rules.
- Entitlement computation remains external; `tenant_service` publishes link changes and caches only minimal plan metadata.
- See `docs/anchors/tenant-contract.md` for canonical field definitions (`name`, `addon_flags`, etc.).

### 9.3 User Assignment Flows
- `tenant_service` stores assignment references (e.g., `primary_admin_user_id`) only.
- Status transitions (e.g., suspend) emit events consumed by assignment/access services to enforce access changes.

---

## 10) Service Boundary Integrity

`tenant_service` MUST NOT:
- Manage institution hierarchy nodes beyond tenant root mapping.
- Authenticate users, issue tokens, or manage credentials.
- Own course, enrollment, curriculum, grading, or learning progress entities.

---

## See also

- `docs/anchors/tenant-contract.md` — canonical tenant payload contract
- `docs/designs/tenant-extension-model.md` — tenant extension field design
- `docs/architecture/multi-tenant-isolation-model.md` — isolation architecture
- `docs/specs/tenant-service-spec-v0.md` — deprecated predecessor (retained on disk)
