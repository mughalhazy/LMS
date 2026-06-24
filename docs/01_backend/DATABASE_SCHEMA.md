# DATABASE_SCHEMA

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

This document captures the data storage layer exactly as implemented. It is derived from direct code inspection. See BACKEND_RISK_REGISTER.md for the risk implications of the findings below.

---

## Persistence State (Updated 2026-06-23)

**16 services use SQLite persistence via wired store_db.py implementations. 53 services remain in-memory.**

Task 7 (2026-06-23) wired complete `store_db.py` implementations into 16 service `main.py` files: auth, rbac, enrollment, progress, tenant, assessment, certificate, lesson, program, badge, session, user, org, cohort, institution, course.

The remaining 53 services (including checkout-service) still use in-memory stores and lose all data on restart. Checkout-service data loss is the highest-severity remaining risk (RISK-002).

**Original finding (pre-Task 7)**: All services were in-memory. This has been partially remediated.

---

## Storage Implementation Pattern

Every service implements the same pattern:

```python
# store.py
class InMemoryXStore:
    def __init__(self):
        self._data: dict[str, Model] = {}

    def create(self, item: Model) -> Model:
        self._data[item.id] = item
        return item

    def get(self, id: str) -> Model | None:
        return self._data.get(id)

    def list(self) -> list[Model]:
        return list(self._data.values())
```

```python
# main.py — always uses InMemoryXStore
store = InMemoryXStore()
service = XService(store, ...)
```

---

## store_db.py Files

`store_db.py` files are **complete, production-quality SQLite implementations** — NOT stubs. They use the `BaseRepository` mixin from `backend/services/shared/db/engine.py` which provides WAL mode, foreign keys enabled, busy timeout 5000ms, and per-tenant isolation.

**16 services actively use store_db.py** (wired in Task 7 2026-06-23):
auth, rbac, enrollment, progress, tenant, assessment, certificate, lesson, program, badge, session, user, org, cohort, institution, course.

Database paths resolved via `resolve_db_path(service_name)` using `LMS_DB_PATH` env var. No ORM, no Alembic — custom BaseRepository on Python stdlib `sqlite3`.

*Prior characterization as "stubs, never imported" was incorrect. Corrected 2026-06-23.*

---

## Data Models by Service

The following tables document the logical data shapes as implemented in each service's `models.py`. Services with wired store_db.py (see above) have corresponding SQLite schemas — field names match the model. Services without store_db.py use these as in-memory-only structures.

### auth-service

| Model | Key Fields | Notes |
|---|---|---|
| `Tenant` | `tenant_id`, `name`, `active`, `domain` | In-memory only |
| `UserCredential` | `user_id`, `tenant_id`, `organization_id`, `email`, `password_hash`, `roles[]`, `status`, `last_login_at` | In-memory only |
| `Session` | `session_id`, `user_id`, `tenant_id`, `issued_at`, `expires_at`, `refresh_expires_at`, `revoked`, `auth_method`, `assurance_level`, `last_seen_at`, `revoked_at`, `revoked_reason` | State: active/revoked/expired |
| `ResetChallenge` | `challenge_id`, `user_id`, `tenant_id`, `token`, `expires_at`, `used`, `challenge_hash`, `delivery_channel`, `attempt_count`, `max_attempts` | Token hashed for storage |
| `LoginResponse` | `session_id`, `access_token`, `refresh_token`, `user_id`, `tenant_id`, `roles[]`, `expires_in`, `token_type` | Response shape only |

Password hashing: Argon2id (primary), PBKDF2 HMAC-SHA256 (fallback).

### rbac-service

| Model | Key Fields | Notes |
|---|---|---|
| `RoleDefinition` | `role_id`, `tenant_id`, `role_key`, `display_name`, `description`, `is_system`, `status`, `version`, `created_at`, `updated_at` | Pydantic BaseModel |
| `PermissionDefinition` | `permission_id`, `permission_key`, `resource_type`, `action`, `risk_tier`, `is_assignable` | risk_tier: low/moderate/high/critical |
| `RolePermissionBinding` | `role_id`, `permission_id`, `effect`, `conditions{}` | effect: allow/deny |
| `SubjectRoleAssignment` | `assignment_id`, `tenant_id`, `subject_type`, `subject_id`, `role_id`, `scope_type`, `scope_id`, `branch_ids[]`, `starts_at`, `ends_at`, `source`, `created_by`, `revoked_at` | source: direct/group_derived/jit |
| `PolicyRule` | `policy_rule_id`, `tenant_id`, `rule_type`, `expression{}`, `priority`, `enabled` | |
| `AuthorizationDecisionLog` | `decision_id`, `tenant_id`, `principal_subject`, `permission_key`, `resource_type`, `resource_id`, `decision`, `reason_codes[]`, `policy_trace[]`, `correlation_id`, `evaluated_at` | Audit log |

SubjectType enum: `user`, `group`, `service_account`
ScopeType enum: `tenant`, `org_unit`, `course`, `program`, `cohort`, `branch`
RoleStatus enum: `active`, `disabled`, `deprecated`
RuleType enum: `sod_conflict`, `explicit_deny`, `step_up_required`, `time_window`, `network_boundary`

### tenant-service

| Model | Key Fields | Notes |
|---|---|---|
| `TenantConfiguration` | (fields from InitializeTenantConfigurationRequest) | Stored per-tenant |
| `LifecycleState` | `ACTIVE`, `SUSPENDED`, `ARCHIVED`, `DECOMMISSIONED`, `PROVISIONING` | State machine |
| `LifecycleEventResponse` | (from dataclass) | State transition history |

