# DOC DRIFT REGISTER

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Source: Direct code inspection + five-domain audit

Documents that were once accurate but have drifted from code reality due to code changes (primarily Task 7). These are not wrong by intent — they were correct when written and need updating to match the current codebase.

---

## DDR-001: DATABASE_SCHEMA.md — Persistence State Stale

| Field | Value |
|---|---|
| **ID** | DDR-001 |
| **Severity** | CRITICAL |
| **Document** | docs/01_backend/DATABASE_SCHEMA.md |
| **When Accurate** | Phase 2 Backend Authority Capture (pre-Task 7) |
| **Drift Cause** | Task 7 wired 16 services to SQLite stores |
| **Stale Claims** | Lines 19, 56: "All services use in-memory exclusively," "store_db.py = unused stubs" |
| **Fix Type** | Documentation correction |

---

## DDR-002: DATABASE_DISCOVERY_REPORT.md — All InMemory Claim

| Field | Value |
|---|---|
| **ID** | DDR-002 |
| **Severity** | CRITICAL |
| **Document** | docs/08_reports/DATABASE_DISCOVERY_REPORT.md |
| **Drift Cause** | Task 7 |
| **Stale Claims** | Line 21: "No persistent database exists in any backend service"; evidence table showing all 6 sample services as InMemoryXStore; store_db.py characterization as "never imported" |
| **Fix Type** | Documentation correction |

---

## DDR-003: AUTH_AND_TENANCY_CONTRACT.md — RS256 Table

| Field | Value |
|---|---|
| **ID** | DDR-003 |
| **Severity** | HIGH |
| **Document** | docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md |
| **Drift Cause** | Task 7 — RS256 added to 33 consuming services |
| **Stale Claims** | Lines 49–61: Table showing rbac-service, tenant-service, etc. as "HS256 only, cannot validate RS256." "Security debt" paragraph describing the mismatch. |
| **Fix Type** | Documentation correction |

---

## DDR-004: AUTH_AND_TENANCY_CONTRACT.md — Session Storage

| Field | Value |
|---|---|
| **ID** | DDR-004 |
| **Severity** | HIGH |
| **Document** | docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md |
| **Drift Cause** | Task 7 — auth-service switched to SQLiteAuthStore |
| **Stale Claims** | Line 102: "Sessions stored in InMemoryAuthStore. All sessions lost on restart." |
| **Fix Type** | Documentation correction |

---

## DDR-005: AUTH_AND_TENANCY_CONTRACT.md — Open Issues Risk IDs

| Field | Value |
|---|---|
| **ID** | DDR-005 |
| **Severity** | MEDIUM |
| **Document** | docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md |
| **Stale Claims** | Open Issues table references RISK-006, RISK-007, RISK-008, RISK-003 — IDs that don't match BACKEND_RISK_REGISTER.md's actual IDs. Also RISK-004 (RS256 mismatch) is now mitigated — listed as open. |
| **Fix Type** | Documentation correction — align IDs, close resolved items |

---

## DDR-006: FULLSTACK_STITCHING_CONTRACT.md — Cross-Cutting Facts

| Field | Value |
|---|---|
| **ID** | DDR-006 |
| **Severity** | HIGH |
| **Document** | docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md |
| **Drift Cause** | Task 7 |
| **Stale Claims** | Phase 2 Addendum table: "All storage is in-memory: Yes" and "All events are in-memory: Yes" |
| **Fix Type** | Documentation correction |

---

## DDR-007: SECURITY_DISCOVERY_REPORT.md — HS256-Only Services

| Field | Value |
|---|---|
| **ID** | DDR-007 |
| **Severity** | HIGH |
| **Document** | docs/08_reports/SECURITY_DISCOVERY_REPORT.md |
| **Drift Cause** | Task 7 — RS256 added to 33 services |
| **Stale Claims** | Lines 27–33: rbac-service, checkout-service, tenant-service and others listed as "HS256 only" |
| **Fix Type** | Documentation correction |

---

## DDR-008: SERVICE_CATALOG.md — Service Count and Non-Standard Table

| Field | Value |
|---|---|
| **ID** | DDR-008 |
| **Severity** | HIGH |
| **Document** | docs/01_backend/SERVICE_CATALOG.md |
| **Drift Cause** | Phase 2 miscount (65 vs 69) + Task 7 resolved auth/checkout ASGI gap, but notification-service gap was never captured |
| **Stale Claims** | Line 15: "65 services"; summary table totalling wrong; "Non-Standard Services" table missing notification-service; auth-service and checkout-service notes about "no app object" are now stale (ASGI shims added) |
| **Fix Type** | Documentation correction |

