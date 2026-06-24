# USER_ROLES_AND_PERMISSIONS

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Documents the role and permission model as implemented in `backend/services/rbac-service`. This is the authoritative cross-layer contract for role-based access control. Derived from direct code inspection of rbac-service models.py and main.py.

---

## RBAC Service

**Service**: `rbac-service` (port 8128)
**App module**: `app.main:app`
**Base path**: `/api/v1/rbac`
**Auth**: JWT required (all endpoints), `X-Tenant-Id` header required with JWT claim match

---

## Subject Types

```python
class SubjectType(str, Enum):
    USER = "user"
    GROUP = "group"
    SERVICE_ACCOUNT = "service_account"
```

A subject is any entity that can be assigned a role:
- `user` — end user
- `group` — a group of users (role assigned to group propagates to all members)
- `service_account` — machine/service identity

---

## Scope Types

```python
class ScopeType(str, Enum):
    TENANT = "tenant"
    ORG_UNIT = "org_unit"
    COURSE = "course"
    PROGRAM = "program"
    COHORT = "cohort"
    BRANCH = "branch"
```

Scope limits where a role assignment applies:

| Scope | `scope_id` Semantics | Notes |
|---|---|---|
| `tenant` | tenant_id | Full tenant access |
| `org_unit` | org unit identifier | Org unit scoped |
| `course` | course_id | Course-scoped access |
| `program` | program_id | Program-scoped access |
| `cohort` | cohort_id | Cohort-scoped access |
| `branch` | N/A (uses `branch_ids[]`) | Multi-branch operator scope (BC-BRANCH-01 / MO-026) |

**Branch scope notes**: For `scope_type=BRANCH`, the `branch_ids` list specifies which branches the subject may operate within. An empty list = no branch access. `hq_admin`/`hq_viewer` use `scope_type=TENANT` for cross-branch visibility.

---

## Role Model

```python
class RoleDefinition(BaseModel):
    role_id: str       # UUID
    tenant_id: str
    role_key: str      # machine-readable key (e.g., "course_admin")
    display_name: str
    description: str
    is_system: bool = False   # system roles cannot be deleted
    status: RoleStatus = RoleStatus.ACTIVE
    version: int = 1
    created_at: datetime
    updated_at: datetime
```

### Role Status

```python
class RoleStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
```

**Deletion is soft-delete only**: DELETE endpoint sets `status=disabled`. Hard deletion is not permitted per spec.

---

## Permission Model

```python
class PermissionDefinition(BaseModel):
    permission_id: str     # UUID
    permission_key: str    # e.g., "course.publish", "audit.view_tenant"
    resource_type: str     # e.g., "course", "audit"
    action: str            # e.g., "publish", "view_tenant"
    risk_tier: Literal["low", "moderate", "high", "critical"] = "low"
    is_assignable: bool = True
```

Permission key format: `<resource_type>.<action>`

### Risk Tiers

| Tier | Description |
|---|---|
| `low` | Standard read/write operations |
| `moderate` | Elevated access, limited blast radius |
| `high` | Significant operational impact |
| `critical` | Security or data destruction potential |

---

## Role-Permission Binding

```python
class RolePermissionBinding(BaseModel):
    role_id: str
    permission_id: str
    effect: Literal["allow", "deny"] = "allow"
    conditions: dict[str, str] = {}
```

**RBAC supports explicit deny**: `effect="deny"` can be set to override an implicit allow.

---

## Subject-Role Assignment

```python
class SubjectRoleAssignment(BaseModel):
    assignment_id: str     # UUID
    tenant_id: str
    subject_type: SubjectType
    subject_id: str
    role_id: str
    scope_type: ScopeType
    scope_id: str
    branch_ids: list[str] | None = None   # for BRANCH scope only
    starts_at: datetime
    ends_at: datetime | None = None        # None = permanent
    source: Literal["direct", "group_derived", "jit"] = "direct"
    created_by: str
    created_at: datetime
    revoked_at: datetime | None = None
```

**Assignment sources**:
- `direct` — explicitly assigned
- `group_derived` — inherited from group membership
- `jit` — just-in-time provisioning (e.g., SSO claim mapping)

---

## Policy Rules

