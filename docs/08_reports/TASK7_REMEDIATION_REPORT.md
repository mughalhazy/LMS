# TASK 7 REMEDIATION REPORT

Status: Complete
Date: 2026-06-23
Owner: AI
Phase: Task 7 — Post-Phase 2 Owner Action Resolution

---

## Purpose

This report documents all code changes and findings from Task 7, which addressed the owner action items reported at the end of Phase 2 Backend Authority Capture.

---

## Owner Actions Addressed

| Action | Severity | Resolution |
|---|---|---|
| D-001: Persistence backend decision | CRITICAL | SQLite activated for 16 services |
| D-002: Identify `service:ClassName` runtime | HIGH | Investigated — root layer legacy classes, no runtime found |
| Verify auth-service startup mechanism | HIGH | ASGI shim added to main.py |
| Verify checkout-service startup mechanism | HIGH | ASGI shim added to main.py |
| Authorize R-012: RS256 migration | HIGH | RS256 validation added to all 32 consuming services |
| Message queue platform decision | CRITICAL | In-process EventBus already wired; cross-process still open |
| Confirm service count discrepancy (65 vs 72) | MEDIUM | Resolved: manifest has 69 services; Phase 2 miscount corrected |

---

## 1. Service Count Discrepancy — RESOLVED

**Finding:** Phase 2 reported 65 services in the manifest; AI_OPERATING_CONTEXT.md said 72.

**Resolution:**
- PowerShell `$data.services.Count` on `infrastructure/deployment/service-manifest.json` = **69**
- `backend/services/` directory has **72 total entries** = 69 service directories + `shared/` + `__init__.py` + `__pycache__`
- The Phase 2 count of "65" was a miscount
- AI_OPERATING_CONTEXT.md's "72" was counting all `ls` entries, not just service directories

**Correct answer:** 69 services in the manifest. 69 service directories in `backend/services/`. No real discrepancy.

---

## 2. Persistence Backend (D-001) — PARTIALLY RESOLVED

### Finding

Phase 2 incorrectly reported `store_db.py` as "stubs." Inspection revealed they are **complete SQLite implementations** using `BaseRepository` from `backend/services/shared/db/engine.py`.

`shared/db/engine.py` provides:
- `BaseRepository` mixin: `_connect()`, `_init_schema()`, `_require_tenant_id()`, `_fetch_one()`, `_fetch_all()`, `_execute_tenant()`, `_row()`, `_rows()`
- `resolve_db_path(service_name)` — env-based per-service DB file path
- WAL mode, foreign keys ON, busy timeout 5000ms
- ARCH_04 (per-service isolation) and ARCH_07 (tenant-first queries)

### Services Wired to SQLite

All 16 services with complete `store_db.py` implementations were switched from `InMemoryXStore` to `SQLiteXStore` in their `main.py`:

| Service | Old Store | New Store |
|---|---|---|
| auth-service | `InMemoryAuthStore` | `SQLiteAuthStore` |
| rbac-service | `InMemoryRBACStore` | `SQLiteRBACStore` |
| enrollment-service | `InMemoryEnrollmentStore` | `SQLiteEnrollmentStore` |
| progress-service | `InMemoryProgressStore`, `InMemoryIdempotencyStore` | `SQLiteProgressStore`, `SQLiteIdempotencyStore` |
| tenant-service | `InMemoryTenantStore` | `SQLiteTenantStore` |
| assessment-service | `InMemoryAssessmentStore` | `SQLiteAssessmentStore` |
| certificate-service | `InMemoryCertificateStore` | `SQLiteCertificateStore` |
| lesson-service | `InMemoryLessonStore` | `SQLiteLessonStore` |
| program-service | `InMemoryProgramStore` | `SQLiteProgramStore` |
| badge-service | `InMemoryBadgeRepository` | `SQLiteBadgeRepository` |
| session-service | `InMemorySessionRepository` | `SQLiteSessionRepository` |
| user-service | _(implicit in UserService)_ | `SQLiteUserStore`, `SQLiteAuditLogStore` |
| org-service | `InMemoryOrgRepository` | `SQLiteOrgRepository` |
| cohort-service | _(default CohortService)_ | `SQLiteCohortStore` |
| institution-service | `InstitutionRepository` | `SQLiteInstitutionRepository` |
| course-service | _(default CourseService)_ | `SQLiteCourseStorage` |

### Remaining

53 services still use `InMemoryXStore`. These services have no `store_db.py` — new SQLite store implementations are required. This remains an open owner action.

---

## 3. Message Queue (D-001 / Event Bus) — CONFIRMED WIRED

### Finding

Phase 2 reported "no real message queue." `backend/services/shared/events/bus.py` was missed.

