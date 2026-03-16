# User Service Engineering Specification (SPEC_02)

## 1) Service Purpose

`user_service` is the profile-and-identity lifecycle domain for Enterprise LMS V2. It extends the existing LMS `User` entity (authoritative person record) without taking over authentication or authorization-policy responsibilities.

### In-scope responsibilities
- User profile lifecycle (`pending_activation`, `active`, `suspended`, `locked`, `deactivated`, `terminated`).
- User status transitions and lifecycle audit timeline.
- Identity attributes and external identity link mappings.
- Profile and preference updates.
- Role linkage support (association pointers), not policy decisioning.

### Explicit non-goals
- No credential verification, token issuance, password reset, session management (owned by `auth_service`).
- No permission graph evaluation, role policy conflict logic, allow/deny decisions (owned by `rbac_service`).

---

## 2) Alignment to Existing LMS User Model (Source Identity Entity)

The canonical identity entity remains `User`.

### Baseline user identity shape retained
- `user_id`, `tenant_id`, `email`, `username`, `status`, `role_set`.
- Profile object: `first_name`, `last_name`, `locale`, `timezone`, `title`, `department`, `manager_id`, `avatar_url`.
- Lifecycle metadata: `created_by`, `created_at`, `activated_at`, `profile_version`, `lifecycle_timeline`.
- External identity links: provider + external subject mapping list.

### Extension strategy
- Extend the existing Rails `User` model via additive fields and related tables (`user_preferences`, `identity_links`, `user_lifecycle_events`) while preserving backward-compatible core columns.
- Keep `user_id` as the stable cross-service subject key.
- Preserve existing domain semantics where user identity ownership is separate from auth and RBAC policy engines.

---

## 3) Owned Data

## 3.1 Aggregates and tables

### `users` (owned)
- Identity core: `user_id`, `tenant_id`, `organization_id` (nullable), `email`, `username`.
- Lifecycle state: `status`, `created_at`, `created_by`, `activated_at`, `deactivated_at`, `terminated_at`.
- Profile snapshot: `first_name`, `last_name`, `locale`, `timezone`, `title`, `department`, `manager_id`, `avatar_url`.
- Role linkage fields: `role_set` (denormalized cache), `role_binding_version`, `last_role_sync_at`.
- Concurrency + audit: `profile_version`, `updated_at`, `updated_by`.

### `user_preferences` (owned)
- `user_id`, `tenant_id`, `notification_preferences` (jsonb), `accessibility_preferences` (jsonb), `language_preference`, `updated_at`, `updated_by`.

### `user_identity_links` (owned)
- `mapping_id`, `user_id`, `tenant_id`, `identity_provider`, `external_subject_id`, `external_username`, `mapping_attributes` (jsonb), `status`, `assurance_level`, `mapped_by`, `mapped_at`, `unmapped_at`, `last_login_at`.
- Uniqueness: `(tenant_id, identity_provider, external_subject_id)`.

### `user_lifecycle_events` (owned, append-only)
- `event_id`, `tenant_id`, `user_id`, `event_type`, `actor_id`, `occurred_at`, `reason_code`, `detail` (jsonb), `correlation_id`.

## 3.2 Data not owned
- Password hashes, MFA secrets, refresh tokens, auth sessions.
- Effective permissions, policy rules, SoD conflict policies.
- Institutional hierarchy source of truth (organization topology mastered by `institution_service`).

---

## 4) API Endpoints