---

## DDR-009: BACKEND_ARCHITECTURE_REPORT.md — Service Count

| Field | Value |
|---|---|
| **ID** | DDR-009 |
| **Severity** | MEDIUM |
| **Document** | docs/08_reports/BACKEND_ARCHITECTURE_REPORT.md |
| **Stale Claims** | Line 21: "65 registered services" |
| **Fix Type** | Documentation correction |

---

## DDR-010: API_DISCOVERY_REPORT.md — Service Count

| Field | Value |
|---|---|
| **ID** | DDR-010 |
| **Severity** | MEDIUM |
| **Document** | docs/08_reports/API_DISCOVERY_REPORT.md |
| **Stale Claims** | Line 200: "approximately 40 of 65 services" |
| **Fix Type** | Documentation correction |

---

## DDR-011: BACKEND_AUTHORITY_CAPTURE_REPORT.md — Service Count (×6)

| Field | Value |
|---|---|
| **ID** | DDR-011 |
| **Severity** | MEDIUM |
| **Document** | docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md |
| **Stale Claims** | "65 services" appears approximately 6 times (lines 42, 104, 120, 154, 173, 198, 222) |
| **Fix Type** | Documentation correction |

---

## DDR-012: REPOSITORY_TREE_INVENTORY.md — Stale Counts and Directory Names

| Field | Value |
|---|---|
| **ID** | DDR-012 |
| **Severity** | LOW |
| **Document** | docs/08_reports/REPOSITORY_TREE_INVENTORY.md |
| **Stale Claims** | "70 named services" (should be 69); "docs/01_backend/ — EMPTY" (now has 8 files); "docs/03_ops/" (actual dir is docs/03_fullstack_contracts/) |
| **Fix Type** | Documentation correction |

---

## DDR-013: GAP-002 / GAP-005 in BACKEND_GAP_REGISTER.md (Already Updated)

| Field | Value |
|---|---|
| **ID** | DDR-013 |
| **Severity** | INFO |
| **Document** | docs/08_reports/BACKEND_GAP_REGISTER.md |
| **Status** | ALREADY UPDATED in Task 7 — GAP-002 marked PARTIALLY RESOLVED, GAP-005 marked RESOLVED |

---

## DDR-014: auth-service-storage-contract.md — Missing auth_tenants Table

| Field | Value |
|---|---|
| **ID** | DDR-014 |
| **Severity** | LOW |
| **Document** | docs/data/auth-service-storage-contract.md |
| **Gap** | auth_tenants table (tenant_id, name, active) exists in store_db.py but not documented in the contract |
| **Fix Type** | Documentation addition |

---

## DDR-015: auth-service-storage-contract.md — Missing refresh_expires_at Column

| Field | Value |
|---|---|
| **ID** | DDR-015 |
| **Severity** | LOW |
| **Document** | docs/data/auth-service-storage-contract.md |
| **Gap** | auth_sessions table in store_db.py includes `refresh_expires_at` column not in the contract |
| **Fix Type** | Documentation addition |

---

## DDR-016: DATABASE_SCHEMA.md — Column-Level Drifts

| Field | Value |
|---|---|
| **ID** | DDR-016 |
| **Severity** | MEDIUM |
| **Document** | docs/01_backend/DATABASE_SCHEMA.md |
| **Specific drifts** | (1) Enrollment model has `version` field — not in SQLite schema; (2) ProgressRecord uses `completion_status` — code uses `status`; (3) course `organization_id` in docs — code uses `institution_id` |
| **Fix Type** | Documentation correction |

---

## DDR-017: core-lms-schema.md — organization_id vs institution_id

| Field | Value |
|---|---|
| **ID** | DDR-017 |
| **Severity** | MEDIUM |
| **Document** | docs/data/core-lms-schema.md |
| **Stale Claims** | Courses table FK = `organization_id`. Actual store_db.py uses `institution_id`. |
| **Fix Type** | Documentation correction |

---

---

## DDR-018: EVENT_AND_QUEUE_ARCHITECTURE.md — InMemoryEventPublisher Misdescription

| Field | Value |
|---|---|
| **ID** | DDR-018 |
| **Severity** | HIGH |
| **Document** | docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md |
| **Stale Claims** | Lines 22–24: "Every service uses InMemoryEventPublisher()… each service has its own copy" |
| **Reality** | All 68 non-shared services use `get_default_bus()` singleton from `backend/services/shared/events/bus.py` — one shared in-process EventBus, not 68 per-service InMemoryEventPublisher instances |
| **Fix Type** | Documentation correction |