**Already implemented:**
- `EventBus` — thread-safe in-process pub/sub, `subscribe()`, `publish()`, wildcard `"*"` support
- `get_default_bus()` — module-level singleton
- `EventEnvelope` — `build_event()` + `publish_event()` factory in `envelope.py`
- auth-service `consumers.py` already imports and uses `get_default_bus()` (9 subscriptions)
- auth-service `service.py` already calls `publish_event()` from `shared.events.envelope`

**Gap that remains:** In-process delivery only. Cross-service event routing (e.g., `enrollment.created` reaching `progress-service` in a different process) requires an external message broker. This is an owner decision on platform (Redis Streams, RabbitMQ, etc.) — no code can resolve it without that decision.

---

## 4. D-002: `service:ClassName` Runtime — INVESTIGATED

**Finding:** Three services in the manifest use `service:ClassName` format: capability-registry, config-service, entitlement-service.

**Discovered:**
- Root `services/capability-registry/service.py` has `CapabilityRegistryService` — a pure Python class with no HTTP server, no `run()`, no `main.py`
- `backend/services/capability-registry/app/main.py` has a newer stdlib http.server implementation on port 8093, using a different `CapabilityRegistryService` from `.service` — this is NOT in the manifest
- The `service:ClassName` manifest format does not match any standard Python ASGI/WSGI spec (`app:object` for uvicorn, `module:callable` for gunicorn)
- No custom loader/runner script found in `infrastructure/` that interprets this format

**Conclusion:** The 3 root-layer `service:ClassName` entries likely cannot be deployed as HTTP services without a custom runner. The newer HTTP versions in `backend/services/` are unregistered. Owner decision required: either locate/document the custom loader, or update the manifest to point to the backend/ HTTP versions.

---

## 5. RS256/HS256 Migration (R-012) — RESOLVED

### Problem

auth-service issues RS256 JWT tokens when the `cryptography` package is available. All consuming services validated HS256 only (`_validate_hs256_jwt`) — they would reject RS256 tokens with 401.

### Solution

Three artefacts created/updated:

**`backend/services/shared/security.py`** — canonical RS256+HS256 security module:
- `_validate_hs256_jwt()` — existing HMAC-SHA256 path
- `_validate_rs256_jwt()` — new RSA PKCS1v15 SHA256 path using `cryptography` package
- `_peek_jwt_alg()` — reads `alg` claim from JWT header without validating
- `validate_jwt()` — routes to RS256 or HS256 based on `alg` claim
- `require_jwt()` — FastAPI dependency, algorithm-aware
- `require_tenant_scope()`, `apply_security_headers()` — unchanged

**32 service `security.py` files updated** to add `_validate_rs256_jwt()` and RS256 routing in `require_jwt()`:
- Standard-style (multiline `def require_jwt(`): 28 services patched via batch script
- Compact-style (`_decode_b64url` helper, single-line signature): 4 services patched via batch script
- Cohort-service: replaced no-op placeholder with full RS256+HS256 implementation

**Not modified (correct as-is):**
- `auth-service/app/security.py` — JWT issuer, not consumer; already handles both RS256 and HS256
- `api-key-service/app/security.py` — different security model (API key hashing)
- `media-service/*/security.py` — custom playback token validation, different model

### How it works

```python
# In require_jwt(), for any incoming Bearer token:
alg = json.loads(_decode_base64url(token.split(".")[0]).decode()).get("alg", "HS256")
if alg == "RS256":
    # Reads JWT_PUBLIC_KEY env var (PEM-encoded RSA public key)
    request.state.jwt_payload = _validate_rs256_jwt(token, public_key_pem)
else:
    # Reads JWT_SHARED_SECRET env var
    request.state.jwt_payload = _validate_hs256_jwt(token, secret)
```

Both `JWT_PUBLIC_KEY` and `JWT_SHARED_SECRET` can be set simultaneously, allowing HS256 and RS256 tokens to coexist during rollout.

### Deployment action required

`JWT_PUBLIC_KEY` (PEM-encoded RSA public key) must be set in each consuming service's environment. The key must match the `JWT_PRIVATE_KEY` used by auth-service. Without it, RS256 tokens return `503 jwt_public_key_not_configured`.

---

## 6. auth-service Startup Mechanism — RESOLVED

**Problem:** Manifest registers `app.main:app` but `auth-service/app/main.py` had no `app` object — uvicorn startup would fail with `AttributeError`.

**Resolution:** FastAPI ASGI shim added at the bottom of `backend/services/auth-service/app/main.py`:
- `app = FastAPI(title="Auth Service", version="2.0.0", ...)`
- Routes: `/api/v2/auth/{path}`, `/.well-known/jwks.json`, `/health`, `/metrics`
- Shim delegates to existing `SERVICE` instance via full_path + method routing
- The original `run()` / `HTTPServer` code is preserved for direct execution