```python
class PolicyRule(BaseModel):
    policy_rule_id: str
    tenant_id: str
    rule_type: RuleType
    expression: dict[str, str]
    priority: int = 100
    enabled: bool = True
```

### Rule Types

```python
class RuleType(str, Enum):
    SOD_CONFLICT = "sod_conflict"        # Separation of duties
    EXPLICIT_DENY = "explicit_deny"      # Force deny regardless of assignments
    STEP_UP_REQUIRED = "step_up_required" # Require additional auth
    TIME_WINDOW = "time_window"          # Time-restricted access
    NETWORK_BOUNDARY = "network_boundary" # Network/IP-based restriction
```

Policy rules are tenant-scoped and evaluated at authorization time. Higher `priority` values take precedence (evaluated in descending order).

---

## Authorization Decision

```python
class AuthorizationDecisionLog(BaseModel):
    decision_id: str
    tenant_id: str
    principal_subject: str
    permission_key: str
    resource_type: str
    resource_id: str
    decision: Literal["allow", "deny"]
    reason_codes: list[str]
    policy_trace: list[str]
    correlation_id: str | None
    evaluated_at: datetime
```

**Authorization flow**:
1. Fetch effective permissions for `(tenant_id, subject_type, subject_id)`
2. Check if `permission_key` is in effective set
3. Evaluate policy rules (SOD, explicit deny, step-up, etc.)
4. Return `allow` or `deny` with reason codes and policy trace

---

## API Endpoints Summary

| Operation | Endpoint | Method |
|---|---|---|
| Create role | `POST /api/v1/rbac/roles` | POST |
| List roles | `GET /api/v1/rbac/roles` | GET |
| Get role | `GET /api/v1/rbac/roles/{role_id}` | GET |
| Update role | `PATCH /api/v1/rbac/roles/{role_id}` | PATCH |
| Soft-delete role | `DELETE /api/v1/rbac/roles/{role_id}` | DELETE |
| Replace role permissions | `PUT /api/v1/rbac/roles/{role_id}/permissions` | PUT |
| List permissions | `GET /api/v1/rbac/permissions` | GET |
| Get permission | `GET /api/v1/rbac/permissions/{permission_key}` | GET |
| Create assignment | `POST /api/v1/rbac/assignments` | POST |
| List assignments | `GET /api/v1/rbac/assignments` | GET |
| Update assignment | `PATCH /api/v1/rbac/assignments/{id}` | PATCH |
| Revoke assignment | `DELETE /api/v1/rbac/assignments/{id}` | DELETE |
| Effective permissions | `GET /api/v1/rbac/subjects/{type}/{id}/effective-permissions` | GET |
| Single authorize | `POST /api/v1/rbac/authorize` | POST |
| Batch authorize | `POST /api/v1/rbac/authorize/batch` | POST |
| Create policy rule | `POST /api/v1/rbac/policy-rules` | POST |
| List policy rules | `GET /api/v1/rbac/policy-rules` | GET |
| Update policy rule | `PATCH /api/v1/rbac/policy-rules/{id}` | PATCH |
| Disable policy rule | `DELETE /api/v1/rbac/policy-rules/{id}` | DELETE |
| View audit log | `GET /api/v1/rbac/audit-log` | GET |

**Audit log access requires `audit.view_tenant` permission** (enforced via authorization dependency).

---

## Cross-Cutting Rules

1. All RBAC data is tenant-scoped — no cross-tenant role inheritance
2. System roles (`is_system=true`) cannot be hard-deleted
3. Soft-delete only on roles (status → disabled) and policy rules (enabled → false)
4. RBAC permission definitions are in PROTECTED_AREAS — changes REQUIRE_APPROVAL
5. `tenant_id` on assignments is immutable once set

---

## Frontend Contract

Frontend must:
1. Send `X-Tenant-Id` header on all RBAC calls
2. Include Bearer JWT in Authorization header
3. Use `POST /api/v1/rbac/authorize` to check before rendering restricted UI
4. Use `GET /subjects/{type}/{id}/effective-permissions` to render permission-dependent UI elements

---

## Related Documents

- `docs/01_backend/API_CONTRACT.md` — full API contract
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — authentication
- `docs/specs/rbac-service-spec.md` — engineering spec
- `docs/specs/features/rbac-service-spec-v0.md` — prior version spec
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk items