Lifecycle transitions:
- `ACTIVE → SUSPENDED → REACTIVATE → ACTIVE`
- `ACTIVE → ARCHIVED → DECOMMISSIONED`
- `PROVISIONING → ACTIVE`

### progress-service

| Model | Key Fields | Notes |
|---|---|---|
| `ProgressRecord` | `lesson_id`, `tenant_id`, `learner_id`, `status`, `progress_percentage`, timestamps | Lesson-level — field is `status` in code, not `completion_status` (corrected 2026-06-23) |
| `LearnerProgressSummary` | `learner_id`, `tenant_id`, course-level aggregates | Computed summary |
| `LearningPathAssignment` | `learning_path_id`, `learner_id`, `tenant_id`, status | |

status values include: `not_started`, `in_progress`, `completed`, `passed` *(field name is `status` in code; `completion_status` in prior docs was wrong)*

### enrollment-service

| Model | Key Fields | Notes |
|---|---|---|
| `Enrollment` | `id`, `tenant_id`, `learner_id`, `course_id`, `status`, `assignment_source`, `cohort_id`, `session_id`, `created_at`, `updated_at`, `enrolled_at`, `completed_at`, `dropped_at`, `deferred_at`, `expired_at` | SQLite schema has INDEX not UNIQUE on (tenant_id, learner_id, course_id) — allows re-enrollment after complete/drop. Uniqueness for ACTIVE enrollments enforced at service layer via `active_for_learner_course()` check (CAT-016). |
| `AuditLog` | `actor_id`, `action`, `enrollment_id`, `metadata`, `created_at` | Append-only |

Enrollment status transitions tracked (AUD-009 canonical path: `/transitions`).
Bulk assignment supported: returns job_id + accepted/rejected counts (202).

### checkout-service

| Model | Key Fields | Notes |
|---|---|---|
| `CheckoutSession` | `session_id`, `tenant_id`, items[], status | Lost on restart — HIGH RISK |
| `Order` | `order_id`, `tenant_id`, status, payment details | Lost on restart — HIGH RISK |

Idempotency check exists in `CheckoutService.submit_session()` — protected against removal (PROHIBITED per governance).

---

## Shared Data Models (root `shared/models/`)

The root `shared/models/` directory exports cross-service data models. Whether these are imported by `backend/services/` is unconfirmed (see OWN-002, LEGACY_AND_ARCHIVE_PLAN.md).

Key models in this layer:
- `ConfigLevel`, `ConfigOverride`, `EffectiveConfig` — configuration resolution types
- `Capability`, `AddOn`, `CapabilityPricing`, `Plan` — commercial/capability models
- `Branch`, `BranchStatus` — multi-branch operator support
- `UnifiedStudentProfile` — cross-system student data shape
- `Invoice`, `ExamSessionRecord`, `TimetableSlot` — academic operation models
- `OnboardingSession` — onboarding state

---

## Idempotency Stores

Some services maintain an idempotency store to prevent duplicate writes:

- `InMemoryIdempotencyStore` — seen in progress-service
- CheckoutService has inline idempotency logic in `submit_session()`

These stores are also in-memory and reset on restart. This means idempotency guarantees do not survive process restarts.

---

## What the Spec Says vs What Exists

The engineering spec (`docs/specs/auth-service-spec.md`) defines a canonical data model with persistent entities:

| Spec Entity | Implementation Reality |
|---|---|
| `auth_identity` table | `UserCredential` dataclass in-memory |
| `session` table | `auth_sessions` table in SQLiteAuthStore (Task 7) |
| `refresh_token_family` table | `auth_refresh_tokens` table with `parent_token_id`/`replaced_by_token_id` lineage columns |
| `refresh_token` table | Implemented as rows in `auth_refresh_tokens` |
| `password_reset_challenge` table | `auth_challenges` table in SQLiteAuthStore (Task 7) |
| `login_audit_event` table | Not observed as separate store (still in-memory log) |
| `key_metadata` table | RSA key cached in module-level variable |

*Updated 2026-06-23: auth-service now uses SQLiteAuthStore (Task 7). Sessions, refresh tokens, and challenges are now persisted.*

---

## Risk Summary

| Risk ID | Description | Severity |
|---|---|---|
| RISK-001 | All data lost on service restart | CRITICAL |
| RISK-002 | Checkout orders lost on restart — payment data unrecoverable | CRITICAL |
| RISK-003 | Auth sessions lost on restart — all users forced to re-login | HIGH |
| RISK-004 | No referential integrity — data relationships not enforced | HIGH |
| RISK-005 | Idempotency stores reset on restart — duplicate-write protection lost | HIGH |

Full risk register: see BACKEND_RISK_REGISTER.md.

---

## Open Questions (All Resolved — 2026-06-23)

| ID | Question | Answer |
|---|---|---|
| D-001 | Does checkout-service have DB persistence for orders/sessions? | **No.** checkout-service still uses `InMemoryCheckoutStore`. RISK-002 remains open. |
| Q-DB-001 | Are store_db.py stubs connected to any runtime database? | **Yes.** 16 services use complete SQLite implementations wired in Task 7. |
| Q-DB-002 | Is there an ORM or migration framework anywhere in the codebase? | **No ORM, no Alembic.** Custom `BaseRepository` on stdlib `sqlite3` in `backend/services/shared/db/engine.py`. |

---

## Related Documents

- `docs/01_backend/BACKEND_ARCHITECTURE.md` — full service architecture
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk analysis
- `docs/specs/auth-service-spec.md` — spec-level DB model (aspirational)