---

## 7. checkout-service Startup Mechanism — RESOLVED

Same pattern as auth-service.

**Resolution:** FastAPI ASGI shim added at the bottom of `backend/services/checkout-service/app/main.py`:
- `app = FastAPI(title="Checkout Service", version="1.0.0", ...)`
- Routes: `/api/v1/checkout/{path}`, `/health`
- Shim delegates to existing `SERVICE` (CheckoutService) instance

---

## Files Modified

### main.py store wire-ups (16 files)
```
backend/services/auth-service/app/main.py
backend/services/rbac-service/app/main.py
backend/services/enrollment-service/app/main.py
backend/services/progress-service/app/main.py
backend/services/tenant-service/app/main.py
backend/services/assessment-service/app/main.py
backend/services/certificate-service/app/main.py
backend/services/lesson-service/app/main.py
backend/services/program-service/app/main.py
backend/services/badge-service/app/main.py
backend/services/session-service/app/main.py
backend/services/user-service/app/main.py
backend/services/org-service/app/main.py
backend/services/cohort-service/app/main.py
backend/services/institution-service/app/main.py
backend/services/course-service/app/main.py
```

### main.py ASGI shim additions (2 files)
```
backend/services/auth-service/app/main.py     (also has store wire-up above)
backend/services/checkout-service/app/main.py
```

### security.py RS256 additions (32 files)
```
backend/services/rbac-service/app/security.py          (updated manually, session start)
backend/services/ai-tutor-service/app/security.py
backend/services/attempt-service/app/security.py
backend/services/badge-service/app/security.py
backend/services/certificate-service/app/security.py
backend/services/content-service/app/security.py
backend/services/course-generation-service/app/security.py
backend/services/course-service/app/security.py
backend/services/department-service/app/security.py
backend/services/email-service/app/security.py
backend/services/enrollment-service/app/security.py
backend/services/group-service/app/security.py
backend/services/hris-sync-service/app/security.py
backend/services/institution-service/app/security.py
backend/services/learning-analytics-service/app/security.py
backend/services/learning-path-service/app/security.py
backend/services/lesson-service/app/security.py
backend/services/lti-service/app/security.py
backend/services/org-service/app/security.py
backend/services/progress-service/app/security.py
backend/services/quiz-engine/app/security.py
backend/services/recommendation-service/app/security.py
backend/services/reporting-service/app/security.py
backend/services/session-service/app/security.py
backend/services/sso-service/app/security.py
backend/services/tenant-service/app/security.py
backend/services/user-service/app/security.py
backend/services/webhook-service/app/security.py
backend/services/prerequisite-engine-service/app/security.py
backend/services/review-service/app/security.py
backend/services/skill-analytics-service/app/security.py
backend/services/skill-inference-service/app/security.py
backend/services/cohort-service/app/security.py          (full replacement of no-op)
```

### New files created (2 files)
```
backend/services/shared/security.py     — canonical RS256+HS256 shared security module
patch_rs256.py                          — batch patcher script (can be deleted)
```

### Documents updated (2 files)
```
docs/08_reports/BACKEND_GAP_REGISTER.md
docs/08_reports/BACKEND_RISK_REGISTER.md
```

---

## Open Owner Actions After Task 7

| Item | Type | Priority |
|---|---|---|
| Set `JWT_PUBLIC_KEY` env var in all service environments | Deployment config | HIGH — RS256 tokens return 503 without it |
| Persistence for remaining 53 services | Architecture decision | CRITICAL — still in-memory |
| checkout-service SQLite idempotency store | Code — medium effort | HIGH — payment duplicate risk |
| Cross-process message broker decision | Architecture decision | CRITICAL — event-driven workflows blocked |
| D-002: Locate `service:ClassName` runtime or replace with backend/ equivalents | Investigation / manifest update | HIGH — 3 services undeployable |
| checkout-service: implement SQLiteCheckoutStore | Code | CRITICAL — payment data lost on restart |
| 53 remaining services: implement store_db.py | Code — high effort | CRITICAL — data loss on restart |

---

## Register Updates

- `BACKEND_GAP_REGISTER.md` — GAP-001, GAP-004, GAP-005, GAP-007, GAP-008 marked RESOLVED; GAP-002, GAP-003 marked PARTIALLY RESOLVED; GAP-006 marked INVESTIGATED; summary table updated
- `BACKEND_RISK_REGISTER.md` — RISK-003, RISK-004, RISK-011, RISK-012 marked RESOLVED/MITIGATED; RISK-001, RISK-007 marked PARTIALLY MITIGATED; summary table updated
