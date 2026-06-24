# UNVERIFIED CLAIMS REGISTER

Status: Active
Date: 2026-06-23
Phase: Pre-Frontend Delta Audit
Source: Direct code inspection + five-domain audit

Claims in documentation that cannot be verified against repository evidence, or that are directly contradicted by code.

---

## UCR-001: Service Count — 65 Services Claimed

| Field | Value |
|---|---|
| **ID** | UCR-001 |
| **Severity** | HIGH |
| **Claim** | "Total services: 65" |
| **Sources** | SERVICE_CATALOG.md:15, BACKEND_ARCHITECTURE.md:23, BACKEND_AUTHORITY_CAPTURE_REPORT.md (×6), BACKEND_ARCHITECTURE_REPORT.md:21, API_DISCOVERY_REPORT.md:200 |
| **Reality** | Manifest has 69 services. 63 `app.main:app` + 1 `api:app` (payment) + 2 Node.js + 3 class-based = 69. |
| **Fix** | Doc correction — update all occurrences of "65" to "69" |

---

## UCR-002: All Services Use In-Memory Storage

| Field | Value |
|---|---|
| **ID** | UCR-002 |
| **Severity** | CRITICAL |
| **Claim** | "All backend services use in-memory storage exclusively. No service connects to a persistent database." |
| **Sources** | DATABASE_SCHEMA.md:19, DATABASE_DISCOVERY_REPORT.md:21 |
| **Reality** | 16 services use SQLite via complete store_db.py implementations wired in main.py (Task 7). |
| **Fix** | Doc correction — update both documents to reflect 16 SQLite services |

---

## UCR-003: store_db.py Are Stub Implementations

| Field | Value |
|---|---|
| **ID** | UCR-003 |
| **Severity** | HIGH |
| **Claim** | "store_db.py appear to be stub implementations intended for future database integration. They are not imported or used by any main.py file." |
| **Sources** | DATABASE_SCHEMA.md:56, DATABASE_DISCOVERY_REPORT.md:46–48 |
| **Reality** | store_db.py files are complete, production-quality SQLite implementations with full CRUD, WAL mode, foreign keys, tenant isolation. 16 are now actively imported and wired. |
| **Fix** | Doc correction |

---

## UCR-004: Consuming Services Validate HS256 Only

| Field | Value |
|---|---|
| **ID** | UCR-004 |
| **Severity** | HIGH |
| **Claim** | "Most services validate HS256 only. They cannot validate RS256 tokens." Table showing rbac-service, tenant-service, etc. as HS256-only. |
| **Sources** | AUTH_AND_TENANCY_CONTRACT.md:49–61, SECURITY_DISCOVERY_REPORT.md:27–33 |
| **Reality** | Task 7 added RS256 validation to 33 consuming services. All use alg-claim routing (RS256 → JWT_PUBLIC_KEY; HS256 → JWT_SHARED_SECRET). |
| **Fix** | Doc correction — update table and "Security debt" paragraph |

---

## UCR-005: Auth Sessions in InMemoryAuthStore

| Field | Value |
|---|---|
| **ID** | UCR-005 |
| **Severity** | HIGH |
| **Claim** | "Sessions are stored in InMemoryAuthStore. All sessions are lost on auth-service restart." |
| **Sources** | AUTH_AND_TENANCY_CONTRACT.md:102, FULLSTACK_STITCHING_CONTRACT.md cross-cutting table |
| **Reality** | auth-service now uses SQLiteAuthStore (Task 7). Sessions persist across restarts. |
| **Fix** | Doc correction |

---

## UCR-006: All Storage Is In-Memory (FULLSTACK_STITCHING_CONTRACT)

| Field | Value |
|---|---|
| **ID** | UCR-006 |
| **Severity** | HIGH |
| **Claim** | "All storage is in-memory: Yes" and "All events are in-memory — InMemoryEventPublisher: Yes" |
| **Sources** | FULLSTACK_STITCHING_CONTRACT.md Phase 2 Addendum cross-cutting facts table |
| **Reality** | 16 services use SQLite. In-process EventBus (not InMemoryEventPublisher) is active. |
| **Fix** | Doc correction |

---

## UCR-007: Login Response Fields — user_id and tenant_id at Top Level

| Field | Value |
|---|---|
| **ID** | UCR-007 |
| **Severity** | CRITICAL — Frontend will break |
| **Claim** | Login response: `{"session_id":"...","access_token":"...","refresh_token":"...","user_id":"...","tenant_id":"...","roles":[...],"expires_in":...,"token_type":"Bearer"}` |
| **Sources** | AUTH_AND_TENANCY_CONTRACT.md, DATA_SHAPE_REGISTRY.md |
| **Reality** | Actual code (auth-service/app/service.py:144–152): `user_id` and `tenant_id` are nested under a `"user"` sub-object; `roles` is absent from response (only in JWT); `refresh_expires_in` is an extra undocumented field. |
| **Fix** | Doc correction — update login response shape in both documents |

---

## UCR-008: JWT Claim for User Identifier is "user_id"

