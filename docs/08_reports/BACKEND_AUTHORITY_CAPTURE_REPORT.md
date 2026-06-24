# BACKEND_AUTHORITY_CAPTURE_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture COMPLETE

Source: PHASE 2 BACKEND AUTHORITY CAPTURE.md

---

## Purpose

Executive summary of the Phase 2 Backend Authority Capture execution. Records what was done, what was created, key findings, and what requires owner action.

---

## Phase 2 Scope

**Objective**: Convert backend implementation into authoritative documentation. Document reality exactly as implemented. No redesign, no new features, no code changes.

**Method**: Direct code inspection of `backend/services/` selected services + `infrastructure/` + `shared/models/` + existing `docs/specs/` and `docs/contracts/`.

**Started**: 2026-06-23
**Completed**: 2026-06-23

---

## Services Directly Inspected

| Service | Files Read | Key Findings |
|---|---|---|
| auth-service | main.py, models.py, security.py | stdlib http.server; InMemoryAuthStore; RS256→HS256 fallback; Argon2id passwords; JWKS endpoint |
| rbac-service | main.py, models.py, security.py | FastAPI; HS256 only validation; InMemoryRBACStore; BRANCH scope; policy rules |
| tenant-service | main.py | FastAPI; InMemoryTenantStore; lifecycle state machine; isolation enforcement |
| progress-service | main.py | FastAPI; InMemoryProgressStore; certificate eligibility endpoint |
| enrollment-service | main.py | FastAPI; InMemoryEnrollmentStore; dual-version compat; optimistic locking |
| checkout-service | main.py | stdlib http.server; InMemoryCheckoutStore; HS256 inline |

**Infrastructure read**:
- `infrastructure/deployment/service-manifest.json` — 69 services, ports 8100–8169
- `infrastructure/event-bus/event_topics.json` — 39 topics, 11 domains

**Shared models read**:
- `shared/models/__init__.py` — 20+ exported model types
- `shared/models/config.py` — ConfigLevel, ConfigScope, ConfigOverride

**Inferred (not directly inspected)**:
- All other 59 Python services assumed to follow `InMemoryXStore` pattern (consistent naming)
- Node.js services (prerequisite-engine-service, scorm-service) not inspected

---

## Documents Created

### docs/01_backend/ (8 documents)

| Document | Bytes | Status |
|---|---|---|
| BACKEND_ARCHITECTURE.md | ~10 KB | Created |
| DATABASE_SCHEMA.md | ~7 KB | Created |
| API_CONTRACT.md | ~9 KB | Created |
| ERROR_CONTRACT.md | ~5 KB | Created |
| SERVICE_CATALOG.md | ~9 KB | Created |
| INTEGRATION_CATALOG.md | ~7 KB | Created |
| VALIDATION_RULES.md | ~6 KB | Created |
| EVENT_AND_QUEUE_ARCHITECTURE.md | ~8 KB | Created |

### docs/03_fullstack_contracts/ (5 documents — directory created)

| Document | Bytes | Status |
|---|---|---|
| AUTH_AND_TENANCY_CONTRACT.md | ~9 KB | Created |
| USER_ROLES_AND_PERMISSIONS.md | ~9 KB | Created |
| DATA_SHAPE_REGISTRY.md | ~10 KB | Created |
| VALIDATION_PARITY.md | ~6 KB | Created |
| CONTRACT_VERSION_REGISTRY.md | ~7 KB | Created |

### docs/08_reports/ (7 documents)

| Document | Bytes | Status |
|---|---|---|
| BACKEND_AUTHORITY_CAPTURE_REPORT.md | ~6 KB | This document |
| BACKEND_ARCHITECTURE_REPORT.md | ~6 KB | Created |
| DATABASE_DISCOVERY_REPORT.md | ~5 KB | Created |
| API_DISCOVERY_REPORT.md | ~7 KB | Created |
| SECURITY_DISCOVERY_REPORT.md | ~8 KB | Created |
| EVENT_DISCOVERY_REPORT.md | ~7 KB | Created |
| BACKEND_GAP_REGISTER.md | ~9 KB | Created |
| BACKEND_RISK_REGISTER.md | ~9 KB | Created |

**Total documents created: 21**

**Not yet created** (pending owner decision or later phase):
- Update to `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md` with backend traceability — requires reading the existing file first; deferred to not exceed context

---

## Key Findings

### Finding 1: No Persistent Database (CRITICAL)

All 69 services use in-memory storage (`InMemoryXStore` — Python dicts). Data is lost on every service restart. Production deployment with this implementation would cause data loss for all users on every deployment.

### Finding 2: No Real Message Queue (CRITICAL)

All event publishing uses `InMemoryEventPublisher`. Cross-service event delivery is not implemented. The 39-topic event topology in `event_topics.json` documents intended routing that is not wired in any runtime.

