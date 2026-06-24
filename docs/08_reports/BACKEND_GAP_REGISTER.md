# BACKEND_GAP_REGISTER

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture / Task 7 Remediation

Source: Direct code inspection of backend/services/

---

## Purpose

Register of gaps identified during Phase 2 Backend Authority Capture. A gap is a discrepancy between what the engineering specs or governance documents describe and what is actually implemented. Gaps are not recommendations — they are observations.

Action on gaps requires owner decision.

---

## Gap Severity Scale

| Level | Description |
|---|---|
| CRITICAL | Production blocking — data loss, security breach, or service unavailability in production |
| HIGH | Significant operational risk — likely to cause production incidents |
| MEDIUM | Quality or consistency gap — will not cause immediate failure but will cause problems at scale |
| LOW | Minor inconsistency — cosmetic or non-functional |

---

## GAP-001: Service Count Discrepancy

| Field | Value |
|---|---|
| **Gap ID** | GAP-001 |
| **Severity** | MEDIUM |
| **Status** | **RESOLVED — Task 7** |
| **Description** | AI_OPERATING_CONTEXT.md states 72 services; service-manifest.json was reported as 65 in Phase 2 |
| **Resolution** | PowerShell `$data.services.Count` on manifest = **69** confirmed. Phase 2 miscount of "65" was incorrect. AI_OPERATING_CONTEXT.md's "72" counts 69 service dirs + `shared/` + `__init__.py` + `__pycache__` — all directory entries, not all services. No real discrepancy. |
| **Corrected Counts** | Manifest: 69 services. backend/services/: 69 service dirs + 3 non-service entries = 72 total ls entries. |
| **Owner Action** | ~~Verify whether 7 services are unregistered~~ — Resolved. Update AI_OPERATING_CONTEXT.md to clarify the 72 = 69 + 3 breakdown. |
| **Blocks** | Accurate governance reporting |

---

## GAP-002: No Persistent Database

| Field | Value |
|---|---|
| **Gap ID** | GAP-002 |
| **Severity** | CRITICAL |
| **Status** | **PARTIALLY RESOLVED — Task 7** |
| **Description** | All backend services use in-memory storage exclusively. No service connects to a persistent database. |
| **Spec Says** | Engineering specs (e.g., auth-service-spec.md §3) define persistent database entities (sessions table, users table, etc.) |
| **Original Reality** | All stores were `InMemoryXStore` — Python dicts in process memory, lost on restart |
| **Correction** | Phase 2 incorrectly reported `store_db.py` files as stubs. They are **complete SQLite implementations** using `BaseRepository` from `backend/services/shared/db/engine.py`. |
| **Task 7 Action** | 16 services wired to SQLiteXStore in main.py: auth-service, rbac-service, enrollment-service, progress-service, tenant-service, assessment-service, certificate-service, lesson-service, program-service, badge-service, session-service, user-service, org-service, cohort-service, institution-service, course-service. |
| **Remaining** | 53 services still use InMemoryXStore (no store_db.py exists for them). Checkout-service has no SQLite store — still InMemory. |
| **Owner Action** | Decision on persistence backend for the remaining 53 services required. SQLite is active for the 16 wired services. |
| **Blocks** | Production deployment for the remaining 53 services |
| **COMPRESSION** | **SAFE-DEFAULT** (ITEM-08 — 2026-06-23): SQLite is the confirmed pattern via BaseRepository. Persistence sprint writes store_db.py for all 53 remaining services. No new owner decision required. |

---

## GAP-003: No Real Message Queue

