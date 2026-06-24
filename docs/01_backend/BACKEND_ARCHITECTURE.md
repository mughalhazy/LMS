# BACKEND_ARCHITECTURE

Status: Active
Authority Level: High
Last Reviewed: 2026-06-23
Owner: Human
Phase: Phase 2 — Backend Authority Capture

---

## Purpose

This document captures the backend architecture exactly as implemented. It is derived from direct code inspection and is authoritative over any prior speculative or design documentation. No redesign or forward projection is included.

---

## Service Count and Registry

The authoritative service registry is `infrastructure/deployment/service-manifest.json`.

| Category | Count | Notes |
|---|---|---|
| Total registered services | **69** | Corrected 2026-06-23 (prior count 65 was wrong) |
| FastAPI HTTP services (`app.main:app`) | **63** | Python, FastAPI |
| Non-standard HTTP (`api:app`) | **1** | payment-service |
| Node.js services (`npm run start`) | **2** | prerequisite-engine-service (8124), scorm-service (8131) |
| Class-based services (`service:ClassName`) | **3** | capability-registry (8140), config-service (8141), entitlement-service (8142) — in root `services/` layer; no runtime found (OA-004) |

> GAP-001 RESOLVED: service-manifest.json has 69 services. AI_OPERATING_CONTEXT.md "72 service directories" refers to total directories including shared/ and cache dirs, not registered services. Use 69 as authoritative.

---

## Two-Layer Service Architecture

The repository contains two distinct service layers:

### Layer 1: `backend/services/` — Active HTTP Layer

- **Purpose**: Active microservices exposing HTTP endpoints
- **Count**: ~65 directories (with tests, shared/, and infra dirs excluded)
- **Pattern**: Python FastAPI or Python stdlib `http.server`
- **Startup**: Registered in `infrastructure/deployment/service-manifest.json`
- **Status**: ACTIVE — these are the runtime services

### Layer 2: `services/` (root) — Legacy Class-Based Layer

- **Purpose**: Domain service modules — thin Python classes, no HTTP
- **Count**: 20 directories
- **Pattern**: `models.py` + `service.py`, no HTTP handler
- **Startup**: 3 of these are registered in service-manifest.json via `service:ClassName` — the runtime that interprets this format is unconfirmed (see OWN-001)
- **Status**: LIKELY LEGACY — criteria met, import analysis pending (see LEGACY_AND_ARCHIVE_PLAN.md)

---

## HTTP Server Implementations

Services in `backend/services/` use one of two HTTP server patterns:

### Pattern A: FastAPI (Majority)

Used by: rbac-service, tenant-service, progress-service, enrollment-service, and most others.

```python
app = FastAPI(title="...", version="...", dependencies=[Depends(require_jwt)])

@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response

from .consumers import register_consumers as _register_consumers
_register_consumers()
```

Characteristics:
- `require_jwt` applied at app level (all routes gated)
- `apply_security_headers(app)` for security response headers
- Event consumers registered at module load
- `X-API-Version: v1` middleware header on every response
- `X-Tenant-Id` header required for all tenant-scoped endpoints

### Pattern B: Python stdlib `http.server` (Auth and Checkout)

Used by: auth-service, checkout-service.

```python
class AuthRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        status, payload = self._dispatch()
        self._send(status, payload)

def run(host="0.0.0.0", port=8081):
    server = HTTPServer((host, port), AuthRequestHandler)
    server.serve_forever()
```

Characteristics:
- Manual routing via `if self.path == "..."` dispatch
- Manual JWT validation inline
- Manual `X-API-Version: v1` header set per response
- Synchronous I/O (not async)
- No FastAPI Pydantic automatic validation — manual schema parsing

---

## Standard Module Structure

Every service in `backend/services/<service-name>/app/` follows this structure:

| Module | Purpose | Present In |
|---|---|---|
| `main.py` | HTTP entrypoint, route definitions | All services |
| `models.py` | Domain data classes / Pydantic models | All services |
| `schemas.py` | Request/response schemas | All services |
| `service.py` | Business logic layer | All services |
| `store.py` | In-memory data store (`InMemoryXStore`) | All services |
| `store_db.py` | Database store stub (not used in main.py) | Some services |
| `security.py` | JWT validation, security headers | All services |
| `consumers.py` | Event consumer registration | All services |
| `audit.py` | Audit log helpers | Most services |
| `events.py` | `InMemoryEventPublisher` | Most services |
| `middleware.py` | Custom middleware (e.g., `TenantContextMiddleware`) | Some services |
| `contracts.py` | Service interface contracts | Some services |
| `secrets.py` | Secret retrieval helper | auth-service |

---

## Storage Architecture

**Critical finding**: All backend services use in-memory storage exclusively.

| Store Class | Pattern | Data Persistence |
|---|---|---|
| `InMemoryAuthStore` | Dict in process memory | Lost on restart |
| `InMemoryRBACStore` | Dict in process memory | Lost on restart |
| `InMemoryTenantStore` | Dict in process memory | Lost on restart |
| `InMemoryProgressStore` | Dict in process memory | Lost on restart |
| `InMemoryEnrollmentStore` | Dict in process memory | Lost on restart |
| `InMemoryCheckoutStore` | Dict in process memory | Lost on restart |
| (all services) | Dict in process memory | Lost on restart |

`store_db.py` files exist in some services but are **not used in any `main.py`**. They appear to be stub implementations for future database integration.

This is a critical production gap (see RISK-001 in BACKEND_RISK_REGISTER.md and DATABASE_SCHEMA.md).

---

## Event Architecture

**Critical finding**: Event publishing is in-memory. There is no actual message queue.

