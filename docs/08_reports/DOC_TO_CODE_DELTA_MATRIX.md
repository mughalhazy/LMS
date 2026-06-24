# DOC-TO-CODE DELTA MATRIX

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Sources: Five-domain parallel audit — Service/API, Auth/Contracts, Database, Repository Hygiene, Events/Infrastructure

Complete matrix of every delta found between documentation and code. One row per finding.

Legend — Resolution column:
- `DOC-FIX` — documentation correction only, no code change needed
- `OWNER` — requires owner decision (see OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md)
- `RESOLVED` — already corrected during this audit session
- `INFO` — informational, no action required
- `PENDING` — awaiting further evidence (single outstanding TBD)

---

| Delta ID | Type | Source Document | Finding | Severity | Resolution |
|---|---|---|---|---|---|
| **AUTH / JWT** | | | | | |
| D-AUTH-001 | UCR | AUTH_AND_TENANCY_CONTRACT.md:49–61 | RS256 consuming-service table shows HS256-only — Task 7 fixed all 33 | HIGH | DOC-FIX |
| D-AUTH-002 | UCR | AUTH_AND_TENANCY_CONTRACT.md:102 | "Sessions in InMemoryAuthStore" — now SQLiteAuthStore (Task 7) | HIGH | DOC-FIX |
| D-AUTH-003 | UCR | AUTH_AND_TENANCY_CONTRACT.md, DATA_SHAPE_REGISTRY.md | Login response: user_id/tenant_id documented at top level; code nests under `"user"` sub-object | CRITICAL | DOC-FIX |
| D-AUTH-004 | UCR | AUTH_AND_TENANCY_CONTRACT.md | JWT user identifier claim: docs imply `user_id`; code uses standard `sub` claim | CRITICAL | DOC-FIX |
| D-AUTH-005 | UCR | AUTH_AND_TENANCY_CONTRACT.md | Login response: `roles` documented in response; code does not include roles in response (only in JWT) | HIGH | DOC-FIX |
| D-AUTH-006 | UDC | AUTH_AND_TENANCY_CONTRACT.md | `refresh_expires_in: 604800` in response — not documented | MEDIUM | DOC-FIX |
| D-AUTH-007 | UDC | AUTH_AND_TENANCY_CONTRACT.md JWT claims table | `scope: "lms.api"` and `session_id` (duplicate of `sid`) undocumented claims | MEDIUM | DOC-FIX |
| D-AUTH-008 | UDC | AUTH_AND_TENANCY_CONTRACT.md JWT claims table | Refresh token claims `token_type: "refresh"`, `family_id`, explicit `jti` undocumented | MEDIUM | DOC-FIX |
| D-AUTH-009 | DRIFT | AUTH_AND_TENANCY_CONTRACT.md Open Issues | Risk IDs (RISK-006/007/008) don't match BACKEND_RISK_REGISTER.md actual IDs | MEDIUM | DOC-FIX |
| D-AUTH-010 | DRIFT | AUTH_AND_TENANCY_CONTRACT.md | Canonical tenant contract table shows `active`, `domain` as fields; anchor + code use `country_code`, `segment_type`, `plan_type`, `addon_flags` | HIGH | DOC-FIX |
| **DATA SHAPES** | | | | | |
| D-SHAPE-001 | UCR | DATA_SHAPE_REGISTRY.md Tenant Shape | 4-field tenant shape (`tenant_id, name, active, domain`) contradicts 6-field anchor + code | HIGH | DOC-FIX |
| D-SHAPE-002 | UCR | DATA_SHAPE_REGISTRY.md Session Shape | Login response shape wrong (see D-AUTH-003/005/006) | CRITICAL | DOC-FIX |
| D-SHAPE-003 | UCR | DATA_SHAPE_REGISTRY.md Event Envelope | `occurred_at` → `timestamp`; `version` → `schema_version`; missing `topic`, `correlation_id`, `metadata` | HIGH | DOC-FIX |
| D-SHAPE-004 | DRIFT | DATA_SHAPE_REGISTRY.md Progress Shape | `completion_status` documented; code uses `status` | MEDIUM | DOC-FIX |
| D-SHAPE-005 | UDC | DATA_SHAPE_REGISTRY.md | No user-service data shapes documented (17+ endpoints, 7+ schemas) | CRITICAL | OWNER |
| D-SHAPE-006 | UDC | DATA_SHAPE_REGISTRY.md | No course-service data shapes documented (12+ endpoints, 7+ schemas) | CRITICAL | OWNER |
| D-SHAPE-007 | UDC | DATA_SHAPE_REGISTRY.md | course-service CreateCourseRequest embeds tenant context fields in body — undocumented pattern | HIGH | OWNER |
| **SERVICE CATALOG** | | | | | |
| D-SVC-001 | UCR | SERVICE_CATALOG.md:15 | "65 services" — confirmed 69 in manifest | HIGH | DOC-FIX |
| D-SVC-002 | UCR | SERVICE_CATALOG.md | Summary table (61+1+2+3 = 67; claimed 65) — internal math also wrong; actual is 63+1+2+3 = 69 | HIGH | DOC-FIX |
| D-SVC-003 | UCR | SERVICE_CATALOG.md Non-Standard table | notification-service (port 8122) is stdlib http.server with no ASGI shim — NOT in Non-Standard table | HIGH | DOC-FIX + OWNER (OA-001 for code fix) |
| D-SVC-004 | DRIFT | SERVICE_CATALOG.md Non-Standard table | auth-service and checkout-service notes say "no app object" — ASGI shims added in Task 7 | MEDIUM | DOC-FIX |
| D-SVC-005 | UCR | SERVICE_CATALOG.md | org-service described as "Organizational hierarchy only" — also owns /departments and /teams (14+ endpoints) | HIGH | DOC-FIX |
| D-SVC-006 | UDC | API_CONTRACT.md | API contract documents only 6 of 69 services (~9%) — 63 services have no endpoint documentation | CRITICAL | OWNER |
| D-SVC-007 | UDC | API_CONTRACT.md, SESSION_CONTRACT | session-service uses `/api/v2/sessions` prefix; all others use v1; undocumented exception | HIGH | OWNER (OA-009) |
| D-SVC-008 | UCR | API_CONTRACT.md | rbac-service health path implied as `/health`; actual is `/api/v1/rbac/health` due to router prefix | LOW | DOC-FIX |
| D-SVC-009 | UCR | SERVICE_CATALOG.md | service:ClassName entries — no runtime found that interprets this manifest format | HIGH | OWNER (OA-004) |
| D-SVC-010 | UDC | SERVICE_CATALOG.md | assessment-service owns both /assessments and /attempts routes; separate attempt-service also registered | HIGH | OWNER (OA-005) |
| **DATABASE / PERSISTENCE** | | | | | |
| D-DB-001 | UCR | DATABASE_SCHEMA.md:19 | "All backend services use in-memory storage exclusively" — 16 now use SQLite | CRITICAL | DOC-FIX |
| D-DB-002 | UCR | DATABASE_DISCOVERY_REPORT.md:21 | "No persistent database exists in any backend service" — 16 services now SQLite | CRITICAL | DOC-FIX |
| D-DB-003 | UCR | DATABASE_SCHEMA.md:56, DATABASE_DISCOVERY_REPORT.md | "store_db.py = stub implementations, never imported" — 16 are complete and wired | HIGH | DOC-FIX |
| D-DB-004 | TBD | DATABASE_SCHEMA.md Open Questions D-001 | "Does checkout-service have DB persistence?" → No (still InMemory) | MEDIUM | DOC-FIX (close TBD) |
| D-DB-005 | TBD | DATABASE_SCHEMA.md Q-DB-001 | "Are store_db.py files actively used?" → Yes, 16 services | HIGH | DOC-FIX (close TBD) |
| D-DB-006 | TBD | DATABASE_SCHEMA.md Q-DB-002 | "Is there an ORM or migration framework?" → No; custom BaseRepository on stdlib sqlite3 | MEDIUM | DOC-FIX (close TBD) |
| D-DB-007 | TBD | DATABASE_DISCOVERY_REPORT.md | "Is there external persistence (PostgreSQL, Redis)?" → No; common.env postgresql/redis are aspirational | MEDIUM | DOC-FIX (close TBD) |
| D-DB-008 | DRIFT | DATABASE_SCHEMA.md spec-vs-impl table | `refresh_token_family` listed as "not found" — implemented as `auth_refresh_tokens` with `parent_token_id`/`replaced_by_token_id` | MEDIUM | DOC-FIX |
| D-DB-009 | UDC | auth-service-storage-contract.md | `auth_tenants` table (tenant cache) exists in store_db.py but not in contract | LOW | DOC-FIX |
| D-DB-010 | DRIFT | auth-service-storage-contract.md | `auth_sessions` missing `refresh_expires_at` column | LOW | DOC-FIX |
| D-DB-011 | DRIFT | DATABASE_SCHEMA.md | Enrollment model: `version` field documented; not in SQLite `enrollments` table schema | MEDIUM | DOC-FIX |
| D-DB-012 | DRIFT | DATABASE_SCHEMA.md, progress-service | ProgressRecord `completion_status` in docs; code uses `status` | MEDIUM | DOC-FIX |
| D-DB-013 | DRIFT | core-lms-schema.md | Courses table: `organization_id` in docs; code uses `institution_id` | MEDIUM | DOC-FIX |
| D-DB-014 | UCR | DATABASE_SCHEMA.md, core-lms-schema.md | Enrollments unique constraint `(tenant_id, user_id, course_id)` documented; SQLite has INDEX not UNIQUE | MEDIUM | OWNER (OA-003) |
| D-DB-015 | UCR | DATABASE_DISCOVERY_REPORT.md evidence table | Only 6 services sampled; all shown as InMemory — 16 are SQLite as of Task 7 | HIGH | DOC-FIX |
| **EVENTS / QUEUE** | | | | | |
| D-EV-001 | UCR | EVENT_AND_QUEUE_ARCHITECTURE.md:22–24 | "Per-service InMemoryEventPublisher" — reality is shared EventBus singleton at `backend/services/shared/events/bus.py` | HIGH | DOC-FIX |
| D-EV-002 | DRIFT | EVENT_DISCOVERY_REPORT.md:38 | Same InMemoryEventPublisher misdescription | HIGH | DOC-FIX |
| D-EV-003 | UCR | EVENT_AND_QUEUE_ARCHITECTURE.md:58–64 | Envelope: `occurred_at`, `version`, 7 fields — code: `timestamp`, `schema_version`, 10 fields (adds `topic`, `correlation_id`, `metadata`) | HIGH | DOC-FIX |
| D-EV-004 | UDC | EVENT_AND_QUEUE_ARCHITECTURE.md | `build_event()` bridges 10-field internal envelope to 7-field external view — bridging logic undocumented | MEDIUM | DOC-FIX |
| D-EV-005 | UDC | EVENT_AND_QUEUE_ARCHITECTURE.md | All consumer handlers are logging stubs ("future: ...") — docs describe them as functional | HIGH | DOC-FIX |
| D-EV-006 | DRIFT | event_topics.json | Canonical names (`lms.<domain>.<event>.v1`) not used consistently in code — auth-service uses `"user.status_changed"`, attempt-service uses `"assessment.submission"` | HIGH | OWNER (OA-007 related) |
| D-EV-007 | UDC | event_topics.json | `lms.course.program_links_updated.v1` published by course-service — not in event_topics.json | LOW | DOC-FIX |
| D-EV-008 | UDC | event_topics.json | `payment.*`, `entitlement.activated` published by payment-service — not in event_topics.json | LOW | DOC-FIX |
| D-EV-009 | UDC | event_topics.json | enrollment-service dual-subscribes `"lms.enrollment.status_changed.v1"` AND `"enrollment.completed"` — resilience pattern, undocumented | MEDIUM | DOC-FIX |
| D-EV-010 | UCR | FULLSTACK_STITCHING_CONTRACT.md | "All events are in-memory — InMemoryEventPublisher: Yes" — wrong implementation name; it's EventBus | HIGH | DOC-FIX |
| **INFRASTRUCTURE** | | | | | |
| D-INF-001 | UCR | infrastructure/event-bus/event_bus_config.json | `"platform": "kafka"` with 3 bootstrap servers — no Kafka client in any Python service; aspirational only | MEDIUM | DOC-FIX (add comment to file) |
| D-INF-002 | UCR | infrastructure/deployment/env/common.env | DATABASE_URL=postgresql, REDIS_URL, EVENT_BUS_URL=amqp — none used in code; SQLite + in-process bus is actual | HIGH | DOC-FIX (add header to file) |
| D-INF-003 | UCR | AI_OPERATING_CONTEXT.md | "No Dockerfiles or CI/CD in repository" constraint — Dockerfile.python, Dockerfile.node, docker-compose.yml, deploy-backend.yml exist in infrastructure/ | MEDIUM | OWNER |
| D-INF-004 | UCR | Event docs, SERVICE_CATALOG.md | `analytics-ingestion-service` in manifest/docs; actual directory is `event-ingestion-service` — name mismatch | MEDIUM | OWNER |
| D-INF-005 | UCR | infrastructure/secrets-management/ | Secrets catalog env vars (DATABASE_URL, REDIS_URL) don't match actual code env vars (JWT_SHARED_SECRET, JWT_PUBLIC_KEY, LMS_DB_PATH) | MEDIUM | DOC-FIX |
| **REPOSITORY HYGIENE** | | | | | |
| D-REPO-001 | UCR | REPOSITORY_TREE_INVENTORY.md:126 | "70 named services" → 69 service directories | LOW | DOC-FIX |
| D-REPO-002 | UCR | REPOSITORY_TREE_INVENTORY.md | "docs/01_backend/ — EMPTY" → contains 8 Phase 2 authority documents | MEDIUM | DOC-FIX |
| D-REPO-003 | UCR | REPOSITORY_TREE_INVENTORY.md | "docs/03_ops/" → actual is `docs/03_fullstack_contracts/` | LOW | DOC-FIX |
| D-REPO-004 | UCR | BACKEND_ARCHITECTURE_REPORT.md:21 | "65 registered services" → 69 | MEDIUM | DOC-FIX |
| D-REPO-005 | UCR | API_DISCOVERY_REPORT.md:200 | "40 of 65 services" → "40 of 69 services" | MEDIUM | DOC-FIX |
| D-REPO-006 | UCR | BACKEND_AUTHORITY_CAPTURE_REPORT.md (×6) | "65 services" × 6 occurrences → 69 | MEDIUM | DOC-FIX |
| D-REPO-007 | UCR | SECURITY_DISCOVERY_REPORT.md:27–33 | rbac-service, tenant-service etc. listed as HS256-only — Task 7 fixed all | HIGH | DOC-FIX |
| D-REPO-008 | UCR | FULLSTACK_STITCHING_CONTRACT.md | "All storage is in-memory: Yes" → 16 services use SQLite | HIGH | DOC-FIX |
| D-REPO-009 | UDC | docs/api/ legacy files | No supersession notice pointing to docs/01_backend/API_CONTRACT.md | MEDIUM | DOC-FIX |
| D-REPO-010 | UDC | docs/ | `scripts/fix_repo_anchor_paths.py` exists but is undocumented in any inventory or maintenance plan | LOW | DOC-FIX |
| D-REPO-011 | UCR | BACKEND_ARCHITECTURE.md | "65 services" → 69 | MEDIUM | DOC-FIX |
| D-REPO-012 | UDC | BACKEND_ARCHITECTURE.md | Cross-layer import topology (root shared/, integrations/, services/ used by backend/services/) undocumented | MEDIUM | DOC-FIX |
| D-REPO-013 | UDC | BACKEND_ARCHITECTURE.md | shared/security.py canonical module (Task 7) not documented | MEDIUM | DOC-FIX |
| D-REPO-014 | OWNER | docs/qc/ | 11 Python scripts in docs/qc/ — should be in validation/ per restructuring plan | LOW | OWNER (OA-010) |
| D-REPO-015 | OWNER | integrations/ | integrations/payment/ (8 files, singular) vs integrations/payments/ (26 files, plural) — ownership overlap | LOW | OWNER (OA-008) |
| D-REPO-016 | UCR | AI_OPERATING_CONTEXT.md | Service count says "72 named service directories" — actual is 69 registered, 72 total dirs including shared/+pycache | LOW | DOC-FIX |
| **TBD RESOLUTION** | | | | | |
| D-TBD-010 | TBD | REPOSITORY_RESTRUCTURING_PLAN.md P1-SEC-002 | "Verify infrastructure/*.env content" — common.env verified as placeholder-only, safe to leave | LOW | DOC-FIX (close P1-SEC-002) |
| D-TBD-012 | TBD | REPOSITORY_RESTRUCTURING_PLAN.md P3-GITIGNORE-001 | spec_index.json consumer — awaiting scripts audit | LOW | PENDING |

---

## Summary Counts

| Resolution | Count |
|---|---|
| DOC-FIX (safe, immediate) | 44 |
| OWNER (requires approval) | 13 |
| PENDING (1 outstanding TBD) | 1 |
| **Total deltas** | **58** |

| Severity | Count |
|---|---|
| CRITICAL | 7 |
| HIGH | 23 |
| MEDIUM | 20 |
| LOW | 8 |

Detailed entries: UNVERIFIED_CLAIMS_REGISTER.md (UCR), DOC_DRIFT_REGISTER.md (DRIFT), UNDOCUMENTED_CODE_REGISTER.md (UDC), TBD_RESOLUTION_REGISTER.md (TBD).
Owner approval items: OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md.
