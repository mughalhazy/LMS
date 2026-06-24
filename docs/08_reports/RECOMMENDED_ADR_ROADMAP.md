# RECOMMENDED_ADR_ROADMAP

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-21
Owner: AI

---

## Purpose

Recommends the next Architecture Decision Records (ADRs) to create as governance matures. ADR-001 (Project Foundation) is already complete and covers all foundational decisions.

These ADRs should be created in priority order as decisions are made or confirmed.

---

## Priority 1 — Required Before Governance Implementation (U12)

### ADR-002: Reverse Dependency Elimination Strategy

**Decision needed:** How will services/ → backend/ reverse dependencies be eliminated?
**Options to evaluate:**
- Option A: Dependency injection via Protocol/ABC (recommended in U11 R-001, R-003)
- Option B: Extract shared libraries (move events envelope + progress interface to shared/)
- Option C: Merge layers (collapse services/ into backend/services/)

**Inputs required:** U11 R-001, R-003 plans; owner architectural preference
**Governance blocker:** GEB-001
**Estimated creation:** After owner review of R-001 and R-003

---

### ADR-003: Circular Import Resolution

**Decision needed:** How will the commerce ↔ subscription-service circular import be resolved?
**Options to evaluate:**
- Option A: Extract SubscriptionPlan to shared/models/plan.py (preferred — plan is a domain model)
- Option B: Extract BillingService interface to shared/protocols/
- Option C: Remove subscription-service direct import; inject BillingService into subscription-service

**Inputs required:** U11 R-004 plan
**Governance blocker:** GEB-002
**Estimated creation:** Alongside R-004 implementation

---

### ADR-004: CheckoutService Persistence Strategy

**Decision needed:** What persistence backend will CheckoutService use?
**Owner decision required:** D-001 — does backend/checkout-service already handle DB persistence?
**Options to evaluate:**
- Option A: PostgreSQL via SQLAlchemy (full ACID; idempotency guaranteed across restarts)
- Option B: Redis (fast; TTL-based idempotency; risk of loss on Redis failure)
- Option C: Backend/checkout-service already persists; services/commerce/checkout.py is domain-only
- Option D: Hybrid (Redis for sessions; PostgreSQL for orders)

**Governance blocker:** GEB-003
**Estimated creation:** After D-001 owner confirmation

---

### ADR-005: CI/CD Platform and Deployment Strategy

**Decision needed:** Which CI/CD platform, container runtime, and deployment target?
**Owner decision required:** D-003
**Options to evaluate:**
- CI: GitHub Actions / GitLab CI / Jenkins
- Container: Docker + Kubernetes / Docker + ECS / other
- Deployment target: AWS / GCP / Azure / DigitalOcean / bare metal

**Governance blocker:** GEB-007
**Estimated creation:** After D-003 owner confirmation

---

### ADR-006: HS256 → RS256 Migration Approach

**Decision needed:** How and when will notification-service, subscription-service, and catalog-service migrate from HS256 to RS256?
**Options to evaluate:**
- Option A: Rolling migration (one service at a time, coordinated with clients)
- Option B: Flag day (all three simultaneously)
- Option C: Parallel run (accept both temporarily via algorithm negotiation)

**Governance blocker:** GEB-004
**Estimated creation:** Before R-012 implementation

---

## Priority 2 — Required During Governance

### ADR-007: Class-Based Service Deployment Model

**Decision needed:** Document the deployment and runtime model for the three class-based services.
**Owner decision required:** D-002
**Content:** How `service:CapabilityRegistryService`, `service:ConfigService`, `service:EntitlementService` are started, health-checked, managed, and updated.
**Estimated creation:** After D-002 owner confirmation

---

### ADR-008: Event Topic Consolidation

**Decision needed:** Resolve the duplicate lesson completion event topic (OI-001):
- `lms.lesson.completed.v1` vs `lms.progress.lesson_completed.v1`
- Which is canonical? Which is deprecated?
- What is the migration plan for consumers?

**Estimated creation:** After owner design review of event topology

---

### ADR-009: Import Safety and Module Loading Strategy

**Decision needed:** Formalize the importlib composition pattern with safety guards.
**Content:** Document the `_load_module()` pattern; specify required guards (cache check + sys.path dedup); optionally centralize in shared/utils/module_loader.py.

**Estimated creation:** Alongside R-010 implementation

---

### ADR-010: Orphaned services/ Disposition

**Decision needed:** What happens to services/file-storage/ and services/interaction-service/?
**Owner decision required:** D-004
**Options:** Keep as stubs; delete; implement; migrate to shared/

**Estimated creation:** After D-004 owner confirmation

---

## Priority 3 — Before Frontend Development

### ADR-011: Frontend Testing Strategy

**Decision needed:** Formally adopt Vitest + Playwright as the frontend test stack (U9 recommendation).
**Content:** Vitest configuration for unit tests; Playwright configuration for E2E; coverage requirements; critical user journey test definitions (CJ-001 through CJ-005).
**Estimated creation:** Before any frontend feature development begins

---

### ADR-012: Frontend State Management and API Client Pattern

**Decision needed:** How does the Next.js frontend communicate with the 69 backend services?
**Content:** API client architecture; authentication token management; service discovery (or direct endpoint config); error handling conventions.
**Inputs required:** Frontend audit (not yet performed — frontend TBD in Phase 1)
**Estimated creation:** During frontend audit (Phase 2 governance)

---

## Priority 4 — Future Scope

### ADR-013: Multi-Country Expansion Model

**Decision needed:** When and how will commerce expand beyond Pakistan (PK)?
**Content:** New country factories pattern; payment adapter selection; config hierarchy country-layer expansion; Urdu i18n (MO-041) as first expansion step.
**Estimated creation:** When expansion is planned

---

### ADR-014: Adaptive Learning Engine Architecture

**Decision needed:** Is the adaptive learning engine (docs/designs/adaptive-learning-engine.md) being built? If so, on what timeline?
**Content:** Feature status confirmation; backend service requirements; AI/ML integration approach.
**Estimated creation:** When adaptive learning is prioritized

---

### ADR-015: Observability Stack Implementation

**Decision needed:** Which observability tools implement the documented observability architecture?
**Content:** Logging framework; metrics backend; distributed tracing; alert routing.
**Estimated creation:** Alongside CI/CD pipeline (ADR-005)

---

## ADR Registry

| ADR | Title | Status | Priority |
|---|---|---|---|
| ADR-001 | Project Foundation | Active | Complete |
| ADR-002 | Reverse Dependency Elimination | Pending D-001 | P1 |
| ADR-003 | Circular Import Resolution | Pending | P1 |
| ADR-004 | CheckoutService Persistence | Pending D-001 | P1 |
| ADR-005 | CI/CD and Deployment | Pending D-003 | P1 |
| ADR-006 | HS256 → RS256 Migration | Pending | P1 |
| ADR-007 | Class-Based Service Deployment | Pending D-002 | P2 |
| ADR-008 | Event Topic Consolidation | Pending | P2 |
| ADR-009 | Import Safety Strategy | Pending | P2 |
| ADR-010 | Orphaned Services Disposition | Pending D-004 | P2 |
| ADR-011 | Frontend Testing Strategy | Pending | P3 |
| ADR-012 | Frontend API Client Pattern | Pending | P3 |
| ADR-013 | Multi-Country Expansion | Future | P4 |
| ADR-014 | Adaptive Learning Engine | Future | P4 |
| ADR-015 | Observability Stack | Future | P4 |