Base path: `/api/v1/users`

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/users` | `POST` | Create user identity record. |
| `/api/v1/users` | `GET` | List users by tenant (+ optional status filter). |
| `/api/v1/users/{user_id}` | `GET` | Fetch one tenant-scoped user. |
| `/api/v1/users/{user_id}` | `PATCH` | Update mutable root attributes (e.g., username, role linkage cache, department). |
| `/api/v1/users/{user_id}` | `DELETE` | Soft-delete/deactivate according to policy. |
| `/api/v1/users/{user_id}/activate` | `POST` | Activate user account lifecycle state. |
| `/api/v1/users/{user_id}/profile` | `PATCH` | Update profile fields with optimistic concurrency. |
| `/api/v1/users/{user_id}/preferences` | `PUT` | Replace user preferences document. |
| `/api/v1/users/{user_id}/status` | `POST` | Transition status via valid lifecycle state machine. |
| `/api/v1/users/{user_id}/lock` | `POST` | Lock/unlock status transition operation. |
| `/api/v1/users/{user_id}/lifecycle` | `POST` | Terminate/reinstate lifecycle command. |
| `/api/v1/users/{user_id}/identity-links` | `POST` | Link external identity subject. |
| `/api/v1/users/{user_id}/identity-links` | `DELETE` | Unlink external identity subject. |
| `/api/v1/users/{user_id}/identity-links` | `GET` | Retrieve identity links. |
| `/api/v1/users/{user_id}/timeline` | `GET` | Retrieve lifecycle timeline. |

---

## 5) Request and Response Contracts

## 5.1 Common request contract rules
- `tenant_id` is mandatory on every command/query (query param or body).
- `user_id` path key + `tenant_id` must resolve to a single row; cross-tenant mismatch returns `404`.
- Write requests must include actor (`created_by`, `updated_by`, `changed_by`, etc.).
- Versioned updates use `If-Match: W/"profile_version:<n>"` or request `profile_version` field.

## 5.2 Key contracts

### Create user (`POST /api/v1/users`)
**Request**
```json
{
  "tenant_id": "t-100",
  "email": "learner@acme.edu",
  "username": "learner_01",
  "first_name": "Ava",
  "last_name": "Stone",
  "role_set": ["learner"],
  "auth_provider": "local",
  "external_subject_id": null,
  "created_by": "admin-22",
  "start_active": false
}
```

**Response 201**
```json
{
  "user": {
    "user_id": "u-8df...",
    "tenant_id": "t-100",
    "email": "learner@acme.edu",
    "username": "learner_01",
    "status": "pending_activation",
    "profile_version": 1,
    "profile": {
      "first_name": "Ava",
      "last_name": "Stone"
    }
  }
}
```

### Update profile (`PATCH /api/v1/users/{user_id}/profile`)
**Request**
```json
{
  "tenant_id": "t-100",
  "updated_by": "u-8df...",
  "title": "Data Analyst",
  "timezone": "Asia/Singapore",
  "avatar_url": "https://cdn.example/avatar.png"
}
```

**Response 200**: Full `user` object with incremented `profile_version`.

### Change status (`POST /api/v1/users/{user_id}/status`)
**Request**
```json
{
  "tenant_id": "t-100",
  "target_status": "suspended",
  "reason_code": "hr_hold",
  "changed_by": "admin-22",
  "effective_at": "2026-02-13T07:25:00Z"
}
```

**Response 200**: Full `user` object with new `status` and lifecycle timeline append.

### Map identity link (`POST /api/v1/users/{user_id}/identity-links`)
**Request**
```json
{
  "tenant_id": "t-100",
  "identity_provider": "azure_ad",
  "external_subject_id": "aad:9472",
  "external_username": "ava.stone",
  "mapping_attributes": {"domain": "acme.edu"},
  "mapped_by": "admin-22"
}
```

**Response 200**
```json
{
  "identity_links": [
    {
      "mapping_id": "map-12",
      "identity_provider": "azure_ad",
      "external_subject_id": "aad:9472",
      "status": "active"
    }
  ]
}
```

## 5.3 Error contract
- `400` invalid payload / invalid state transition.
- `401`/`403` authN/authZ failure from platform gateway/auth middleware.
- `404` user not found in provided tenant.
- `409` duplicate identity mapping, optimistic concurrency conflict.
- `422` validation errors (email format, enum mismatch, immutable field mutation attempt).

---

## 6) Events Produced

All events include envelope: `event_id`, `event_type`, `occurred_at`, `tenant_id`, `user_id`, `actor_id`, `trace_id`, `schema_version`, `payload`.

- `user.created`
- `user.activated`
- `user.profile_updated`
- `user.preferences.updated`
- `user.status_changed`
- `user.identity.mapped`
- `user.identity.unmapped`
- `user.lifecycle.terminated`
- `user.lifecycle.reinstated`

Event contract examples:
- `user.status_changed.payload`: `previous_status`, `new_status`, `reason_code`, `effective_at`.
- `user.profile_updated.payload`: changed field set, `profile_version`, updater.

---

## 7) Events Consumed

- `auth.login.succeeded` (from `auth_service`): update `last_login_at` on relevant identity link/user.
- `rbac.assignments.changed` (from `rbac_service`): refresh role linkage cache fields (`role_set`, `role_binding_version`) for read convenience.
- `institution.membership.changed` (from `institution_service`): update `organization_id`, `department`, `manager_id` links when institution mappings change.
- `tenant.deactivated` (platform/tenant domain): bulk move active users to `deactivated` according to tenant shutdown policy.

Consumer behavior:
- Idempotency key = producer `event_id`.
- Out-of-order tolerance with per-user version checks (`role_binding_version`, event timestamps).

---

## 8) Tenant Context Handling

- All reads/writes are tenant-scoped by `(tenant_id, user_id)`.
- DB constraints and indexes enforce tenant partition behavior:
  - `UNIQUE (tenant_id, email)`
  - `UNIQUE (tenant_id, username)`
  - `UNIQUE (tenant_id, identity_provider, external_subject_id)`
- Service rejects tenant context from untrusted body if JWT tenant claim mismatches.
- No cross-tenant query endpoints.
- Audit logs and emitted events always carry tenant context.

---

## 9) Integration Contracts

## 9.1 `auth_service`
- `user_service` provides identity attributes (status, profile, identity links).
- `auth_service` owns login/session/token/password.
- Integration mode:
  - Sync: `auth_service` checks user status before issuing sessions.
  - Async: consume `auth.login.succeeded` for usage metadata updates.

## 9.2 `rbac_service`
- `user_service` stores role linkage references (`role_set` cache, assignment version) for UI and filtering.
- `rbac_service` remains policy authority for permission evaluation and conflict rules.
- `user_service` never returns permission decisions; only role linkage data.

## 9.3 `institution_service`
- `institution_service` owns institution/org hierarchy and membership graph.
- `user_service` stores user-facing denormalized pointers (`organization_id`, manager linkage metadata).
- Membership changes flow via `institution.membership.changed` events.

---

## 10) Domain Boundary Guardrails

- User remains source identity entity across LMS services.
- Auth concerns are explicitly excluded from this domain.
- RBAC policy logic is explicitly excluded from this domain.
- Institution hierarchy ownership is external; only linkage lives here.

---

## 11) QC LOOP

### QC Iteration 1

| Category | Score (1-10) | Defect found |
|---|---:|---|
| ownership clarity | 9 | Needed sharper split between cached role linkage and RBAC authority. |
| alignment with repo User model | 9 | Needed explicit mapping to existing fields (`profile_version`, identity links, statuses). |
| API contract quality | 9 | Needed clearer error semantics and versioning expectations. |
| tenant safety | 10 | None. |
| extensibility | 9 | Needed explicit event idempotency/versioning statements. |
| domain separation | 9 | Needed stronger auth/RBAC non-goal language. |

**Revision actions applied**
1. Added explicit “owned vs not owned” data section and role linkage cache wording.
2. Added alignment section with current user shape and extension strategy.
3. Added error contract and optimistic concurrency notes.
4. Added consumed-event idempotency + out-of-order handling guidance.
5. Strengthened boundary guardrails and integration contracts.

### QC Iteration 2 (Final)

| Category | Score (1-10) | Rationale |
|---|---:|---|
| ownership clarity | 10 | Data ownership and non-ownership are explicit and testable. |
| alignment with repo User model | 10 | Core fields and lifecycle semantics are mapped and preserved. |
| API contract quality | 10 | Endpoint purpose, payload examples, status/error semantics, and version handling are defined. |
| tenant safety | 10 | Tenant keys, constraints, claim checks, and no cross-tenant access are explicit. |
| extensibility | 10 | Event schema envelope, consumed events, idempotency, and version controls are specified. |
| domain separation | 10 | Auth, RBAC policy, and institution authority boundaries are explicitly enforced. |

**QC status: all categories = 10/10.**