---

## DDR-019: EVENT_DISCOVERY_REPORT.md — InMemoryEventPublisher Misdescription

| Field | Value |
|---|---|
| **ID** | DDR-019 |
| **Severity** | HIGH |
| **Document** | docs/08_reports/EVENT_DISCOVERY_REPORT.md |
| **Stale Claims** | Line 38: same InMemoryEventPublisher per-service misdescription |
| **Fix Type** | Documentation correction |

---

## DDR-020: EVENT_AND_QUEUE_ARCHITECTURE.md — Envelope Fields

| Field | Value |
|---|---|
| **ID** | DDR-020 |
| **Severity** | HIGH |
| **Document** | docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md lines 58–64 |
| **Stale Claims** | Envelope: `occurred_at`, `version`, 7 fields |
| **Reality** | Code (`shared/events/envelope.py`): `timestamp`, `schema_version`, 10 fields (adds `topic`, `correlation_id`, `metadata`) |
| **Fix Type** | Documentation correction |

---

## DDR-021: event_bus_config.json — Claims Kafka (Aspirational Only)

| Field | Value |
|---|---|
| **ID** | DDR-021 |
| **Severity** | MEDIUM |
| **Document** | infrastructure/event-bus/event_bus_config.json |
| **Stale Claims** | `"platform": "kafka"` with 3 bootstrap servers and schema registry |
| **Reality** | No Kafka client in any Python service — in-process EventBus only. This file is aspirational deployment config. |
| **Fix Type** | Add header comment to file: `# ASPIRATIONAL — not implemented; actual implementation uses in-process EventBus` |

---

## DDR-022: common.env — External Service URLs Aspirational

| Field | Value |
|---|---|
| **ID** | DDR-022 |
| **Severity** | HIGH |
| **Document** | infrastructure/deployment/env/common.env |
| **Stale Claims** | DATABASE_URL=postgresql, REDIS_URL=redis, EVENT_BUS_URL=amqp |
| **Reality** | No service uses these protocols. Actual env vars in use: JWT_SHARED_SECRET, JWT_PUBLIC_KEY, LMS_DB_PATH. The postgresql/redis/amqp URLs are future-state deployment targets. |
| **Fix Type** | Add header comment to file noting aspirational vs current env vars |

---

## DDR-023: EVENT_AND_QUEUE_ARCHITECTURE.md — Consumer Handlers All Stubs

| Field | Value |
|---|---|
| **ID** | DDR-023 |
| **Severity** | HIGH |
| **Document** | docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md |
| **Stale Claims** | Consumer handlers described as functional business logic |
| **Reality** | auth-service consumers.py line 1: "business logic is stub (logging only). Full implementation deferred to event-sprint." All 68 consumers.py files contain only logging stubs. |
| **Fix Type** | Add note to EVENT_AND_QUEUE_ARCHITECTURE.md: "Consumer handlers are currently logging stubs — business logic deferred to event-sprint." |

---

## Summary by Document

| Document | Drift Items | Priority |
|---|---|---|
| DATABASE_SCHEMA.md | DDR-001, DDR-016 | CRITICAL + MEDIUM |
| DATABASE_DISCOVERY_REPORT.md | DDR-002 | CRITICAL |
| AUTH_AND_TENANCY_CONTRACT.md | DDR-003, DDR-004, DDR-005 | HIGH × 2 + MEDIUM |
| FULLSTACK_STITCHING_CONTRACT.md | DDR-006 | HIGH |
| SECURITY_DISCOVERY_REPORT.md | DDR-007 | HIGH |
| SERVICE_CATALOG.md | DDR-008 | HIGH |
| BACKEND_ARCHITECTURE_REPORT.md | DDR-009 | MEDIUM |
| API_DISCOVERY_REPORT.md | DDR-010 | MEDIUM |
| BACKEND_AUTHORITY_CAPTURE_REPORT.md | DDR-011 | MEDIUM |
| REPOSITORY_TREE_INVENTORY.md | DDR-012 | LOW |
| auth-service-storage-contract.md | DDR-014, DDR-015 | LOW |
| core-lms-schema.md | DDR-017 | MEDIUM |
| EVENT_AND_QUEUE_ARCHITECTURE.md | DDR-018, DDR-020, DDR-023 | HIGH × 3 |
| EVENT_DISCOVERY_REPORT.md | DDR-019 | HIGH |
| event_bus_config.json | DDR-021 | MEDIUM |
| common.env | DDR-022 | HIGH |
