# BACKEND_RISK_REGISTER

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture / Task 7 Remediation

Source: BACKEND_GAP_REGISTER.md + direct code inspection

---

## Purpose

Risk register for backend implementation. Risk = likelihood of occurrence × impact severity. Derived from gaps identified in Phase 2. Risks are observations only — remediation requires owner decision.

---

## Risk Level Scale

| Level | Definition |
|---|---|
| CRITICAL | Will cause production failure without mitigation |
| HIGH | Will likely cause production incidents under realistic load or failure scenarios |
| MEDIUM | Will degrade quality or cause occasional incidents |
| LOW | Minor — addressable without production impact |

---

## RISK-001: No Persistent Database — Data Loss on Service Restart

| Field | Value |
|---|---|
| **Risk ID** | RISK-001 |
| **Level** | CRITICAL |
| **Status** | **PARTIALLY MITIGATED — Task 7** |
| **Source Gap** | GAP-002 |
| **Description** | Every backend service used in-memory storage. All application data lost on restart or crash. |
| **Mitigation Applied** | 16 critical services switched to SQLite via `store_db.py`: auth-service, rbac-service, enrollment-service, progress-service, tenant-service, assessment-service, certificate-service, lesson-service, program-service, badge-service, session-service, user-service, org-service, cohort-service, institution-service, course-service. |
| **Remaining Risk** | 53 services still in-memory. SQLite is file-backed (survives restart) but not production-grade for distributed or high-availability deployments. |
| **Owner Action** | Architecture decision on production persistence backend (PostgreSQL, etc.) for the remaining 53 services |

---

## RISK-002: Checkout Data Lost on Restart — Payment Data Unrecoverable

| Field | Value |
|---|---|
| **Risk ID** | RISK-002 |
| **Level** | CRITICAL |
| **Source Gap** | GAP-002 (checkout-service) |
| **Description** | checkout-service stores checkout sessions and orders in `InMemoryCheckoutStore`. Restart loses all active payment flows. |
| **Probability** | Certain in production |
| **Impact** | Payment failures, customer disputes, unrecoverable lost orders |
| **Owner Action** | D-001: Owner must decide on persistence backend for checkout-service |
| **Reference** | AI_OPERATING_CONTEXT.md KNOWN_RISKS — `CheckoutService loses data on restart — HIGH — R-005` |

---

## RISK-003: Auth Sessions Lost on Restart — All Users Forced to Re-Login

| Field | Value |
|---|---|
| **Risk ID** | RISK-003 |
| **Level** | HIGH |
| **Status** | **MITIGATED — Task 7** |
| **Source Gap** | GAP-002 (auth-service) |
| **Description** | auth-service stored sessions and credentials in `InMemoryAuthStore`. Restart invalidated all sessions. |
| **Mitigation Applied** | auth-service now uses `SQLiteAuthStore` (7 tables: auth_tenants, auth_user_credentials, auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events). Sessions and credentials survive restart. WAL mode and busy timeout configured. |
| **Remaining** | SQLite is single-process; distributed auth (multiple auth-service replicas) still requires a shared session store. |

---

## RISK-004: RS256/HS256 Algorithm Mismatch

| Field | Value |
|---|---|
| **Risk ID** | RISK-004 |
| **Level** | HIGH |
| **Status** | **MITIGATED — Task 7** |
| **Source Gap** | GAP-008 |
| **Description** | auth-service issues RS256 JWTs; consuming services validated HS256 only and rejected RS256 tokens with 401. |
| **Mitigation Applied** | `_validate_rs256_jwt()` added to all 32 consuming service security.py files. `require_jwt()` now peeks at JWT header `alg` claim and routes accordingly: RS256 → cryptography-backed validation via `JWT_PUBLIC_KEY`; HS256 → HMAC-SHA256 via `JWT_SHARED_SECRET`. Both algorithms coexist during rollout window. |
| **Canonical Implementation** | `backend/services/shared/security.py` — drop-in replacement for per-service security modules. |
| **Remaining** | `JWT_PUBLIC_KEY` env var (PEM) must be set in each service environment. Without it, RS256 tokens return 503 `jwt_public_key_not_configured`. |