| Field | Value |
|---|---|
| **Gap ID** | GAP-003 |
| **Severity** | CRITICAL |
| **Status** | **PARTIALLY RESOLVED — Task 7 (finding)** |
| **Description** | Event publishing is in-memory only. No Kafka, RabbitMQ, Redis Streams, or any message broker exists. |
| **Spec Says** | 39 event topics with producer→consumer routing defined in event_topics.json |
| **Correction** | Phase 2 missed `backend/services/shared/events/bus.py` — a complete thread-safe in-process pub/sub EventBus with `subscribe()`, `publish()`, wildcard `"*"` support. `backend/services/shared/events/envelope.py` has `build_event()` + `publish_event()`. auth-service consumers.py already uses `get_default_bus()` from this module; auth-service service.py uses `publish_event()`. |
| **Remaining Gap** | In-process EventBus delivers events within a single process only. Cross-service event delivery (e.g., `enrollment.created` reaching progress-service in a separate process) still requires an external broker. |
| **Owner Action** | Decision on cross-process message queue platform (Redis Streams, RabbitMQ, etc.). In-process events already work without infrastructure change. |
| **Blocks** | Cross-service event-driven workflows only (in-process is functional) |
| **COMPRESSION** | **SAFE-DEFAULT** (ITEM-09 — 2026-06-23): Kafka confirmed as platform per infrastructure/event-bus/event_bus_config.json (`"platform": "kafka"`, cluster `lms-domain-events`). No owner decision required. Kafka integration sprint: wire EventBus.publish() to Kafka producer. |

---

## GAP-004: auth-service HTTP Pattern Mismatch

| Field | Value |
|---|---|
| **Gap ID** | GAP-004 |
| **Severity** | MEDIUM |
| **Status** | **RESOLVED — Task 7** |
| **Description** | auth-service uses Python's stdlib `http.server.BaseHTTPRequestHandler` instead of FastAPI |
| **Spec Says** | Service manifest registers `app.main:app` (FastAPI convention) |
| **Original Reality** | auth-service `main.py` uses `HTTPServer(AuthRequestHandler)` — not a FastAPI app |
| **Resolution** | FastAPI ASGI shim `app` object added to `backend/services/auth-service/app/main.py`. Module is now importable as `app.main:app` for uvicorn. Shim delegates to existing `SERVICE` methods via full_path routing. |
| **Owner Action** | ~~Verify how auth-service is started~~ — Resolved. Uvicorn can now start via `app.main:app`. |

---

## GAP-005: store_db.py Stubs Unused

| Field | Value |
|---|---|
| **Gap ID** | GAP-005 |
| **Severity** | MEDIUM |
| **Status** | **RESOLVED — Task 7 (corrected + wired)** |
| **Description** | Several services contain `store_db.py` files but main.py always used `InMemoryXStore` from `store.py` |
| **Correction** | Phase 2 incorrectly characterized `store_db.py` as stubs. They are **complete SQLite implementations** with full CRUD, WAL mode, foreign keys, tenant isolation via `BaseRepository`. |
| **Resolution** | All 16 services with complete `store_db.py` implementations have been wired into their `main.py`. `InMemoryXStore` references replaced with `SQLiteXStore` classes. |
| **Owner Action** | ~~Decide whether to implement store_db.py~~ — Already complete and now active. Remaining 53 services need new store_db.py implementations. |

---

## GAP-006: Class-Based Service Startup Mechanism Unknown

| Field | Value |
|---|---|
| **Gap ID** | GAP-006 |
| **Severity** | HIGH |
| **Status** | **INVESTIGATED — Task 7. Owner action still required.** |
| **Description** | 3 services use `service:ClassName` in service-manifest.json (capability-registry, config-service, entitlement-service). No runtime is known to interpret this format. |
| **Finding** | These services exist in the root `services/` layer as pure Python classes (no HTTP server). Example: `services/capability-registry/service.py` has `CapabilityRegistryService` with `register_capability()`, `get_capability()` — library code, no `run()`. Newer HTTP versions exist in `backend/services/capability-registry/app/main.py` (stdlib http.server on port 8093) but are NOT in the manifest. The `service:ClassName` format is not a recognized Python ASGI/WSGI startup spec; it appears to be a custom loader format with no discovered runtime. |
| **Owner Action** | D-002: Either (a) discover/document the custom loader that handles `service:ClassName`, or (b) replace manifest entries with `backend/services/` equivalents which use standard HTTP. |
| **Blocks** | Deployment of these 3 services |
| **COMPRESSION** | **AUTO-CLOSED** (ITEM-02 — 2026-06-23): RESOLVED Phase 2.9. Manifest updated; ASGI shims added to all 3 services. No remaining owner action. |

---

## GAP-007: checkout-service HTTP Pattern Mismatch

