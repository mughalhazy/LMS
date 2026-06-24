# PRE-FRONTEND READINESS REPORT

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Owner: Human
Verdict: **CONDITIONAL GO** — 4 critical blockers require resolution before Frontend Authority Capture begins

---

## Assessment

All 5 audit domains completed. 58 deltas found. 44 are documentation corrections that can be applied immediately. 13 require owner decisions. 1 is pending evidence (scripts audit TBD).

The backend is structurally ready for frontend work with caveats. The critical login/JWT findings (D-AUTH-003, D-AUTH-004) would cause frontend authentication to break silently. These must be corrected in documentation before the frontend team begins API integration.

---

## Hard Blockers — Must Resolve Before Frontend Authority Capture Starts

### BLOCK-001: Login Response Shape Is Wrong (CRITICAL)

**Finding**: AUTH_AND_TENANCY_CONTRACT.md and DATA_SHAPE_REGISTRY.md both document the login response with `user_id` and `tenant_id` at the top level. Code reality (auth-service/app/service.py:144–152) nests them inside a `"user"` sub-object. `roles` is absent from the response (only in JWT). `refresh_expires_in: 604800` exists in the response but is undocumented.

**Impact**: Frontend code reading `response.user_id` or `response.tenant_id` will get `undefined`. Authentication flow silently broken.

**Resolution**: DOC-FIX — update login response shape in AUTH_AND_TENANCY_CONTRACT.md and DATA_SHAPE_REGISTRY.md before Frontend Authority Capture begins. (Applied during this audit — see remediation log.)

---

### BLOCK-002: JWT User Identifier Claim Is `sub`, Not `user_id` (CRITICAL)

**Finding**: Documents imply `user_id` is the JWT claim for the user's identity. Code (auth-service/app/service.py:111) sets `"sub": user.user_id`. Frontend code accessing `payload.user_id` will get `undefined`.

**Impact**: Any feature using the logged-in user's ID (profile, permissions, progress) is broken.

**Resolution**: DOC-FIX — add explicit statement: "JWT user identifier is in the standard `sub` claim." (Applied during this audit.)

---

### BLOCK-003: notification-service Cannot Start (HIGH)

**Finding**: notification-service is registered in the manifest with `app.main:app` but uses `BaseHTTPRequestHandler` with no FastAPI `app` object. Uvicorn startup will raise `AttributeError`. No ASGI shim has been added (unlike auth-service and checkout-service in Task 7).

**Impact**: Email/notification delivery is unavailable. Any frontend feature that triggers notifications (enrollment confirmation, password reset email fallback, etc.) silently fails.

**Resolution**: OWNER (OA-001) — add ASGI shim to notification-service (same pattern as Task 7). Low complexity.

---

### BLOCK-004: session-service v2 API Prefix Undocumented (HIGH)

**Finding**: session-service uses `/api/v2/sessions` as its base path. All other services use `/api/v1/`. This is not documented in API_CONTRACT.md, the versioning strategy, or any contract document.

**Impact**: Frontend code using `/api/v1/sessions/` will receive 404 for all session operations.

**Resolution**: OWNER (OA-009) — document the v2 prefix as intentional in API_CONTRACT.md. Low complexity; does not require code change.

---

## Soft Blockers — Should Resolve Before Full FA Sprint Starts

### SOFT-001: 3 Manifest Services Undeployable (OA-004)

capability-registry, config-service, entitlement-service use `service:ClassName` manifest format with no discoverable runtime. If any feature depends on these services, it cannot be tested. Recommendation: resolve before FA if any planned frontend features depend on capability or configuration service APIs.

### SOFT-002: assessment/attempt Route Ownership Unclear (OA-005)

Frontend cannot confidently route attempt-related API calls without knowing which service owns `/api/v1/attempts/`. Resolve before designing the assessment/quiz frontend surface.

### SOFT-003: API Contract Covers Only 6/69 Services (UDC-001)

The remaining 63 services have no documented API contract. Frontend Authority Capture should systematically document all services needed for Phase 3 frontend features. This is expected scope for FA, not a blocker to starting FA.

---