---

## RISK-005: Ephemeral RSA Key — RS256 Tokens Invalidated on Restart

| Field | Value |
|---|---|
| **Risk ID** | RISK-005 |
| **Level** | HIGH |
| **Source Gap** | GAP-004 |
| **Description** | auth-service generates an ephemeral in-process RSA key when `JWT_PRIVATE_KEY` env var is not set. Every restart generates a new key, invalidating all previously issued RS256 tokens. |
| **Code** | `# Ephemeral key for development — tokens invalidated on restart` |
| **Probability** | High — if `JWT_PRIVATE_KEY` is not set in production |
| **Impact** | All users logged out on every deployment |
| **Required Action** | Set `JWT_PRIVATE_KEY` to a stable PEM-encoded RSA private key in production |

---

## RISK-006: No Cross-Service Event Delivery

| Field | Value |
|---|---|
| **Risk ID** | RISK-006 |
| **Level** | CRITICAL |
| **Source Gap** | GAP-003 |
| **Description** | `InMemoryEventPublisher` only delivers events within the same process. Cross-service event subscriptions (as defined in event_topics.json) are not implemented. |
| **Impact** | All event-driven workflows silently fail. Example: `enrollment.created` event never reaches progress-service or certificate-service in practice. |
| **Required Action** | Message broker (Kafka, RabbitMQ, Redis Streams, etc.) required |

---

## RISK-007: Idempotency Protection Lost on Restart

| Field | Value |
|---|---|
| **Risk ID** | RISK-007 |
| **Level** | HIGH |
| **Status** | **PARTIALLY MITIGATED — Task 7** |
| **Source Gap** | GAP-010 |
| **Description** | `InMemoryIdempotencyStore` resets on service restart. Duplicate requests bypass idempotency after restart. |
| **Mitigation Applied** | progress-service now uses `SQLiteIdempotencyStore` (idempotency keys persisted to SQLite, survive restart). |
| **Remaining** | checkout-service still uses `InMemoryIdempotencyStore` — no SQLite idempotency store implemented for checkout. Payment duplicate risk remains. |
| **Required Action** | Implement SQLite or Redis-backed idempotency store for checkout-service |

---

## RISK-008: No CI/CD — Tests Not Enforced

| Field | Value |
|---|---|
| **Risk ID** | RISK-008 |
| **Level** | HIGH |
| **Source Gap** | None (pre-existing) |
| **Description** | No CI/CD pipeline exists. Tests are not automatically run. Code changes can be deployed without test validation. |
| **Reference** | AI_OPERATING_CONTEXT.md KNOWN_RISKS — `No CI/CD — tests not automatically enforced — HIGH — R-013` |
| **Required Action** | D-003: Owner decision on CI/CD platform |

---

## RISK-009: entitlement-service Crash Risk

| Field | Value |
|---|---|
| **Risk ID** | RISK-009 |
| **Level** | HIGH |
| **Source Gap** | None (pre-existing) |
| **Description** | entitlement-service crashes if `backend/shared/events` is absent |
| **Reference** | AI_OPERATING_CONTEXT.md KNOWN_RISKS — `R-001 (implement dependency injection)` |
| **Required Action** | Implement R-001: DI to remove hard dependency |

---

## RISK-010: Circular Import (commerce ↔ subscription-service)

| Field | Value |
|---|---|
| **Risk ID** | RISK-010 |
| **Level** | HIGH |
| **Source Gap** | None (pre-existing) |
| **Description** | Circular import between commerce domain and subscription-service |
| **Reference** | AI_OPERATING_CONTEXT.md KNOWN_RISKS — `R-004 (extract shared models)` |
| **Required Action** | Implement R-004: extract shared models to break cycle |

---

## RISK-011: auth-service Startup Mechanism Mismatch