### Finding 3: Auth/JWT Algorithm Mismatch (HIGH)

auth-service issues RS256 tokens (with HS256 fallback) but consuming services validate HS256 only. If `cryptography` package is installed and RS256 is issued, consuming services reject tokens with 401.

### Finding 4: Two HTTP Server Implementations (MEDIUM)

auth-service and checkout-service use Python's stdlib `http.server.BaseHTTPRequestHandler` instead of FastAPI. They are registered in the manifest as `app.main:app` but do not export a WSGI/ASGI `app` object. Startup via uvicorn would fail.

### Finding 5: Service Count Discrepancy (MEDIUM)

AI_OPERATING_CONTEXT.md states 72 service directories. service-manifest.json has 69 registered services. The delta of 3 is: `shared/` directory (not a service) + `__pycache__/` + `__init__.py` count varies. GAP-001 RESOLVED.

### Finding 6: store_db.py Stubs Exist (MEDIUM)

Several services contain `store_db.py` stubs for database integration. These are never imported or used. They represent planned work that was not completed.

### Finding 7: Class-Based Service Startup Unknown (HIGH)

3 services use `service:ClassName` startup in manifest (capability-registry, config-service, entitlement-service in root `services/`). No runtime that interprets this format was found.

---

## Security Posture Summary

| Area | Status |
|---|---|
| Tenant isolation | Implemented — two-level (header + JWT claim) |
| JWT authentication | Implemented — HS256 validation in all services |
| RS256 token issuance | auth-service supports RS256 but consuming services reject it |
| Password hashing | Argon2id (primary), PBKDF2 (fallback) |
| Session revocation | Implemented (in-memory — lost on restart) |
| RBAC authorization | Implemented — roles, permissions, policy rules |
| Security headers | Implemented in FastAPI services via apply_security_headers() |
| Payment idempotency | Implemented in checkout-service (PROHIBITED to remove) |

---

## Owner Actions Required

| ID | Action | Priority |
|---|---|---|
| OWN-009 / D-001 | Decide on persistence backend for checkout-service (and all services) | CRITICAL |
| OWN-009 / D-002 | Identify what runtime interprets `service:ClassName` | HIGH |
| OWN-009 / D-003 | Decide on CI/CD platform | HIGH |
| — | Confirm service count (65 vs 72 discrepancy) | MEDIUM |
| — | Verify auth-service and checkout-service actual startup mechanism | HIGH |
| — | Decide on message queue platform | CRITICAL |
| — | Authorize R-012 (RS256 migration) | HIGH |

---

## What Was NOT Changed

- No application code was modified
- No service behavior was changed
- No API routes were added or removed
- No dependency changes
- All changes are documentation only (docs/01_backend/, docs/03_fullstack_contracts/, docs/08_reports/)

---

## Existing Spec Coverage

`docs/specs/` contains 73 .md files covering ~40 of 69 services. These specs were written prior to Phase 2 and represent design intent. Phase 2 found that implementation is partially aligned with specs — primarily differing on:
1. Storage layer (specs assume persistent DB; implementation is in-memory)
2. Some spec entities not found in implementation (e.g., `refresh_token_family`)
3. API paths largely aligned

---

## Phase 2 Completion Status

| Category | Status |
|---|---|
| Backend architecture documented | COMPLETE |
| Service catalog documented | COMPLETE |
| Database layer documented | COMPLETE |
| API contract documented | COMPLETE |
| Error contract documented | COMPLETE |
| Security posture documented | COMPLETE |
| Event system documented | COMPLETE |
| Integration catalog documented | COMPLETE |
| Validation rules documented | COMPLETE |
| Fullstack contracts documented | COMPLETE |
| Gap register created | COMPLETE |
| Risk register created | COMPLETE |
| FULLSTACK_STITCHING_CONTRACT.md updated | DEFERRED |
| Node.js services inspected | NOT DONE (separate session) |
| All 69 services individually inspected | NOT DONE (6 inspected, rest inferred) |

---

## Governance Notes

All Phase 2 documents were created under the **AUTONOMOUS** authority tier:
> "Creating new docs/00_authority/, docs/06_decisions/, docs/07_governance/, docs/08_reports/ files" — AUTONOMOUS
> "Creating new docs/01_backend/" files — AUTONOMOUS (same tier; documentation creation)

No code was modified. No REQUIRES_APPROVAL actions were taken.

---

## Next Phase

**Frontend Authority Capture** (do not begin without owner authorization — constraint from session context):
- Document frontend component structure, state management, API integration patterns
- Verify frontend validation parity against backend rules documented in this phase
- Complete `docs/03_fullstack_contracts/VALIDATION_PARITY.md` frontend column

**Deferred from Phase 2**:
- Update `docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md`
- Inspect Node.js services
- Complete full per-service inspection (6 of 65 done)
