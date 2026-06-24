# ADR-001: Project Foundation

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-21
Owner: Human
Supersedes: None
Superseded by: N/A

---

## Context

Meridian LMS began as a Rails LMS runtime ("Enterprise LMS V2") and has been extended with a Python microservices architecture. A significant body of documentation, design decisions, and implementation work was completed through sessions U0â€“U11 before formal governance was established. This ADR records all foundational decisions as of governance entry.

---

## Project Purpose

Build a multi-tenant SaaS Learning Management System for Pakistan's education market, starting with tuition centers and academies, with architecture designed for:

1. Pakistan-first product-market fit
2. Global capability platform expansion (MENA/South Asia)
3. AI-enhanced learning as a differentiator
4. Enterprise-grade multi-tenancy

---

## Current Architecture

### Platform Layers

| Layer | Technology | Purpose |
|---|---|---|
| Domain services | Python (plain classes, importlib) | Business logic, orchestration |
| HTTP presentation | Python FastAPI | REST API endpoints |
| Adapters | Python | JazzCash/EasyPaisa, WhatsApp/SMS/Email |
| Frontend | Next.js 16 + React 19 + Tailwind v4 | Web application |
| Shared | Python dataclasses | Cross-service data contracts |

### Service Counts (Verified 2026-06-21)

| Layer | Count | Notes |
|---|---|---|
| Domain services (services/) | 20 directories | 3 manifest-deployed, 5 active runtime, 10 duplicated, 2 orphaned |
| HTTP services (backend/services/) | 69 directories | 67 Python/FastAPI + 2 Node.js |
| Manifest-registered deployed | 72 total | 69 HTTP + 3 class-based |

### Rails Runtime Heritage

The learning lifecycle anchors from the original Rails LMS remain authoritative:
- User, Course, Lesson, Enrollment, Progress, Certificate
- These entities power enrollment, content consumption, completion tracking, and credential issuance
- New services layer around this runtime via APIs and events

---

## Core Technology Choices

### Decision 1: Python + FastAPI for Backend Services

**Decision:** All new backend services are Python/FastAPI ASGI applications.
**Rationale:** Existing codebase; team expertise; strong async support; test patterns established.
**Constraint:** service-manifest.json defines all 69 backend services; no service may be removed without updating the manifest.

### Decision 2: Next.js 16 + React 19 + Tailwind v4 for Frontend

**Decision:** Frontend is Next.js 16 with React 19 and Tailwind v4.
**Rationale:** Existing codebase.
**Constraint:** All npm/pnpm paths sealed to D: drive; NEXT_TELEMETRY_DISABLED=1.

### Decision 3: JWT RS256 as Platform Auth Standard

**Decision:** All services must use JWT RS256 for authentication.
**Rationale:** Asymmetric key prevents token forgery; public key can be distributed to all services without exposing signing capability.
**Exceptions (tracked technical debt):** notification-service (B05-002), subscription-service (B10-006), catalog-service â€” all use HS256; migration required (R-012).

### Decision 4: Canonical Event Envelope (7 Fields)

**Decision:** All domain events must use the 7-field canonical envelope.
**Fields:** event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata
**Authority:** docs/anchors/event-envelope.md
**Source of truth for topics:** event_topics.json (39 topics; 0 phantom consumers as of U7)

### Decision 5: Tenant-First Isolation

**Decision:** tenant_id is the primary isolation key for all data, config, and entitlement.
**Rationale:** Multi-tenant SaaS; strict data isolation is a non-negotiable product constraint.
**Implementation:** Row-level isolation, API middleware tenant context propagation, config hierarchy scoped to tenant.

### Decision 6: Config Resolution Hierarchy

**Decision:** Configuration resolves through a fixed hierarchy: global → country → segment → tenant (4 levels).
**Implementation:** services/config-service/service.py — ConfigLevel enum: GLOBAL, COUNTRY, SEGMENT, TENANT. ConfigResolutionContext fields: tenant_id, country_code, segment_id (no plan_type field).
**Constraint (MS-CONFIG-01):** Services must NOT branch on country/segment discriminators in business logic. Behavioral variation is expressed only through resolved config values.
**Note on plan_type:** The tenant's plan_type field is used by the entitlement service to make allow/deny decisions for capabilities. It is NOT a config resolution layer — the ConfigLevel enum has no PLAN value and ConfigResolutionContext has no plan_type field. Plan-based capability differentiation is an entitlement concern, not a config concern.

### Decision 7: Capability Resolution Sequence

**Decision:** Capability state must be determined in a fixed sequence: capability (definition) → config (overrides) → entitlement (decision) → final_state.
**Authority:** docs/anchors/capability-resolution.md
**Implementation:** services/capability-registry/, services/config-service/, services/entitlement-service/
**Constraint:** The three services must not overlap responsibilities.

### Decision 8: Pakistan-First Commerce

**Decision:** The initial commerce implementation targets Pakistan only.
**Evidence:** `build_commerce_service_for_pakistan(default_provider="jazzcash")` is the only country factory in services/commerce/service.py.
**Payment providers:** JazzCash (default), EasyPaisa.
**Expansion:** Country-specific factories can be added for new markets.

### Decision 9: Two-Layer Domain Architecture

**Decision:** Business logic lives in services/ (domain layer); HTTP routing lives in backend/services/ (presentation layer).
**Rationale:** Clean architecture / hexagonal architecture intent â€” domain should be independently testable without HTTP.
**Current state:** Architecture is transitional â€” 3 reverse dependencies violate clean separation (R-001, R-002, R-003 in U11). These are tracked debts.
**Authority:** workspace/sessions/U10/U10_LMS_ARCHITECTURE_DECISION_REPORT.md