| Field | Value |
|---|---|
| **Risk ID** | RISK-011 |
| **Level** | MEDIUM |
| **Status** | **RESOLVED — Task 7** |
| **Source Gap** | GAP-004 |
| **Description** | service-manifest.json registered auth-service as `app.main:app` but main.py had no `app` variable. |
| **Resolution** | FastAPI ASGI `app` object added to `backend/services/auth-service/app/main.py`. Uvicorn `app.main:app` startup now works. Shim delegates all routes to existing `SERVICE` methods. |

---

## RISK-012: checkout-service Startup Mechanism Mismatch

| Field | Value |
|---|---|
| **Risk ID** | RISK-012 |
| **Level** | MEDIUM |
| **Status** | **RESOLVED — Task 7** |
| **Source Gap** | GAP-007 |
| **Description** | checkout-service used stdlib HTTPServer but registered as `app.main:app`. |
| **Resolution** | FastAPI ASGI `app` object added to `backend/services/checkout-service/app/main.py`. Uvicorn startup now works. |

---

## RISK-013: frontend Has Zero Tests

| Field | Value |
|---|---|
| **Risk ID** | RISK-013 |
| **Level** | HIGH |
| **Source Gap** | None (pre-existing) |
| **Description** | Frontend codebase has zero automated tests |
| **Reference** | AI_OPERATING_CONTEXT.md KNOWN_RISKS — `Frontend has zero tests — HIGH — U9 test plan P7/P8` |
| **Required Action** | Frontend test implementation plan (P7/P8) |

---

## RISK-014: Class-Based Services Not Verified as Running

| Field | Value |
|---|---|
| **Risk ID** | RISK-014 |
| **Level** | HIGH |
| **Source Gap** | GAP-006 |
| **Description** | capability-registry, config-service, entitlement-service use `service:ClassName` in manifest. No runtime for this format has been found or documented. |
| **Impact** | These 3 services may not be running in any environment |
| **Required Action** | D-002: Owner must identify the startup mechanism |

---

## Risk Summary

| Level | Open | Resolved / Mitigated by Task 7 |
|---|---|---|
| CRITICAL | 2 (RISK-002, RISK-006) | RISK-001 partially mitigated (16 services) |
| HIGH | 7 (RISK-005, RISK-007 partial, RISK-008–RISK-010, RISK-013, RISK-014) | RISK-003 mitigated, RISK-004 mitigated, RISK-007 partially |
| MEDIUM | 0 | RISK-011 resolved, RISK-012 resolved |
| LOW | 0 | — |
| **Total open** | **9** | 6 fully/partially resolved by Task 7 |

**Task 7 resolved:** RISK-003, RISK-004, RISK-011, RISK-012 (fully); RISK-001, RISK-007 (partially).
**Still open:** RISK-002 (checkout InMemory), RISK-005 (ephemeral RSA key), RISK-006 (cross-process events), RISK-007 (checkout idempotency), RISK-008 (no CI/CD), RISK-009 (entitlement-service DI), RISK-010 (circular import), RISK-013 (frontend tests), RISK-014 (class-based startup).

---

## Pre-Existing Risks (Carried from AI_OPERATING_CONTEXT.md)

These risks were documented before Phase 2 and are confirmed by code inspection:

| Prior ID | Risk | Phase 2 Verdict |
|---|---|---|
| R-001 | entitlement-service DI crash | Confirmed — RISK-009 |
| R-004 | Circular import commerce↔subscription | Confirmed — RISK-010 |
| R-005 | Checkout data loss | Confirmed CRITICAL — RISK-002 |
| R-012 | HS256 security gap | Confirmed HIGH — RISK-004 |
| R-013 | No CI/CD | Confirmed — RISK-008 |
| R-008 | 25 services without specs | Confirmed MEDIUM — GAP-014 |

---

## Related Documents

- `docs/08_reports/BACKEND_GAP_REGISTER.md` — gap register
- `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` — executive summary
- `docs/01_backend/DATABASE_SCHEMA.md` — database gaps
- `workspace/sessions/U11/U11_LMS_REMEDIATION_PLAN.md` — remediation plan
- `workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md` — governance blockers
