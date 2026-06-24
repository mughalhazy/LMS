# VALIDATION_PARITY

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

Documents the alignment (or misalignment) between backend validation rules and the validation the frontend must implement. Frontend validation is a PENDING document — Frontend Authority Capture has not been executed. This document reflects backend-side rules only; frontend parity is to be verified.

---

## Status Note

**Frontend validation not yet verified.** This document currently captures backend-side rules only. When Frontend Authority Capture is executed, the "Frontend" column must be updated with actual implementation details.

---

## Authentication Validation Parity

| Rule | Backend (Verified) | Frontend (Pending) |
|---|---|---|
| JWT Bearer required on all authenticated endpoints | `require_jwt` dependency — enforced | Must include Authorization: Bearer <token> |
| Token expiry handling | Checked via `exp` claim | Must handle 401 and trigger token refresh |
| X-Tenant-Id required | Enforced at dependency injection | Must include X-Tenant-Id on every request |
| JWT tenant_id claim must match X-Tenant-Id | Enforced — returns 401/403 | Must not send mismatched tenant context |
| X-API-Version: v1 returned | Set on every response | Should read this header for API version detection |
| Refresh before expiry | auth-service enforces TTL | Frontend must proactively refresh before exp |

---

## Password Validation Parity

Backend rules (auth-service `POST /api/v2/auth/password/policy/validate`):

| Rule | Violation Code | Backend Enforced | Frontend Should Pre-validate |
|---|---|---|---|
| Min 8 characters | `min_length_8` | Yes | Yes (UX) |
| At least one uppercase | `requires_uppercase` | Yes | Yes (UX) |
| At least one digit | `requires_digit` | Yes | Yes (UX) |

**Parity status**: Frontend should pre-validate to improve UX, but backend validation is the authoritative gate. Both must enforce identical rules.

---

## Tenant Isolation Parity

| Rule | Backend | Frontend |
|---|---|---|
| All API calls scoped to tenant | X-Tenant-Id header required | Must always include X-Tenant-Id |
| Tenant context from auth token | JWT `tenant_id` claim | Derive from JWT payload after login |
| Cross-tenant reads blocked | 401/403 returned | Never construct requests for other tenants |
| Tenant lifecycle state check | SUSPENDED → no writes | Show appropriate error for suspended tenant |

---

## Enrollment Validation Parity

| Rule | Backend | Frontend |
|---|---|---|
| Duplicate enrollment | 409 `already_enrolled` | Show "already enrolled" without re-submitting |
| Version conflict | 409 `version_conflict` | Refresh enrollment state and retry |
| Optimistic locking | version field tracked | Send current version in transition requests |
| Inactive enrollment | 409 `enrollment_inactive` | Show appropriate state |
| Status transitions | State machine enforced | Show only valid next-state options |
| Bulk assign | 202 async accepted | Poll job status or handle async response |

---

## RBAC Validation Parity

| Rule | Backend | Frontend |
|---|---|---|
| Permission check before action | `POST /authorize` | Check before rendering restricted UI |
| Tenant scope match | 403 `tenant_mismatch` | Never call RBAC with mismatched tenant |
| Audit log access | Requires `audit.view_tenant` | Check permission before showing audit log link |
| Role soft-delete only | DELETE sets disabled | Do not expect hard delete |
| Branch scope | `branch_ids[]` | Handle branch-scoped permission checks |

---

## Progress Validation Parity

| Rule | Backend | Frontend |
|---|---|---|
| Tenant mismatch in progress | 400 `tenant_mismatch` | Derive tenant from token context |
| Enrollment inactive | 409 | Show active enrollment required warning |
| Completion eligibility | GET /eligibility endpoint | Check before showing certificate link |

---

## Tenant Service Validation Parity

| Rule | Backend | Frontend |
|---|---|---|
| Idempotency-Key required for lifecycle transitions | 400 or 422 if missing | Generate and send Idempotency-Key for lifecycle actions |
| Lifecycle state constraints | State machine enforced | Show only allowed next actions |
| Feature flags | PATCH /feature-flags | Reflect flag state in UI |

---

## Form Field Validation Parity

### Required Fields

| Entity | Required Backend Fields | Required Frontend Fields |
|---|---|---|
| Login | tenant_id, identifier, password | Same |
| Enrollment create | user_id, course_id, source_channel, tenant_id | Same |
| Role create | role_key, display_name, description, tenant_id | Same |
| Assignment create | subject_type, subject_id, role_id, scope_type, scope_id, created_by | Same |
| Authorize request | subject_type, subject_id, permission_key, resource_type, resource_id | Same |

---

## Idempotency Requirements

Frontend must generate and send `Idempotency-Key` (UUID) for:
- `POST /api/v1/tenants` — tenant creation
- `POST /api/v1/tenants/{id}/lifecycle/suspend`
- `POST /api/v1/tenants/{id}/lifecycle/reactivate`
- `POST /api/v1/tenants/{id}/lifecycle/archive`
- `POST /api/v1/tenants/{id}/lifecycle/decommission`

The key must be unique per logical operation (not per retry). Use the same key on retry.

---

## Error Handling Parity

Frontend must handle these HTTP status codes:

| Status | Backend Sends When | Frontend Should Do |
|---|---|---|
| 400 | Malformed request, missing required field | Show field-level error |
| 401 | Invalid/expired token, tenant mismatch | Redirect to login or refresh token |
| 403 | Permission denied, tenant scope mismatch | Show access denied |
| 404 | Resource not found | Show not found state |
| 409 | Conflict (duplicate, version mismatch) | Show conflict with context |
| 422 | Pydantic validation failure | Show field-level validation errors |
| 503 | Server misconfiguration (missing secrets) | Show "service unavailable" |

---

## Gap: Frontend Validation Not Verified

Frontend Authority Capture has not been executed. The following are currently unknown:
- Whether frontend validates password policy before submission
- Whether frontend includes `X-Tenant-Id` on all API calls
- Whether frontend handles 401 token refresh correctly
- Whether frontend sends `Idempotency-Key` for lifecycle operations
- Whether frontend checks RBAC permissions before rendering restricted UI

These gaps must be addressed in the Frontend Authority Capture phase.

---

## Related Documents

- `docs/01_backend/VALIDATION_RULES.md` — backend validation rules (verified)
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — auth contract
- `docs/03_fullstack_contracts/DATA_SHAPE_REGISTRY.md` — data shapes
- `docs/01_backend/ERROR_CONTRACT.md` — error codes