## Non-Blockers (Documentation-Only Corrections)

All items in DOC_TO_CODE_DELTA_MATRIX.md with resolution type `DOC-FIX` are safe corrections that do not block FA. They should be applied before or during FA to ensure frontend engineers read accurate contracts.

High-priority doc fixes applied during this audit:
- AUTH_AND_TENANCY_CONTRACT.md: RS256 table, session storage, login response, JWT sub claim
- DATA_SHAPE_REGISTRY.md: tenant shape, login response, event envelope
- DATABASE_SCHEMA.md, DATABASE_DISCOVERY_REPORT.md: persistence state corrections
- SERVICE_CATALOG.md: service count 65→69
- FULLSTACK_STITCHING_CONTRACT.md: cross-cutting facts
- SECURITY_DISCOVERY_REPORT.md: RS256 stale claims
- BACKEND_AUTHORITY_CAPTURE_REPORT.md: service count across all occurrences

See PRE_FRONTEND_DELTA_AUDIT.md §8 for the complete remediation log.

---

## State of Each Phase-3 Prerequisite

| Prerequisite | Status | Notes |
|---|---|---|
| Auth API contract is accurate | PARTIAL | Login response shape now corrected; 4 undocumented JWT claims documented |
| Tenant isolation contract is accurate | PASS | AUTH_AND_TENANCY_CONTRACT.md tenant isolation section verified |
| JWT validation working across services | PASS | Task 7 — 33 services updated for RS256+HS256 |
| auth-service starts with uvicorn | PASS | ASGI shim added in Task 7 |
| checkout-service starts with uvicorn | PASS | ASGI shim added in Task 7 |
| notification-service starts with uvicorn | FAIL | BLOCK-003: no ASGI shim |
| Session persistence survives restart | PASS | auth-service now SQLiteAuthStore |
| Service catalog is accurate | PASS | Count corrected 65→69 |
| Service catalog covers all non-standard services | PARTIAL | notification-service not listed as non-standard |
| API contract exists for frontend-facing services | PARTIAL | 6/69 services; sufficient for auth/enrollment/progress/rbac. Gaps documented |
| Data shapes are accurate | PASS (after fixes) | Tenant, event envelope, login response corrected |
| Database schema is accurate | PASS (after fixes) | 16 SQLite services now documented |
| Event architecture is accurate | PASS (after fixes) | EventBus singleton documented; InMemoryEventPublisher corrected |
| All registers up to date | PASS | All 8 reports written/updated |

---

## Go/No-Go Summary

| Condition | Status |
|---|---|
| BLOCK-001 (login response shape) | APPLIED — doc corrected |
| BLOCK-002 (JWT sub claim) | APPLIED — doc corrected |
| BLOCK-003 (notification-service ASGI) | PENDING OWNER — OA-001 |
| BLOCK-004 (session-service v2 prefix) | PENDING OWNER — OA-009 |

**Verdict: CONDITIONAL GO**

Frontend Authority Capture can begin once BLOCK-001 and BLOCK-002 doc corrections are accepted by owner and BLOCK-003 and BLOCK-004 are resolved (OA-001 code fix + OA-009 doc decision). Remaining soft blockers and doc-only corrections should be addressed during FA sprint but do not gate its start.

---

## Deliverables Produced by This Audit

| Document | Location | Status |
|---|---|---|
| PRE_FRONTEND_DELTA_AUDIT.md | docs/08_reports/ | Complete |
| DOC_TO_CODE_DELTA_MATRIX.md | docs/08_reports/ | Complete |
| UNVERIFIED_CLAIMS_REGISTER.md | docs/08_reports/ | Complete |
| UNDOCUMENTED_CODE_REGISTER.md | docs/08_reports/ | Complete |
| DOC_DRIFT_REGISTER.md | docs/08_reports/ | Complete |
| TBD_RESOLUTION_REGISTER.md | docs/08_reports/ | Complete |
| PRE_FRONTEND_READINESS_REPORT.md | docs/08_reports/ | This document |
| OWNER_APPROVAL_ITEMS_BEFORE_PHASE3.md | docs/08_reports/ | Complete — 10 items |
