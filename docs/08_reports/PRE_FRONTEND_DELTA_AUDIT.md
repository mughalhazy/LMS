# PRE-FRONTEND DOC-TO-CODE DELTA AUDIT

Status: Complete
Date: 2026-06-23
Phase: Pre-Frontend
Owner: AI (Human review required for owner-approval items)
Verdict: CONDITIONAL GO — see PRE_FRONTEND_READINESS_REPORT.md

---

## 1. Objective

Full comparison of all project documentation against the actual repository code before Frontend Authority Capture begins. Goal: ensure frontend engineers read contracts that accurately describe what the code does.

Scope: root files, backend source, tests, configs, scripts, CI/CD, deployment, DB/migration, generated artifacts, legacy/archive, docs, reports, registers, governance.

---

## 2. Method

Five parallel domain audits executed by specialized forks:

| Domain | Fork | Status |
|---|---|---|
| Service/API (service catalog, API contract, routing) | Fork 1 | Complete |
| Auth/Contracts (JWT, login, tenant shape, data registry) | Fork 2 | Complete |
| Database/Persistence (schemas, stores, migrations) | Fork 3 | Complete |
| Repository Hygiene (inventory, legacy layer, cross-refs) | Fork 5 | Complete |
| Events/Infrastructure (event bus, envelope, env files, scripts) | Fork 4 (retry) | Complete |

Each fork performed direct code inspection against the relevant documentation.

---

## 3. Summary Statistics

| Metric | Value |
|---|---|
| Total deltas found | 58 |
| Doc-fix only (safe, immediate) | 44 |
| Owner-approval required | 13 |
| Pending (1 outstanding TBD) | 1 |
| CRITICAL severity | 7 |
| HIGH severity | 23 |
| MEDIUM severity | 20 |
| LOW severity | 8 |

---

## 4. Findings by Domain

### 4.1 Auth / JWT

**Critical:**
- Login response shape is wrong. `user_id`/`tenant_id` are nested under a `"user"` sub-object. `roles` is not in the response. `refresh_expires_in` is undocumented. (UCR-007)
- JWT user identifier is `sub` claim, not `user_id`. Frontend reading `payload.user_id` gets `undefined`. (UCR-008)

**High:**
- RS256 table in AUTH_AND_TENANCY_CONTRACT.md shows consuming services as HS256-only — Task 7 fixed all 33. (DDR-003)
- Session storage claim "InMemoryAuthStore" — now SQLiteAuthStore. (DDR-004)
- Tenant canonical fields: DATA_SHAPE_REGISTRY shows `active`/`domain` — anchor + code use `country_code`/`segment_type`/`plan_type`/`addon_flags`. (UCR-009)

**Medium:**
- Undocumented JWT claims: `scope: "lms.api"`, `sid` + `session_id` duplication, refresh token `family_id` / `token_type: "refresh"`.
- AUTH_AND_TENANCY_CONTRACT.md Open Issues table has wrong risk ID references.

### 4.2 Service / API

**Critical:**
- API_CONTRACT.md covers only 6 of 69 services (9%). (UDC-001)

**High:**
- Service count is 69, not 65 — appears in 7+ documents. (UCR-001)
- notification-service is a third stdlib http.server service with no ASGI shim — not documented in Non-Standard Services table. Cannot start with uvicorn. (UCR-014)
- session-service uses `/api/v2/sessions` prefix — undocumented exception to v1 convention. (UDC-005)
- org-service owns /organizations, /departments, AND /teams — catalog says "hierarchy only". (UDC-006)
- assessment-service owns /attempts routes — overlap with attempt-service. (UDC-007)
- course-service `CreateCourseRequest` embeds tenant context fields in body — novel undocumented pattern. (UDC-003)

**Medium:**
- rbac-service health path: documented as `/health`, actual is `/api/v1/rbac/health`.
- service:ClassName manifest entries — no runtime found; 3 services undeployable.

### 4.3 Database / Persistence

**Critical:**
- DATABASE_SCHEMA.md and DATABASE_DISCOVERY_REPORT.md both claim "no persistent database exists" — 16 services now use SQLite. (UCR-002, DDR-001, DDR-002)
- store_db.py characterized as "stub implementations, never imported" — 16 are complete and wired. (UCR-003)

**High:**
- Enrollments unique constraint documented but not enforced in SQLite schema. (OA-003)

**Medium:**
- Enrollment `version` field documented but absent from SQLite schema.
- `completion_status` in docs, `status` in code (progress-service).
- `organization_id` in docs, `institution_id` in code (courses table).
- auth_tenants table and `refresh_expires_at` column missing from auth-service-storage-contract.md.
- `refresh_token_family` table listed as "not found" — implemented as `auth_refresh_tokens` with lineage columns.