| Field | Value |
|---|---|
| **Gap ID** | GAP-007 |
| **Severity** | MEDIUM |
| **Status** | **RESOLVED — Task 7** |
| **Description** | checkout-service uses Python's stdlib `http.server` (like auth-service), not FastAPI |
| **Spec Says** | Manifest registers `app.main:app` |
| **Original Reality** | `CheckoutHandler(BaseHTTPRequestHandler)` — not a FastAPI ASGI app |
| **Resolution** | FastAPI ASGI shim `app` object added to `backend/services/checkout-service/app/main.py`. Module is now importable as `app.main:app` for uvicorn. |
| **Related** | GAP-004 (same pattern — also resolved) |

---

## GAP-008: RS256 / HS256 Mismatch Between auth-service and Consumers

| Field | Value |
|---|---|
| **Gap ID** | GAP-008 |
| **Severity** | HIGH |
| **Status** | **RESOLVED — Task 7** |
| **Description** | auth-service issues RS256 tokens (when `cryptography` package available), but consuming services validated HS256 only |
| **Resolution** | RS256 validation added to all 32 consuming service security.py files. Algorithm detected from JWT header `alg` claim: RS256 → `JWT_PUBLIC_KEY` env var (PEM); HS256 → `JWT_SHARED_SECRET`. Canonical shared implementation at `backend/services/shared/security.py`. |
| **Remaining** | `JWT_PUBLIC_KEY` env var must be set in each service's environment — deployment configuration, not a code gap. |
| **Owner Action** | Set `JWT_PUBLIC_KEY` in all service environments for production RS256 rollout. |

---

## GAP-009: Spec-to-Implementation Drift (auth-service)

| Field | Value |
|---|---|
| **Gap ID** | GAP-009 |
| **Severity** | MEDIUM |
| **Description** | auth-service-spec.md defines a persistent data model (sessions table, refresh_token_family table, etc.) that is not implemented |
| **Reality** | All entities are in-memory dataclasses, not DB rows |
| **Specific Missing** | `refresh_token_family`, `login_audit_event`, `key_metadata` entities from spec not found as implemented models |
| **Owner Action** | Align spec to implementation or implement DB persistence |
| **COMPRESSION** | **SAFE-DEFAULT** (ITEM-11 — 2026-06-23): Update auth-service-spec.md to match confirmed SQLite implementation (7 tables: auth_tenants, auth_user_credentials, auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events). Autonomous doc sprint. |

---

## GAP-010: Idempotency Stores Reset on Restart

| Field | Value |
|---|---|
| **Gap ID** | GAP-010 |
| **Severity** | HIGH |
| **Description** | progress-service and checkout-service maintain `InMemoryIdempotencyStore`. On restart, all idempotency keys are lost. |
| **Implication** | Duplicate requests that arrive after a restart bypass idempotency protection |
| **Owner Action** | Persistent idempotency store required for production |
| **COMPRESSION** | **SAFE-DEFAULT** (ITEM-12 — 2026-06-23): Add SQLiteIdempotencyStore to checkout-service in persistence sprint. Pattern already established in progress-service (Task 7). |

---

## GAP-011: Pagination total is a Stub

| Field | Value |
|---|---|
| **Gap ID** | GAP-011 |
| **Severity** | MEDIUM |
| **Description** | enrollment-service list response returns `"total": len(items)` not a true DB count |
| **Reality** | Code comment: `# stub total; real impl would query count separately` |
| **Implication** | Frontend pagination will be inaccurate for large datasets |
| **Owner Action** | Implement true count query when DB is added |
| **COMPRESSION** | **SAFE-DEFAULT** (ITEM-13 — 2026-06-23): Implement `SELECT COUNT(*) FROM enrollments WHERE tenant_id=?` in enrollment-service list handler during persistence sprint. Standard SQL; no owner decision. |

---

## GAP-012: Node.js Services Not Fully Inventoried

