# TBD RESOLUTION REGISTER

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Source: Direct code inspection + five-domain audit

Open questions and TBDs from documentation that are now answerable from code evidence. Each item has a code-derived answer and can be closed in its source document.

---

## TBD-001: D-001 — Does checkout-service have DB persistence?

| Field | Value |
|---|---|
| **ID** | TBD-001 |
| **Source** | DATABASE_SCHEMA.md Open Questions: D-001 |
| **Question** | "Does checkout-service have DB persistence?" |
| **Answer** | **No.** checkout-service has no `store_db.py`. It still uses `InMemoryCheckoutStore`. Payment data (sessions, orders) is lost on service restart. This remains an open RISK-002 (CRITICAL). |
| **Action** | Close D-001 in DATABASE_SCHEMA.md with this answer. |

---

## TBD-002: Q-DB-001 — Are store_db.py files actively used?

| Field | Value |
|---|---|
| **ID** | TBD-002 |
| **Source** | DATABASE_SCHEMA.md Open Questions: Q-DB-001; DATABASE_DISCOVERY_REPORT.md |
| **Question** | "Are store_db.py files actively used in any service?" |
| **Answer** | **Yes.** 16 services have complete SQLite implementations now wired into main.py: auth, rbac, enrollment, progress, tenant, assessment, certificate, lesson, program, badge, session, user, org, cohort, institution, course. |
| **Action** | Close Q-DB-001 with this answer. Remove characterization of store_db.py as "stubs." |

---

## TBD-003: Q-DB-002 — Is there an ORM or migration framework?

| Field | Value |
|---|---|
| **ID** | TBD-003 |
| **Source** | DATABASE_SCHEMA.md Open Questions: Q-DB-002 |
| **Question** | "Is there an ORM or migration framework (SQLAlchemy, Alembic, etc.)?" |
| **Answer** | **No ORM. No migration framework.** The persistence layer uses a custom `BaseRepository` mixin in `backend/services/shared/db/engine.py` built on Python stdlib `sqlite3`. WAL mode, foreign keys, and busy timeout are set via `engine.py`. No Alembic, no SQLAlchemy, no asyncpg. Database paths resolved via `resolve_db_path(service_name)` using `LMS_DB_PATH` env var. |
| **Action** | Close Q-DB-002 with this answer. |

---

## TBD-004: Q-DB-003 — Is there an external persistence layer?

| Field | Value |
|---|---|
| **ID** | TBD-004 |
| **Source** | DATABASE_DISCOVERY_REPORT.md |
| **Question** | "Is there an external persistence layer (PostgreSQL, Redis, etc.)?" |
| **Answer** | **No external persistence.** Only SQLite (file-backed, per-service). No DATABASE_URL, no POSTGRES_URI, no REDIS_URL found in any service's code. Infrastructure env files reference postgresql and rabbitmq with placeholder credentials — these appear to be future-state configuration not yet wired to any service. |
| **Action** | Close with this answer. Note that infrastructure/deployment/env/ files contain placeholder credentials for a planned PostgreSQL/RabbitMQ deployment. |

---

## TBD-005: D-002 — What runtime interprets `service:ClassName`?

| Field | Value |
|---|---|
| **ID** | TBD-005 |
| **Source** | BACKEND_GAP_REGISTER.md GAP-006; AI_OPERATING_CONTEXT.md |
| **Question** | "What runtime interprets `service:ClassName` format in manifest for capability-registry, config-service, entitlement-service?" |
| **Answer** | **No runtime found.** Exhaustive search of `infrastructure/service-discovery/`, `scripts/`, and all Python files found no custom loader for `service:ClassName`. The root `services/` layer for these 3 services contains pure Python classes (no HTTP server, no `run()` function). These services cannot be deployed as HTTP services using the current manifest entry without a custom runner not present in the repository. Newer stdlib HTTP versions exist in `backend/services/` but are unregistered. |
| **Action** | Update GAP-006 with this confirmed finding. Escalate to owner as OA-004. |

---

## TBD-006: Refresh Token Family Tracking — "not found" in Spec-vs-Impl Table

| Field | Value |
|---|---|
| **ID** | TBD-006 |
| **Source** | DATABASE_SCHEMA.md spec-vs-implementation table showing `refresh_token_family = "not found"` |
| **Answer** | **Implemented.** `auth_refresh_tokens` table in auth-service/app/store_db.py (lines ~140–160) includes `parent_token_id` and `replaced_by_token_id` columns, implementing token family lineage. The family tracking is via FK linkage, not a separate `refresh_token_family` table as the spec literally named it. |
| **Action** | Update DATABASE_SCHEMA.md table to show `auth_refresh_tokens` with lineage columns as the implemented equivalent. |

---

## TBD-007: Login Response Shape — "verify against code" note

| Field | Value |
|---|---|
| **ID** | TBD-007 |
| **Source** | AUTH_AND_TENANCY_CONTRACT.md, DATA_SHAPE_REGISTRY.md — login response shape marked with verification TODOs in some prior audits |
| **Answer** | **Verified.** Actual login response (auth-service/app/service.py:144–152): `{"session_id", "user": {"user_id", "tenant_id"}, "access_token", "token_type": "Bearer", "expires_in": 900, "refresh_token", "refresh_expires_in": 604800}`. Key differences from documented shape: `user_id`/`tenant_id` are nested under `"user"` object; `roles` is NOT in the response (only in JWT); `refresh_expires_in` is undocumented. |
| **Action** | Correct both documents. See UCR-007. |