```python
publisher = InMemoryEventPublisher()
service = SomeService(store, publisher, ...)
```

- `InMemoryEventPublisher` routes events to consumers registered in the same process
- `register_consumers()` is called at module load in each service's `consumers.py`
- 39 event topics are defined in `infrastructure/event-bus/event_topics.json`
- The event topology (topic → consumer_services) documents intended routing but does not implement it via a real queue

See EVENT_AND_QUEUE_ARCHITECTURE.md for the full topic registry.

---

## Tenant Isolation

Tenant isolation is enforced at two levels:

### 1. Header-Level Isolation (all services)
- `X-Tenant-Id` header required on all non-exempt endpoints
- Services validate the header at the dependency injection layer

### 2. JWT Claim Validation (most services)
- JWT payload `tenant_id` claim is extracted
- Claim must match `X-Tenant-Id` header value
- Mismatch returns `401 tenant_header_jwt_mismatch` or `403 tenant_mismatch`

```python
# enrollment-service example
if jwt_tenant and jwt_tenant != x_tenant_id:
    raise HTTPException(status_code=401, detail="tenant_header_jwt_mismatch")
```

```python
# rbac-service example (via require_tenant_scope)
if not x_tenant_id or not claim_tenant or claim_tenant != x_tenant_id:
    raise HTTPException(status_code=403, detail="tenant_mismatch")
```

---

## API Versioning

- **Primary version**: `/api/v1/`
- **Legacy compatibility**: Some services accept `/api/v2/` via middleware path rewriting
- **Response header**: `X-API-Version: v1` on every response (CAT-004)

```python
# enrollment-service v2 compat middleware
if request.url.path.startswith("/api/v2/"):
    scope["path"] = scope["path"].replace("/api/v2/", "/api/v1/", 1)
```

---

## Security Headers (Standard Set)

All FastAPI services apply via `apply_security_headers(app)`:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `no-referrer` |
| `Cache-Control` | `no-store` |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` |

---

## Port Allocation

- **Registered services**: ports 8100–8169 (from service-manifest.json)
- **Auth-service source code default**: 8081 (may be overridden by manifest or runtime config)
- **Checkout-service source code default**: 8095 (may be overridden by manifest or runtime config)
- **Node.js prerequisite-engine-service**: 8124
- **Node.js scorm-service**: 8131

---

## Configuration Resolution

Implemented in `shared/models/config.py`:

| Level | Enum Value | scope_id Semantics |
|---|---|---|
| GLOBAL | `"global"` | `scope_id` must be `"global"` |
| COUNTRY | `"country"` | country code string |
| SEGMENT | `"segment"` | segment identifier |
| TENANT | `"tenant"` | tenant_id string |

Resolution order: `global → country → segment → tenant` (last wins)

`ConfigResolutionContext` carries: `tenant_id`, `country_code`, `segment_id`

---

## Shared Models

Located at `shared/models/` (root, NEEDS-REVIEW status per LEGACY_AND_ARCHIVE_PLAN.md):

Key models exported:
- `ConfigLevel`, `ConfigOverride`, `ConfigResolutionContext`, `EffectiveConfig`, `SegmentBehaviorConfig`
- `Capability`, `AddOn`, `CapabilityPricing`, `Plan`
- `Branch`, `BranchStatus`
- `UnifiedStudentProfile`, `AcademicState`, `FinancialState`, `GuardianContact`
- `Invoice`, `ExamSessionRecord`
- `TimetableSlot`, `AttendanceSessionEvent`
- `OnboardingMode`, `OnboardingSession`, `OnboardingStatus`

Whether these are actively imported by `backend/services/` is unconfirmed (see OWN-002).

---

## Backend Integrations

Separate integration adapters exist in:
- `integrations/payments/` — JazzCash, EasyPaisa (PROTECTED — production-confirmed)
- `integrations/communication/` — notification delivery adapters (PROTECTED)
- `backend/integrations/` — additional integration code (relationship to root integrations/ unconfirmed — see OWN-003)

---

## Infrastructure

- `infrastructure/deployment/` — service-manifest.json, deployment configs
- `infrastructure/event-bus/` — event_topics.json (39 topics)
- `infrastructure/api-gateway/` — API gateway configuration (not fully inspected)
- `infrastructure/observability/` — monitoring stack (not fully inspected)
- `infrastructure/service-discovery/` — Python service discovery utilities

---

## Known Architectural Gaps

| Gap ID | Description | Risk |
|---|---|---|
| GAP-001 | Service count discrepancy: manifest (65) vs AI_OPERATING_CONTEXT.md (72) | Medium |
| GAP-002 | All services use InMemoryStore — no persistent database | Critical |
| GAP-003 | InMemoryEventPublisher — no actual message queue | Critical |
| GAP-004 | auth-service uses stdlib http.server, not FastAPI | Medium |
| GAP-005 | store_db.py stubs exist but are unused | Medium |
| GAP-006 | `service:ClassName` startup mechanism unconfirmed | High |
| GAP-007 | root services/ layer 3 registered — runtime unknown | High |

Full risk register: see BACKEND_RISK_REGISTER.md.

---

## Related Documents

- `infrastructure/deployment/service-manifest.json` — authoritative service registry
- `infrastructure/event-bus/event_topics.json` — event topic registry
- `docs/01_backend/SERVICE_CATALOG.md` — per-service details
- `docs/01_backend/DATABASE_SCHEMA.md` — storage layer analysis
- `docs/01_backend/EVENT_AND_QUEUE_ARCHITECTURE.md` — event system detail
- `docs/03_fullstack_contracts/AUTH_AND_TENANCY_CONTRACT.md` — auth architecture
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk register