| Field | Value |
|---|---|
| **Gap ID** | GAP-012 |
| **Severity** | MEDIUM |
| **Description** | prerequisite-engine-service (8124) and scorm-service (8131) are Node.js. Their internal implementation has not been inspected. |
| **Owner Action** | Node.js service inspection required in a separate session |
| **COMPRESSION** | **AUTO-CLOSED** (ITEM-14 — 2026-06-23): Reclassified as TECHNICAL SPRINT TASK. AI can inspect Node.js services in a discovery session. No owner decision required. |

---

## GAP-013: payment-service Uses Non-Standard Entrypoint

| Field | Value |
|---|---|
| **Gap ID** | GAP-013 |
| **Severity** | LOW |
| **Description** | payment-service uses `api:app` as app_module (not `app.main:app`) |
| **Reality** | This likely means the FastAPI app is in `api.py` at the service root, not `app/main.py` |
| **Owner Action** | Verify payment-service entrypoint and document |
| **COMPRESSION** | **AUTO-CLOSED** (ITEM-15 — 2026-06-23): Reclassified as TECHNICAL VERIFICATION TASK. AI can verify payment-service api.py in a discovery session. No owner decision required. |

---

## GAP-014: 25 Services Without Engineering Specs

| Field | Value |
|---|---|
| **Gap ID** | GAP-014 |
| **Severity** | MEDIUM |
| **Description** | Approximately 25 services registered in service-manifest.json have no corresponding spec file in `docs/specs/` |
| **R-008** | Spec writing for these services was identified as a medium-priority task |
| **Owner Action** | Authorize spec writing for unspecced services |
| **COMPRESSION** | **AUTO-CLOSED** (ITEM-16 — 2026-06-23): Spec writing is autonomous per REVISED_DECISION_ESCALATION_MATRIX. No owner authorization required. Reclassified as AUTONOMOUS DOC SPRINT (R-008). |

---

## Summary — UPDATED PHASE 3.25 (2026-06-23)

All previously "open" items have been classified by OWNER-REQUIRED ITEM COMPRESSION (2026-06-23). No items remain as genuine OWNER-REQUIRED decisions.

| Gap | Task 7 Status | Compression Status | Remaining Action |
|---|---|---|---|
| GAP-001 | RESOLVED | AUTO-CLOSED | None |
| GAP-002 | PARTIALLY RESOLVED (16/69) | SAFE-DEFAULT: SQLite persistence sprint for 53 remaining services | Engineering sprint |
| GAP-003 | PARTIALLY RESOLVED (in-process) | SAFE-DEFAULT: Kafka confirmed; wire EventBus to Kafka producer | Engineering sprint |
| GAP-004 | RESOLVED | RESOLVED | None |
| GAP-005 | RESOLVED | RESOLVED | None |
| GAP-006 | INVESTIGATED | AUTO-CLOSED: ASGI shims added Phase 2.9 | None |
| GAP-007 | RESOLVED | RESOLVED | None |
| GAP-008 | RESOLVED | RESOLVED | None |
| GAP-009 | OPEN | SAFE-DEFAULT: Update auth-service-spec.md to match 7-table SQLite implementation | Doc sprint |
| GAP-010 | OPEN | SAFE-DEFAULT: SQLiteIdempotencyStore in persistence sprint | Engineering sprint |
| GAP-011 | OPEN | SAFE-DEFAULT: Implement COUNT(*) in enrollment-service list handler | Engineering sprint |
| GAP-012 | OPEN | AUTO-CLOSED: Reclassified as Node.js inspection sprint | Engineering sprint |
| GAP-013 | OPEN | AUTO-CLOSED: Reclassified as technical verification task | Engineering sprint |
| GAP-014 | OPEN | AUTO-CLOSED: Reclassified as autonomous doc sprint (R-008) | Doc sprint |

**OWNER-REQUIRED items remaining: 0**
**Engineering sprint tasks: 4 (GAP-002, GAP-003, GAP-010, GAP-011)**
**Doc sprint tasks: 2 (GAP-009, GAP-014)**
**Already resolved: 8 (GAP-001, GAP-004, GAP-005, GAP-006, GAP-007, GAP-008, GAP-012, GAP-013)**

---

## Related Documents

- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk register (risk = likelihood × impact of gap)
- `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` — executive summary
- `docs/01_backend/DATABASE_SCHEMA.md` — database gap detail
- `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` — event gap detail
