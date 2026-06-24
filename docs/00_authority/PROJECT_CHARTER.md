# PROJECT_CHARTER

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-21
Owner: Human

---

## 1. Project Identity

**Platform Name:** Meridian LMS
**Canonical Identity:** Global Capability Platform (per Master Spec §0.1)
**Heritage Name:** Enterprise LMS V2 (refers to the Rails runtime layer in §1–§2 of core-system-architecture.md; retained for historical traceability only)

---

## 2. Purpose

Meridian LMS is a multi-tenant SaaS Learning Management System designed for the Pakistan education market, with architecture capable of global expansion.

The platform enables education operators — tuition centers, academies, coaching networks, private schools, universities — to run their complete learning operations digitally:

- Student enrollment and batch management
- Course content delivery (live, recorded, SCORM)
- Assessment and certification
- Fee collection and billing (JazzCash/EasyPaisa)
- Teacher management and economics
- Analytics and reporting
- AI-assisted learning and course generation

---

## 3. Primary Market

**Geography:** Pakistan-first
**Target segments (verified from docs/market/):**

| Segment | Scale | Payment model |
|---|---|---|
| Tuition centers & small academies | < 50 students | Per-student or transaction cut |
| Large academies & coaching networks | 1,000–50,000 students | Annual flat or per-student |
| Private schools (low-cost) | 100–500 students | Monthly or annual flat |
| Universities | 5,000+ students | Enterprise negotiated |

**Payment infrastructure (non-negotiable):** JazzCash, EasyPaisa
**Currency:** PKR
**Language:** Urdu i18n planned (MO-041 — deferred)

---

## 4. Core Architecture

**Two-layer Python architecture + HTTP presentation layer:**

```
services/           ← Domain layer (20 Python orchestrators; business logic)
backend/services/   ← HTTP presentation layer (69 FastAPI services)
integrations/       ← Adapter layer (JazzCash/EasyPaisa, WhatsApp/SMS/Email)
shared/             ← Common models (not a service)
frontend/           ← Next.js 16 + React 19 + Tailwind 4
```

**Runtime core (Rails heritage):** User, Course, Lesson, Enrollment, Progress, Certificate — authoritative entities anchoring the learning lifecycle.

**Manifest-registered class-based services:** capability-registry, config-service, entitlement-service (run via `service:ClassName` notation — non-HTTP deployed services).

**Evidence source:** workspace/sessions/U10/ — TWO-LAYER ARCHITECTURE FORENSIC (2026-06-21)

---

## 5. Technology Choices (Frozen)

| Component | Technology | Evidence |
|---|---|---|
| Frontend framework | Next.js 16 | Repo/frontend/package.json |
| Frontend UI | React 19 + Tailwind v4 | Repo/frontend/package.json |
| Backend language | Python (FastAPI) | Repo/backend/services/ |
| Domain layer | Python (plain classes + importlib) | Repo/services/ |
| Auth standard | JWT RS256 | docs/designs/auth-rsa-key-design.md |
| Auth exceptions | HS256 — notification, subscription, catalog | U7 remediation records |
| Payment — Pakistan | JazzCash / EasyPaisa | integrations/payments/ |
| Communication | WhatsApp / SMS / Email | integrations/communication/ |
| Event envelope | 7-field canonical (docs/anchors/event-envelope.md) | Confirmed U7 |
| Config resolution | global→country→segment→tenant (4 levels) | services/config-service/service.py ConfigLevel enum |
| Node.js services | prerequisite-engine-service, scorm-service | service-manifest.json |

---

## 6. Current Project Phase

**Phase:** Governance Entry (Phase 1 documentation complete; implementation pending → see GEB-001 through GEB-008 in docs/07_governance/AI_OPERATING_CONTEXT.md)
**Session history:** U0–U11 complete (workspace/sessions/)
**Active governance blockers:** 8 (see workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md)

**What is complete:**
- Repository reality discovery (U0)
- Authority reconstruction (U1)
- Documentation catalogue (U2)
- Documentation normalization (U3)
- Workspace restructuring (U4–U5)
- Doc-to-code delta analysis (U6)
- Delta remediation (U7)
- Workspace sealing (U8)
- Test suite planning (U9)
- Two-layer architecture forensic (U10)
- Remediation plan (U11)

**What is NOT yet complete:**
- Reverse dependency fixes (R-001, R-003)
- Circular import resolution (R-004)
- HS256 → RS256 migration (R-012)
- CI/CD pipeline (R-013)
- 25 unspecced services (R-008)
- Class-based service startup documentation (R-009)

---

## 7. Known Constraints

| Constraint | Source |
|---|---|
| No C: drive writes — all paths on D: | U8 workspace sealing |
| `python` not on PATH — use `py -3` | Confirmed U0-U9 forensic audit |
| Dockerfiles/CI-CD exist in infrastructure/ — do not add new ones without owner approval | Phase 2.9 confirmed 2026-06-23 |
| services/ cannot be used without backend/ on path (reverse deps) | U10 R-001, R-003 |
| CheckoutService has no persistence — in-memory only | U10 CF-007 |
| JazzCash/EasyPaisa integration: Pakistan only | services/commerce/service.py |
| Frontend has zero tests | U9 confirmed |

---

## 8. Protected Areas

The following areas must not be modified without explicit owner approval:

- `docs/anchors/` — canonical anchors; changes require re-validation of all consumers
- `service-manifest.json` — registry of all 72 deployed services
- `shared/models/` — cross-service data contracts; changes cascade to all consumers
- `backend/services/shared/` — event envelope; reverse dependencies from services/ layer
- `integrations/payments/` — active payment adapters (JazzCash/EasyPaisa in production use evidence: .pyc)
- Multi-tenant isolation code in any service — tenant_id propagation must be preserved

---

## 9. Architectural Principles

*Canonical list. ADR-001_PROJECT_FOUNDATION.md §Architectural Principles contains the same list — both documents must remain in sync.*

Source: docs/anchors/, docs/architecture/, and U10 forensic findings

1. **Tenant-first isolation** — tenant_id is the primary isolation key; no cross-tenant data access
2. **Config resolution hierarchy** — global → country → segment → tenant (4 levels; plan_type is evaluated by entitlement service, not config); no runtime branching on country/segment codes (MS-CONFIG-01)
3. **Capability resolution sequence** — capability → config → entitlement → final_state (docs/anchors/capability-resolution.md)
4. **Single system of record** — one service owns each entity; no dual writes
5. **Event-driven decoupling** — domain events use the 7-field canonical envelope; no direct service-to-service synchronous coupling for async workflows
6. **RS256 JWT standard** — all new services must use RS256; HS256 exceptions are tracked debts (see ADR-001_PROJECT_FOUNDATION.md Decision 5 for full exception service list)
7. **Pakistan-first commerce** — JazzCash is the default payment provider; only PK supported at domain layer currently
8. **Domain/HTTP separation** — services/ provides domain logic; backend/services/ provides HTTP; services/ must not import backend/

---

## 10. Business Objectives

1. Acquire tuition centers and small academies first (lowest friction segment)
2. Expand to large coaching networks (higher revenue, higher implementation cost)
3. Reach private schools and eventually universities
4. Pakistan-first → MENA/South Asia expansion eventually
5. AI features (tutoring, course generation, analytics) as differentiators