---

## TBD-008: JWT User Identifier Claim Name

| Field | Value |
|---|---|
| **ID** | TBD-008 |
| **Source** | AUTH_AND_TENANCY_CONTRACT.md — "user identifier in JWT" not explicitly named |
| **Answer** | **Confirmed: `sub` claim.** auth-service/app/service.py:111 sets `"sub": user.user_id`. The JWT standard `sub` claim carries the user ID. Frontend code reading `payload.user_id` will get `undefined` — must read `payload.sub`. |
| **Action** | Add explicit statement to AUTH_AND_TENANCY_CONTRACT.md: "User identifier is in the `sub` JWT claim." |

---

## TBD-009: EventBus Implementation Status

| Field | Value |
|---|---|
| **ID** | TBD-009 |
| **Source** | EVENT_AND_QUEUE_ARCHITECTURE.md, EVENT_DISCOVERY_REPORT.md — "in-memory event bus" characterization unclear |
| **Answer** | **Confirmed: Full in-process EventBus exists.** `backend/services/shared/events/bus.py` implements `EventBus` with thread-safe `subscribe()`, `publish()`, wildcard `"*"` support, and `get_default_bus()` singleton. `envelope.py` provides `build_event()` and `publish_event()`. auth-service consumers.py registers 9 topic subscriptions using `get_default_bus()`. This is NOT `InMemoryEventPublisher` — it is a separate, more capable implementation that was missed in Phase 2. Cross-process delivery still requires an external broker. |
| **Action** | Update EVENT_AND_QUEUE_ARCHITECTURE.md to document the existing in-process EventBus. |

---

## TBD-010: P1-SEC-002 — Are infrastructure env files sensitive?

| Field | Value |
|---|---|
| **ID** | TBD-010 |
| **Source** | REPOSITORY_RESTRUCTURING_PLAN.md P1-SEC-002: "Verify infrastructure/*.env content" (PENDING) |
| **Answer** | **Not sensitive. Safe to leave.** `infrastructure/deployment/env/common.env` and `services.env` contain only placeholder/local-dev credentials: `lms:lms@postgres`, `guest:guest@rabbitmq`, OTEL endpoints. No production secrets. No git history risk. |
| **Action** | Close P1-SEC-002 as DONE. |

---

## TBD-011: Tenant Model Fields — "2 additional fields per anchor"

| Field | Value |
|---|---|
| **ID** | TBD-011 |
| **Source** | AUTH_AND_TENANCY_CONTRACT.md — mentions "6-field tenant model (PROTECTED)" but only lists 4 fields, saying "(2 additional fields per anchor)" without naming them |
| **Answer** | **Fields identified.** From docs/anchors/tenant-contract.md (TIER 1) and tenant-service/app/schemas.py: the 6 fields are `tenant_id`, `name`, `country_code`, `segment_type`, `plan_type`, `addon_flags`. The missing 2 (not in the 4-field DATA_SHAPE_REGISTRY entry) are `segment_type` and one of `country_code`/`plan_type`/`addon_flags`. Full 6-field list: `{tenant_id, name, country_code, segment_type, plan_type, addon_flags}`. |
| **Action** | Update AUTH_AND_TENANCY_CONTRACT.md to list all 6 fields explicitly. Update DATA_SHAPE_REGISTRY.md tenant shape. |

---

## TBD-012: docs/governance/spec_index.json Consumer

| Field | Value |
|---|---|
| **ID** | TBD-012 |
| **Source** | REPOSITORY_RESTRUCTURING_PLAN.md P3-GITIGNORE-001: "Verify spec_index.json consumer" |
| **Answer** | **CLOSED (Phase 3.25 — 2026-06-23).** `scripts/` directory: no Python scripts exist in the repository (Glob search returned empty). `docs/governance/spec_index.json` is a stale pre-governance documentation catalog generated circa 2026-03-31. It references files using old underscore naming conventions (`capability_resolution.md`, `doc_precedence.md`) and pre-normalization paths (e.g., `docs/anchors/capability_resolution.md` vs current `docs/anchors/capability-resolution.md`). These files were renamed during governance normalization. The index has zero current consumers. It is a historical artifact — no code reads it, no CI process consumes it, no tool references it. **Action: No action required. File may be left in place as historical artifact or deleted at discretion.** |
| **Action** | CLOSED. No consumer exists. |

---

## Summary

| Status | Count |
|---|---|
| Resolved — doc correction only | 10 (TBD-001 through TBD-011 except TBD-012) |
| Resolved — no consumer (Phase 3.25) | 1 (TBD-012) |
| **Total** | **12** |
| **Open** | **0** |

All 12 TBDs are now closed. Documentation corrections for TBD-001 through TBD-011 are tracked in DOC_DRIFT_REGISTER.md and UNVERIFIED_CLAIMS_REGISTER.md.
