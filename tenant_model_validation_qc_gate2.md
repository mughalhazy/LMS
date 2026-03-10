issue_type
component
description
severity
recommended_fix

Missing tenant identifier on tenant-scoped entity
`lessons` table and lesson-service contract
`lessons` is course-owned but has no explicit `tenant_id` in the core schema, and lesson creation/update contracts also omit `tenant_id`. This creates a validation gap where tenant scoping depends on transitive joins to `courses` instead of first-class tenant keys at write/read boundaries.
high
Add `tenant_id` to `lessons` (with FK to `tenants`) and require `tenant_id` in lesson-service commands/queries. Enforce composite constraints such as `(tenant_id, course_id, lesson_id)` and index by tenant for all lesson lookups.

Missing tenant identifier on tenant-scoped entity
`enrollments` table
`enrollments` lacks `tenant_id` despite being tenant-owned learner state. Current isolation relies on joining `users` and `courses`, increasing risk of accidental cross-tenant access from partial predicates or ad-hoc reporting queries.
high
Add `tenant_id` to `enrollments`, backfill from authoritative `users/courses` mapping, enforce FK to `tenants`, and add uniqueness/indexing with tenant scope (e.g., unique `(tenant_id, user_id, course_id)`).

Tenant boundary enforcement gap at service level
Lesson service operations
Lesson operations are defined with `course_id` and `lesson_id` only, unlike course operations that always include `tenant_id`. This inconsistency means the service boundary does not uniformly require tenant context before mutating tenant data.
high
Standardize all service contracts to include `tenant_id` as a mandatory input, validate token tenant claim == request tenant, and deny requests missing tenant context.

Cross-tenant access not strictly impossible by design
Isolation strategy + RBAC global scope
The isolation strategy explicitly includes shared-schema mode where filtering bugs can leak data, and RBAC includes global roles (`Platform Super Admin`, `support.impersonate_readonly`, `tenant.view_all`) with all-tenant scope. These are controlled exceptions but violate the strict requirement that cross-tenant data access be impossible.
medium
For strict isolation guarantees, remove/limit shared-schema tenancy for regulated tiers, enforce DB-level RLS policies keyed by tenant, and gate global/support access through break-glass workflows with just-in-time approval, immutable audit, and tenant-consent controls.

Tenant configuration inconsistency
Config key taxonomy across tenant/config specs
Tenant configuration keys are not fully canonicalized across specs (`tenant.features.*` in customization vs `feature.*` in configuration service), which can cause drift between control-plane configuration and runtime flag evaluation.
medium
Define a single canonical configuration namespace (e.g., `tenant.*` + `platform.*`), publish a versioned config schema/registry, and enforce key validation in configuration APIs and CI linting.