### Decision 10: importlib Dynamic Loading for Service Composition

**Decision:** Domain services compose peer services via `importlib.util.spec_from_file_location()` rather than package imports.
**Rationale:** No Python package structure required; flexible loading order.
**Risk:** sys.path mutation accumulates; module re-execution risk (see R-010).
**Mitigations planned:** module cache guard + sys.path deduplication (R-010).

---

## Known Constraints

| Constraint | Source | Impact |
|---|---|---|
| No C: drive writes | U8 workspace sealing | All tooling paths on D: |
| `python` not on PATH | Confirmed | Use `py -3` everywhere |
| Dockerfiles/CI-CD exist in infrastructure/ (do not add new ones) | Phase 2.9 confirmed | Dockerfile.python, Dockerfile.node, docker-compose.yml, deploy-backend.yml present; constraint updated 2026-06-23 |
| services/ requires backend/ on path | Reverse dependencies | Services not independently deployable yet |
| JazzCash/EasyPaisa only | Domain layer | Other markets need new payment factories |
| Frontend has zero tests | U9 confirmed | Full frontend test infrastructure needed |
| CheckoutService in-memory | U10 confirmed | Persistence strategy needed (R-005) |

---

## Major Assumptions

| Assumption | Confidence | Evidence |
|---|---|---|
| Rails core entities are the system of record | HIGH | migrations in backend/services/; progress-service/src/entities.py |
| Pakistan is the primary launch market | HIGH | build_commerce_service_for_pakistan(); JazzCash/EasyPaisa integration; market docs |
| JazzCash is production-confirmed | HIGH | .pyc in services/commerce/ â€” code was executed |
| 3 class-based services are deployed | HIGH | service-manifest.json `service:ClassName` entries |
| backend/checkout-service handles DB persistence | ASSUMED (D-001 unconfirmed) | services/commerce/checkout.py is domain logic |
| Docker Compose and CI/CD YAML exist in infrastructure/ | CONFIRMED | infrastructure/deployment/docker/, infrastructure/deployment/cicd/ verified Phase 2.9 |

---

## Known Risks

| Risk | Severity | Status | Remediation |
|---|---|---|---|
| Reverse dependencies (services/ → backend/) | HIGH | Open | R-001, R-002, R-003 |
| Circular import: commerce â†” subscription | HIGH | Open | R-004 |
| CheckoutService in-memory storage | HIGH | Open | R-005 (owner decision) |
| HS256 on 3 services | HIGH | Open | R-012 |
| No CI/CD pipeline | HIGH | Open | R-013 (owner decision) |
| 25 services without canonical specs | MEDIUM | Open | R-008 |
| Class-based service startup undocumented | MEDIUM | Open | R-009 (owner decision) |
| Frontend zero tests | HIGH | Open | U9 test plan P7/P8 |

---

## Architectural Principles

*Canonical list. These 8 principles are the authoritative governance reference. PROJECT_CHARTER.md §9 contains the same list — both documents must remain in sync.*

1. **Tenant-first isolation** — tenant_id is the primary isolation key; mandatory and immutable in all data operations; no cross-tenant data access
2. **Config resolution hierarchy** — global → country → segment → tenant (4 levels per ConfigLevel enum); no runtime branching on country/segment discriminators (MS-CONFIG-01); behavioral variation expressed only through resolved config values
3. **Capability resolution sequence** — capability → config → entitlement → final_state (fixed, mandatory); see docs/anchors/capability-resolution.md
4. **Single system of record** — one service owns each entity; no dual writes
5. **Event-driven decoupling** — domain events use the 7-field canonical envelope (docs/anchors/event-envelope.md); no direct synchronous service coupling for async workflows
6. **RS256 JWT standard** — all services must use RS256; HS256 exceptions (notification, subscription, catalog) are tracked debts (R-012); never add new HS256 services
7. **Pakistan-first commerce** — JazzCash is the default payment provider; commerce is country-parameterized via factory pattern (build_commerce_service_for_pakistan); extensible to new markets
8. **Domain/HTTP separation** — services/ provides domain logic; backend/services/ provides HTTP; services/ must not import backend/ (3 current violations tracked as R-001, R-002, R-003)


---

## Governance Session History

| Session | Date | Output Location |
|---|---|---|
| U0 â€” Repository Reality Discovery | 2026-06-20 | workspace/sessions/U0/ |
| U1 â€” Authority Reconstruction | 2026-06-20 | workspace/sessions/U1/ |
| U2 â€” Documentation Catalogue | 2026-06-20 | workspace/sessions/U2/ |
| U3 â€” Documentation Normalization | 2026-06-20 | workspace/sessions/U3/ |
| U4 â€” Workspace Restructuring Plan | 2026-06-20 | workspace/sessions/U4/ |
| U5 â€” Workspace Restructuring Execution | 2026-06-20 | workspace/sessions/U5/ |
| U6 â€” Doc-to-Code Delta Analysis | 2026-06-20 | workspace/sessions/U6/ |
| U7 â€” Delta Remediation | 2026-06-20 | workspace/sessions/U7/ |
| U8 â€” Workspace Sealing | 2026-06-21 | workspace/sessions/U8/ |
| U9 â€” Test Suite Planning | 2026-06-21 | workspace/sessions/U9/ |
| U10 â€” Two-Layer Architecture Forensic | 2026-06-21 | workspace/sessions/U10/ |
| U11 â€” Remediation Plan | 2026-06-21 | workspace/sessions/U11/ |
| Governance Phase 1 | 2026-06-21 | docs/00_authority/ (5 docs), docs/06_decisions/ (1 doc), docs/07_governance/ (2 docs), docs/08_reports/ (4 docs) |