### 4.4 Events / Queue

**High:**
- EVENT_AND_QUEUE_ARCHITECTURE.md and EVENT_DISCOVERY_REPORT.md both describe per-service `InMemoryEventPublisher`. Reality is a shared in-process `EventBus` singleton (`backend/services/shared/events/bus.py`). Architectural description is wrong. (D-EV-001/002)
- Event envelope: docs say `occurred_at`/`version`/7 fields. Code uses `timestamp`/`schema_version`/10 fields (adds `topic`, `correlation_id`, `metadata`). (D-EV-003, UCR-010)
- All consumer handlers are logging stubs — docs do not note this. (D-EV-006)
- event_topics.json canonical names (`lms.<domain>.<event>.v1`) not used consistently in code. (D-EV-006)
- FULLSTACK_STITCHING_CONTRACT.md: "All events are in-memory — InMemoryEventPublisher: Yes" — wrong implementation name. (D-EV-010)

**Medium:**
- `event_bus_config.json` claims `"platform": "kafka"` — no Kafka client in any service. Aspirational only.
- `common.env`: DATABASE_URL=postgresql, REDIS_URL, EVENT_BUS_URL=amqp — none implemented in code.

### 4.5 Repository Hygiene

**High:**
- SECURITY_DISCOVERY_REPORT.md shows HS256-only for consuming services — stale after Task 7. (DDR-007)
- FULLSTACK_STITCHING_CONTRACT.md Phase 2 Addendum: "All storage is in-memory: Yes" — 16 services use SQLite. (DDR-006)

**Medium:**
- REPOSITORY_TREE_INVENTORY.md: wrong dir name (03_ops vs 03_fullstack_contracts), docs/01_backend listed as empty (has 8 files), 70 services (should be 69).
- docs/api/ legacy files have no supersession notices pointing to docs/01_backend/API_CONTRACT.md.
- Root services/ layer is partially active: entitlement-service and subscription-service imported (guarded) by backend services; 5 backend services import from root shared/.
- BACKEND_ARCHITECTURE.md missing: cross-layer import topology, shared/security.py documentation.
- Two EventEnvelope definitions (course-service local vs shared dataclass). (OA-007)
- Dockerfiles and CI/CD files exist in infrastructure/ despite AI_OPERATING_CONTEXT.md constraint.
- analytics-ingestion-service in event docs vs event-ingestion-service actual directory.

---

## 5. Owner Approval Items

10 items require owner decision before Phase 3 can proceed. Full details in OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md.

| ID | Topic | Priority |
|---|---|---|
| OA-001 | notification-service ASGI shim (code change, like Task 7) | HIGH |
| OA-002 | branch_ids missing from AssignmentCreateRequest | MEDIUM |
| OA-003 | Enrollments unique constraint absent from SQLite | MEDIUM |
| OA-004 | service:ClassName runtime — 3 services undeployable | HIGH |
| OA-005 | assessment-service vs attempt-service route overlap | HIGH |
| OA-006 | Root services/ classification (entitlement + subscription active) | MEDIUM |
| OA-007 | Two competing EventEnvelope definitions | MEDIUM |
| OA-008 | integrations/payment/ vs integrations/payments/ overlap | LOW |
| OA-009 | session-service v2 API prefix — doc decision or standardize | MEDIUM |
| OA-010 | docs/qc/ Python scripts — move to validation/ | LOW |

---

## 6. TBD Items Resolved

11 of 12 open TBDs in documentation resolved from code evidence. See TBD_RESOLUTION_REGISTER.md.

Key resolutions:
- D-001: checkout-service has no DB persistence (still InMemory)
- Q-DB-001: store_db.py are complete and wired (16 services)
- Q-DB-002: No ORM/migration; custom BaseRepository on stdlib sqlite3
- Q-DB-003: No external DB; common.env postgresql/redis are aspirational
- D-002: No runtime for service:ClassName format — confirmed
- Login response shape: verified from code
- JWT sub claim: confirmed
- EventBus: confirmed full implementation
- P1-SEC-002: infrastructure env files are placeholder-only, safe to leave
- Tenant 6-field model: all 6 fields identified

1 pending: spec_index.json consumer (scripts audit TBD).

---

## 7. Readiness Assessment

See PRE_FRONTEND_READINESS_REPORT.md for full analysis.

**Verdict: CONDITIONAL GO**

