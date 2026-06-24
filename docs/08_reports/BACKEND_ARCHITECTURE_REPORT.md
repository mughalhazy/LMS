# BACKEND_ARCHITECTURE_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture

Source: Phase 2 Backend Authority Capture — direct code inspection

---

## Purpose

Architecture findings report from Phase 2. Documents the backend structure as-implemented, highlights key patterns, and flags architectural questions that require owner decisions.

---

## Architecture Overview

Meridian LMS backend is a Python-first microservice architecture with 69 registered services across two physical layers. *(count corrected from 65 — pre-frontend delta audit 2026-06-23)*

### Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: backend/services/ (62+ dirs) — ACTIVE HTTP LAYER  │
│                                                              │
│  60 FastAPI (ASGI) services     → ports 8100–8169           │
│   1 FastAPI (api:app variant)   → payment-service 8162      │
│   2 Node.js (npm run start)     → 8124, 8131                │
│   2 stdlib http.server          → auth-service, checkout     │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: services/ (20 dirs) — LIKELY LEGACY               │
│                                                              │
│  3 class-based services registered → 8140, 8141, 8142       │
│  17 other dirs — not registered (likely unactivated)        │
└─────────────────────────────────────────────────────────────┘
```

### Standard Service Internal Structure

```
backend/services/<service-name>/
  app/
    main.py         ← HTTP entrypoint + route handlers
    models.py       ← Domain data models (Pydantic or dataclasses)
    schemas.py      ← Request/response schemas
    service.py      ← Business logic layer
    store.py        ← InMemoryXStore (primary storage)
    store_db.py     ← DB store stub (unused)
    security.py     ← require_jwt, apply_security_headers
    consumers.py    ← Event consumer registration
    events.py       ← InMemoryEventPublisher
    audit.py        ← Audit log helpers (most services)
    middleware.py   ← Custom middleware (some services)
    contracts.py    ← Service contracts (some services)
  tests/
    test_*.py       ← pytest tests (some services)
```

---

## Service Composition Pattern

Every FastAPI service follows this composition pattern:

```python
# 1. Create stores (in-memory)
store = InMemoryXStore()
publisher = InMemoryEventPublisher()

# 2. Inject into service layer
service = XService(store=store, publisher=publisher, ...)

# 3. Create FastAPI app with global auth
app = FastAPI(title="...", dependencies=[Depends(require_jwt)])

# 4. Register event consumers at startup
from .consumers import register_consumers as _register_consumers
_register_consumers()

# 5. Apply cross-cutting middleware
app.middleware("http")(_add_api_version_header)  # X-API-Version: v1
apply_security_headers(app)
```

This pattern is consistent across every inspected FastAPI service. It is clearly a deliberate architectural convention.

---

## Cross-Cutting Concerns

### Authentication (All Services)

Every service applies `require_jwt` as a FastAPI dependency at the app level:
```python
app = FastAPI(dependencies=[Depends(require_jwt)])
```

This gates all routes globally. Exempt paths (health, metrics, etc.) are excluded inside `require_jwt`.

### Tenant Isolation (All Services)

`X-Tenant-Id` header required on all tenant-scoped endpoints. JWT `tenant_id` claim validated against header.

### API Version Header (All Services)

`X-API-Version: v1` middleware applied to every response (CAT-004 compliance).

### Security Headers (FastAPI Services)

`apply_security_headers(app)` adds 5 defensive headers to every response.

### Event Consumer Registration (All Services)

`register_consumers()` called at module load (FA-024 / G-24 compliance).

---

## Dependency Injection Architecture

Services use constructor injection:

```python
service = ProgressService(
    store=store,
    idempotency=idempotency,
    publisher=publisher,
    metrics=metrics
)
```

This makes the service layer testable (stores/publishers can be substituted in tests). However:
- All injected dependencies are currently in-memory implementations
- `store_db.py` stubs exist for future DB implementations but are not injected

---

## Known Architectural Risks

| Risk | ID | Severity |
|---|---|---|
| No persistent database — all services in-memory | RISK-001 | CRITICAL |
| No real message queue | RISK-006 | CRITICAL |
| Checkout data loss on restart | RISK-002 | CRITICAL |
| RS256/HS256 mismatch | RISK-004 | HIGH |
| Ephemeral RSA key on restart | RISK-005 | HIGH |
| Sessions lost on restart | RISK-003 | HIGH |
| Class-based service startup unknown | RISK-014 | HIGH |

Full register: see BACKEND_RISK_REGISTER.md.

---

## Infrastructure Layer

Not fully inspected. Known components:

| Directory | Contents |
|---|---|
| `infrastructure/deployment/` | service-manifest.json (authoritative registry) |
| `infrastructure/event-bus/` | event_topics.json (39 topics) |
| `infrastructure/api-gateway/` | API gateway configuration (not inspected) |
| `infrastructure/observability/` | Monitoring stack (not inspected) |
| `infrastructure/service-discovery/` | Python service discovery utilities |

---

## Frontend Interface

**Frontend Authority Capture not yet executed.** Frontend is Next.js 16 + React 19 + Tailwind v4 (frozen decision). Frontend connects to backend services via HTTP (presumably through API gateway). Frontend-to-backend alignment is documented in `docs/03_fullstack_contracts/` but frontend side is unverified.

---

## Architectural Coherence Assessment

| Area | Status | Notes |
|---|---|---|
| Service boundary definition | Good | Services are well-bounded, single-responsibility |
| Module structure consistency | Good | Standard pattern across all services |
| Dependency injection | Good | Constructor injection enables testing |
| Tenant isolation | Good | Enforced at both JWT and header level |
| API versioning | Mixed | auth-service v2; others v1 |
| HTTP server consistency | Mixed | FastAPI + stdlib http.server coexist |
| Storage layer | Gap | In-memory only — production-blocking |
| Event system | Gap | In-memory only — cross-service delivery broken |
| Security (JWT algorithm) | Gap | RS256/HS256 mismatch |

---

## Open Architectural Questions (From U11, Confirmed Relevant)

| ID | Question | Impact |
|---|---|---|
| D-001 | checkout-service persistence? | RISK-002 |
| D-002 | `service:ClassName` runtime? | RISK-014 |
| D-003 | CI/CD platform? | RISK-008 |
| D-004 | Delete services/file-storage/ and interaction-service/? | Cleanup |
| D-005 | services/commerce/reconciliation.py active? | Commerce integrity |

---

## Related Documents

- `docs/01_backend/BACKEND_ARCHITECTURE.md` — authoritative architecture document
- `docs/01_backend/SERVICE_CATALOG.md` — complete service list
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — risk register
- `docs/08_reports/BACKEND_GAP_REGISTER.md` — gap register
- `docs/08_reports/BACKEND_AUTHORITY_CAPTURE_REPORT.md` — executive summary
- `infrastructure/deployment/service-manifest.json` — service registry