| Field | Value |
|---|---|
| **ID** | UCR-008 |
| **Severity** | CRITICAL — Frontend will break |
| **Claim** | Contract implies `user_id` is the JWT claim name for the user identifier |
| **Sources** | AUTH_AND_TENANCY_CONTRACT.md, DATA_SHAPE_REGISTRY.md |
| **Reality** | auth-service/app/service.py:111 sets `"sub": user.user_id`. JWT uses standard `sub` claim, not `user_id`. Frontend must read `payload.sub`. |
| **Fix** | Doc correction — explicitly document `sub` as user identifier claim |

---

## UCR-009: Tenant Shape Has 4 Fields (active, domain)

| Field | Value |
|---|---|
| **ID** | UCR-009 |
| **Severity** | HIGH |
| **Claim** | Tenant object: `{tenant_id, name, active, domain}` |
| **Sources** | DATA_SHAPE_REGISTRY.md |
| **Reality** | Canonical anchor (docs/anchors/tenant-contract.md, TIER 1): 6 fields — `tenant_id, name, country_code, segment_type, plan_type, addon_flags`. `active` and `domain` are not canonical fields. Confirmed by tenant-service/app/schemas.py:24–30. |
| **Fix** | Doc correction — update tenant shape to match anchor and code |

---

## UCR-010: Event Envelope Shape — "occurred_at" and "version"

| Field | Value |
|---|---|
| **ID** | UCR-010 |
| **Severity** | HIGH |
| **Claim** | Event envelope: `{event_id, event_type, tenant_id, producer_service, occurred_at, version, payload}` |
| **Sources** | DATA_SHAPE_REGISTRY.md |
| **Reality** | Canonical anchor (docs/anchors/event-envelope.md): uses `timestamp` (not `occurred_at`); no `version` field; has `correlation_id` and `metadata`. Code (shared/events/envelope.py): 10 fields — adds `topic`, `producer_service`, `schema_version` to anchor's 7. Registry omits `correlation_id` and `metadata`. |
| **Fix** | Doc correction — align with anchor and code |

---

## UCR-011: "70 Named Services" in Repository Tree Inventory

| Field | Value |
|---|---|
| **ID** | UCR-011 |
| **Severity** | LOW |
| **Claim** | "70 named services" in backend/services/ |
| **Sources** | REPOSITORY_TREE_INVENTORY.md:126 |
| **Reality** | 69 service directories (confirmed via manifest count). The inventory overstates by 1. |
| **Fix** | Doc correction |

---

## UCR-012: docs/01_backend/ Is Empty

| Field | Value |
|---|---|
| **ID** | UCR-012 |
| **Severity** | MEDIUM |
| **Claim** | "docs/01_backend/ — EMPTY placeholder" |
| **Sources** | REPOSITORY_TREE_INVENTORY.md |
| **Reality** | Contains 8 Phase 2 authority documents (API_CONTRACT.md, BACKEND_ARCHITECTURE.md, DATABASE_SCHEMA.md, ERROR_CONTRACT.md, EVENT_AND_QUEUE_ARCHITECTURE.md, INTEGRATION_CATALOG.md, SERVICE_CATALOG.md, VALIDATION_RULES.md). |
| **Fix** | Doc correction — update inventory entry |

---

## UCR-013: docs/03_ops/ Directory Exists

| Field | Value |
|---|---|
| **ID** | UCR-013 |
| **Severity** | LOW |
| **Claim** | "docs/03_ops/" listed in tree inventory |
| **Sources** | REPOSITORY_TREE_INVENTORY.md |
| **Reality** | Directory is actually `docs/03_fullstack_contracts/` containing 5 authority documents. |
| **Fix** | Doc correction — update inventory |

---

## UCR-014: notification-service Uses FastAPI (Not Flagged as Non-Standard)

| Field | Value |
|---|---|
| **ID** | UCR-014 |
| **Severity** | HIGH |
| **Claim** | SERVICE_CATALOG.md lists only auth-service and checkout-service in the "Non-Standard Services" table as stdlib http.server. |
| **Sources** | SERVICE_CATALOG.md |
| **Reality** | notification-service (port 8122) also uses `BaseHTTPRequestHandler` with no FastAPI `app` object. Uvicorn startup with `app.main:app` would fail (no ASGI shim exists unlike auth/checkout). |
| **Fix** | Doc correction + owner approval needed for ASGI shim code fix |

---

## UCR-015: RBAC Health Path

| Field | Value |
|---|---|
| **ID** | UCR-015 |
| **Severity** | LOW |
| **Claim** | Contract implies rbac-service health endpoint at `/health` |
| **Sources** | API_CONTRACT.md |
| **Reality** | Router uses prefix `/api/v1/rbac` making actual health path `/api/v1/rbac/health` |
| **Fix** | Doc correction |

---

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 3 (UCR-007, UCR-008, UCR-009 variant) |
| HIGH | 8 |
| MEDIUM | 1 |
| LOW | 3 |
| **Total** | **15** |
