# Multi-Branch RBAC Model

**Type:** Architecture | **Date:** 2026-04-14 | **MS§:** §5.6 (RBAC), §5.10 (Admin Operations)
**Gap:** MO-017 | **Contract:** BC-BRANCH-01
**Source authority:** `LMS_Pakistan_Market_Research_MASTER.md` §3.2 (Coaching Academies — multi-branch complexity)
**Status:** SPEC COMPLETE — implementation reference for `rbac-service` and `enterprise-control`

---

## Purpose

This document defines how Role-Based Access Control (RBAC) is extended for multi-branch tenants — coaching academy networks, franchise school chains, corporate multi-office deployments. It implements the behavioral contract BC-BRANCH-01 (Multi-Branch Operations: Unified Visibility Without Context Switching).

---

## Problem Statement

Large coaching academies (e.g., KIPS, Star) operate 50+ branches across Pakistan. Branch managers must be isolated from each other's operational data. HQ administrators need cross-branch visibility. Without a formal multi-branch RBAC model:
- HQ administrators must log into each branch separately (worst case in current market)
- Cross-branch analytics require manual report aggregation
- Branch managers may accidentally see or act on other branch data

---

## Multi-Branch Identity Model

```
Tenant
  └── Organisation (root)
        ├── Branch A (org node type: "branch")
        │     ├── Batch A1
        │     └── Batch A2
        ├── Branch B
        │     ├── Batch B1
        │     └── Batch B2
        └── Branch C
```

**Tenant = entire academy network.** All branches exist within a single tenant. Data is not multi-tenanted by branch — it is scope-filtered by branch assignment at the RBAC layer.

---

## Role Types

### System-Defined Multi-Branch Roles

| Role | Scope | Permissions |
|---|---|---|
| `hq_admin` | All branches in tenant | Read + write across all branches; cross-branch analytics; no branch-level filter |
| `hq_viewer` | All branches in tenant | Read-only across all branches; no write |
| `branch_manager` | Assigned branch(es) only | Full ops (enroll, attendance, fee, batch) for assigned branches only |
| `branch_teacher` | Assigned branch + assigned batch(es) | Content delivery, attendance marking, assessment grading for assigned batches |
| `branch_staff` | Assigned branch only | Fee collection, basic attendance, student comms |

### Role Scope Bindings

Every role binding includes a `scope` field:

```json
{
  "user_id": "user_123",
  "role": "branch_manager",
  "tenant_id": "tenant_abc",
  "scope": {
    "type": "branch",
    "branch_ids": ["branch_A", "branch_B"]
  }
}
```

`hq_admin` bindings have `scope.type = "tenant"` (no branch filter applied).

---

## RBAC Enforcement at Service Layer

All services that operate on branch-scoped data must enforce branch filtering at query time. The tenant_id is always the outermost filter; branch_id is the inner scope filter.

### Enforcement pattern

```python
def require_branch_access(user_context: UserContext, branch_id: str) -> None:
    if user_context.scope_type == "tenant":
        return  # hq_admin — no restriction
    if branch_id not in user_context.branch_ids:
        raise PermissionError(f"branch_access_denied: {branch_id}")
```

This check must be present in:
- `services/academy-ops/` — batch, student, attendance, fee operations
- `services/analytics-service/` — cross-branch vs single-branch query routing
- `services/operations-os/` — Daily Action List scope filtering
- `backend/services/enrollment-service/` — enrollment scoped to branch's batches
- `backend/services/reporting-service/` — report scope selection

---

## Cross-Branch Analytics Model

### HQ Role (scope_type = "tenant")

The analytics service returns **aggregate + per-branch breakdown** by default:

```json
{
  "aggregate": {
    "total_students": 1840,
    "avg_attendance_rate": 0.82,
    "overdue_fees_count": 47
  },
  "by_branch": [
    {"branch_id": "branch_A", "students": 450, "attendance_rate": 0.79, "overdue_fees": 12},
    {"branch_id": "branch_B", "students": 380, "attendance_rate": 0.88, "overdue_fees": 8}
  ]
}
```

The analytics service must default to the aggregate+breakdown view for `hq_admin` — not require a separate "run cross-branch report" action.

### Branch Role (scope_type = "branch")

The analytics service returns data scoped to the user's assigned branch(es) only. No aggregate across other branches is returned. No reference to other branch names or data is included in the response.

---

## Daily Action List — Branch Scoping

The `operations-os` service generates the Daily Action List per user scope:

| User Role | Daily Action List Scope |
|---|---|
| `hq_admin` | All branches — aggregated, with branch label on each item |
| `branch_manager` | Assigned branch(es) only |
| `branch_teacher` | Assigned batches only (within their branch) |

BC-BRANCH-01 requires the HQ Daily Action List to be **filterable by branch** — not separate lists per branch. HQ sees one unified list with branch context on each item.

---

## Operational Isolation Rules

Per BC-BRANCH-01: branch-level isolation for operational actions.

- A `branch_manager` for Branch A **cannot** enroll a student in Branch B
- A `branch_manager` for Branch A **cannot** send a fee reminder to a Branch B student
- A `branch_teacher` **cannot** mark attendance for a batch outside their assignment
- Cross-branch CRUD operations raise `PermissionError` — they do not silently succeed

---

## Entitlement Dependency

Multi-branch operations are a **paid capability**:

- `CAP-MULTI-BRANCH` must be in the tenant's capability bundle to activate multi-branch role bindings
- Free tier: single branch only (`hq_admin` role is disabled; only `branch_manager` = tenant owner)
- Starter tier: up to 5 branches
- Pro/Enterprise: unlimited branches

When a tenant is on the free tier and attempts to add a second branch, the entitlement service returns `deny_reason = "not_entitled_addon:CAP-MULTI-BRANCH"` and the commerce service triggers an upgrade suggestion (BC-LANG-01 compliant).

---

## Implementation Points

| Component | What to update |
|---|---|
| `backend/services/rbac-service/` | Add `scope` field to role bindings; add `require_branch_access()` enforcement utility |
| `services/academy-ops/` | Branch-scope filters on all list/create/update operations |
| `services/analytics-service/` | Cross-branch aggregate view for `scope_type = "tenant"` |
| `services/operations-os/` | Daily Action List branch-label injection + branch filter support |
| `services/enterprise-control/` | Multi-branch role binding management UI/API |
| `docs/specs/B0P09_full_capability_domain_map.md` | Register `CAP-MULTI-BRANCH` |

---

## References

- `docs/specs/platform_behavioral_contract.md` — BC-BRANCH-01
- `docs/architecture/B2P02_entitlement_service_design.md` — entitlement model
- `docs/architecture/B2P07_audit_policy_layer_design.md` — audit trail for branch ops
- `docs/specs/enterprise_control_spec.md` — enterprise role management
- `docs/architecture/org_hierarchy_spec.md` — org/branch data model
- `LMS_Pakistan_Market_Research_MASTER.md` §3.2 (coaching academy multi-branch complexity)