Hard blockers:
1. BLOCK-001: Login response shape (APPLIED — doc corrected in this audit)
2. BLOCK-002: JWT sub claim (APPLIED — doc corrected)
3. BLOCK-003: notification-service ASGI shim (PENDING OWNER — OA-001)
4. BLOCK-004: session-service v2 prefix (PENDING OWNER — OA-009)

---

## 8. Remediation Log (Applied During This Audit)

### 8.1 Documentation Corrections Applied

The following doc-only corrections were applied immediately per audit mandate (no owner approval required):

| # | Document | What Changed |
|---|---|---|
| 1 | SERVICE_CATALOG.md | "65 services" → "69 services"; summary table corrected; notification-service added to Non-Standard table; auth/checkout ASGI notes updated |
| 2 | AUTH_AND_TENANCY_CONTRACT.md | RS256 validation table updated (all 33 services RS256+HS256); session storage updated (SQLiteAuthStore); login response shape corrected (user sub-object, sub claim, refresh_expires_in); JWT claims table extended; tenant field table corrected to 6 fields |
| 3 | DATA_SHAPE_REGISTRY.md | Tenant shape: 4 fields → 6 fields (country_code, segment_type, plan_type, addon_flags); login response shape corrected; event envelope shape corrected (timestamp, schema_version, topic, correlation_id, metadata); progress status field corrected (completion_status → status) |
| 4 | FULLSTACK_STITCHING_CONTRACT.md | Phase 2 Addendum cross-cutting facts: "All storage in-memory: Yes" → "16 services SQLite"; "All events InMemoryEventPublisher" → "in-process EventBus singleton" |
| 5 | SECURITY_DISCOVERY_REPORT.md | RS256-only table updated; security debt paragraph updated |
| 6 | DATABASE_SCHEMA.md | "No persistent database" section replaced; store_db.py characterization corrected; open questions D-001/Q-DB-001/Q-DB-002 closed; spec-vs-impl table corrected (auth_refresh_tokens lineage); column-level drifts corrected |
| 7 | DATABASE_DISCOVERY_REPORT.md | Summary finding updated; evidence table updated; store_db.py section corrected |
| 8 | EVENT_AND_QUEUE_ARCHITECTURE.md | InMemoryEventPublisher → shared EventBus singleton; envelope fields corrected; consumer stubs noted |
| 9 | EVENT_DISCOVERY_REPORT.md | Same InMemoryEventPublisher correction |
| 10 | BACKEND_AUTHORITY_CAPTURE_REPORT.md | All 65→69 occurrences |
| 11 | BACKEND_ARCHITECTURE.md | 65→69 count |
| 12 | BACKEND_ARCHITECTURE_REPORT.md | 65→69 count |
| 13 | API_DISCOVERY_REPORT.md | "40 of 65" → "40 of 69" |
| 14 | REPOSITORY_TREE_INVENTORY.md | 70→69; docs/01_backend not empty; 03_ops→03_fullstack_contracts |
| 15 | auth-service-storage-contract.md | auth_tenants table added; refresh_expires_at column added |
| 16 | core-lms-schema.md | organization_id → institution_id in courses table |
| 17 | AI_OPERATING_CONTEXT.md | 72→69 service count clarification; note on Dockerfiles/CI existence in infrastructure/ |

### 8.2 New Reports Written

All 8 required outputs created in docs/08_reports/:
1. PRE_FRONTEND_DELTA_AUDIT.md — this document
2. DOC_TO_CODE_DELTA_MATRIX.md — 58-row delta matrix
3. UNVERIFIED_CLAIMS_REGISTER.md — 15 UCR entries
4. UNDOCUMENTED_CODE_REGISTER.md — 16 UDC entries
5. DOC_DRIFT_REGISTER.md — 17 DDR entries
6. TBD_RESOLUTION_REGISTER.md — 12 TBD entries (11 resolved)
7. PRE_FRONTEND_READINESS_REPORT.md — go/no-go assessment
8. OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md — 10 OA items

---

## 9. Documents NOT Modified (Requiring Owner Approval)

The following files were audited and found to have deltas but NOT modified because the fix requires a code or architecture decision:

- `backend/services/notification-service/app/main.py` — ASGI shim needed (OA-001)
- `backend/services/rbac-service/app/schemas.py` — branch_ids addition (OA-002)
- `backend/services/enrollment-service/app/store_db.py` — unique constraint (OA-003)
- `infrastructure/deployment/service-manifest.json` — service:ClassName entries (OA-004)
- `backend/services/session-service/app/main.py` — v2 prefix (OA-009, doc decision)
- `docs/qc/` — 11 scripts to validate/ (OA-010, path verification needed)
