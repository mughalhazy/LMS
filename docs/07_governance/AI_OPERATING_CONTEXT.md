# AI_OPERATING_CONTEXT

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-21
Owner: Shared

---

## Purpose

This document is loaded at the start of every AI session working on this project. It provides sufficient context to operate correctly without re-reading all source code.

Any AI session that cannot answer the questions in the SUCCESS CRITERIA section (Governance Phase 1) must re-read this document before proceeding.

---

## CURRENT_PHASE

**Phase:** Project Memory Layer complete (2026-06-24)
**Session history:** U0 through U11 + Phase 2 Backend Authority + Phase 2.9 OA Resolution + Phase 2.95 Decision Collapse + OWNER-REQUIRED Compression + Phase 3 Frontend Authority + Phase 3.25 Gap Elimination + Project Memory Layer
**Status:** All architectural questions resolved. All governance blockers cleared. All owner-required items compressed to 3 genuine credentials/anchors (OR-001, OR-002, OR-003). Frontend authority captured. Repository fully determined. 83-item Project Memory Layer established in docs/09_project_memory/.
**Next phases available:** Frontend Implementation Sprint, Backend Persistence Sprint (SQLite for 53 remaining services), Service API Inspection Sprint (FSC-005 through FSC-009 code inspection)

**IMPORTANT FOR FUTURE AI SESSIONS:** Load `docs/09_project_memory/FINAL_CLASSIFIED_REGISTER.md` before any audit, gap analysis, or implementation work. This register contains 83 classified items covering all resolved questions, safe defaults, open owner decisions, external dependencies, and deferred features. Loading it prevents re-deriving already-answered questions.

---

## FROZEN_DECISIONS

These decisions have been made and must not be reopened without explicit owner instruction:

| Decision | Value | Evidence |
|---|---|---|
| Frontend framework | Next.js 16 + React 19 + Tailwind v4 | Repo/frontend/package.json |
| Backend language | Python (FastAPI) + Node.js (2 services) | Repo/backend/services/ (67 Python/FastAPI + 2 Node.js = 69 HTTP total) |
| Auth standard | JWT RS256 | docs/designs/auth-rsa-key-design.md |
| Event envelope | 7-field canonical | docs/anchors/event-envelope.md |
| Tenant contract | 6-field canonical | docs/anchors/tenant-contract.md |
| Config resolution order | global→country→segment→tenant (4 levels; plan_type handled by entitlement service) | docs/anchors/capability-resolution.md (NOTE: anchor doc may need update) |
| Capability resolution sequence | capability→config→entitlement→final_state | docs/anchors/capability-resolution.md |
| Pakistan payment providers | JazzCash, EasyPaisa | integrations/payments/ (.pyc confirms production use) |
| No C: drive writes | All paths on D: | workspace/sessions/U8/WORKSPACE_SEALING_REPORT.md |
| Python command | `py -3` not `python` | python not on PATH; U9 H-003 |
| Two-layer architecture | services/ (domain) + backend/services/ (HTTP) | workspace/sessions/U10/ |
| Service count | 69 in manifest; 3 class-based services (capability-registry, config-service, entitlement-service) now have ASGI shims in backend/services/ and updated manifest entries (Phase 2.9) | service-manifest.json + Phase 2.9 |

---

## ACTIVE_AUTHORITY_DOCS

Read these before making any architectural decisions:

| Document | Location | What it governs |
|---|---|---|
| PROJECT_CHARTER | docs/00_authority/PROJECT_CHARTER.md | Platform identity, constraints, principles |
| DOMAIN_MODEL | docs/00_authority/DOMAIN_MODEL.md | Bounded contexts, aggregates, tenant model |
| FEATURE_SCOPE | docs/00_authority/FEATURE_SCOPE.md | What is in/out of scope |
| PRODUCT_WORKFLOWS | docs/00_authority/PRODUCT_WORKFLOWS.md | Primary user and system workflows |
| FULLSTACK_STITCHING_CONTRACT | docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md | Feature traceability |
| DECISION_ESCALATION_MATRIX | docs/07_governance/REVISED_DECISION_ESCALATION_MATRIX.md | What requires approval (includes SAFE_REPOSITORY_HYGIENE tier) |
| ADR-001 | docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md | All foundational technology decisions |
| Tenant Contract | docs/anchors/tenant-contract.md | Canonical tenant model |
| Capability Resolution | docs/anchors/capability-resolution.md | Resolution sequence |
| Event Envelope | docs/anchors/event-envelope.md | Event structure |
| Remediation Plan | workspace/sessions/U11/U11_LMS_REMEDIATION_PLAN.md | All open architectural fixes |
| Governance Blockers | workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md | What must be fixed first |

---

## PROTECTED_AREAS

These areas must not be modified without explicit owner approval:

| Area | Files | Reason |
|---|---|---|
| Canonical anchors | docs/anchors/*.md | Changes cascade to all consumers |
| Service manifest | Repo/service-manifest.json | Registry of all 72 deployed services |
| Shared models | Repo/shared/models/ | Cross-service data contracts |
| Event topics | Repo/event_topics.json | 39 topics; changes affect all consumers |
| Backend shared events | Repo/backend/services/shared/events/ | Reverse dependency from services/ domain layer |
| Payment adapters | Repo/integrations/payments/ | Production-confirmed code (.pyc); JazzCash/EasyPaisa live |
| Communication adapters | Repo/integrations/communication/ | Notification delivery infrastructure |
| Tenant isolation code | Any service middleware | Tenant isolation is a hard constraint |
| RS256 auth config | Any service JWT middleware | Security standard; HS256 services are tracked debts |

---

## DO_NOT_MODIFY

These specific patterns must never be changed without a named remediation task:

| Pattern | Reason |
|---|---|
| `tenant_id` field in any data model | Primary isolation key â€” immutable once set |
| 7-field event envelope structure | Canonical contract for all 39 event topics |
| `capability → config → entitlement → final_state` evaluation order | Breaking this breaks capability gating for all tenants |
| JazzCash/EasyPaisa adapter payment flow | Production-used; any change needs reconciliation strategy |
| CheckoutService idempotency_key logic | Duplicate payment prevention; removing breaks payment safety |
| `sys.path.append()` calls in services/_load_module() | Do not remove without implementing R-010 first |

---

## OPEN_ARCHITECTURAL_QUESTIONS

**Status: ALL 5 QUESTIONS RESOLVED OR DEFAULTED — 2026-06-23 (OWNER-REQUIRED ITEM COMPRESSION)**

| ID | Question | Resolution |
|---|---|---|
| D-001 | Does backend/checkout-service handle DB persistence for orders/sessions? | **SAFE-DEFAULT**: Keep InMemoryCheckoutStore for development. Add SQLiteCheckoutStore in persistence sprint (same BaseRepository pattern as 16 already-wired services). No owner decision required. |
| D-002 | What runtime interprets `service:ClassName` in service-manifest.json? | **AUTO-CLOSED (RESOLVED Phase 2.9)**: No loader found. Manifest updated — capability-registry, config-service, entitlement-service now point to backend/services/ with ASGI shims. Fully resolved. |
| D-003 | Which CI/CD platform? Docker? Deployment target? | **SAFE-DEFAULT**: Docker Compose (infrastructure/deployment/docker-compose.yml) confirmed for local/staging. GitHub Actions as CI default. Production cloud provider: deferred — owner chooses before production launch. Non-blocking. |
| D-004 | Keep or delete services/file-storage/ and services/interaction-service/? | **AUTO-CLOSED**: interaction-service does not exist (PDC-004). file-storage/ retained as domain library per MO-023 Phase B intent (PDC-003). |
| D-005 | Is services/commerce/reconciliation.py actively used? | **AUTO-CLOSED (RESOLVED Phase 2.95)**: Both reconciliation files confirmed active. services/commerce/reconciliation.py = domain algorithm. integrations/payments/reconciliation.py = JazzCash/EasyPaisa adapter. FGAP-005 tracks HTTP endpoint + admin screen sprint. |

---

## REQUIRED_VALIDATIONS

Run these before asserting any code change is correct:

```powershell
# Run all backend tests
cd D:\SaaS\LMS\Repo
py -3 -m pytest backend/services/ -q

# Run all services/ tests
py -3 -m pytest services/ -q

# Verify service manifest completeness
py -3 -c "import json; m=json.load(open('service-manifest.json')); print(f'Services: {len(m[\"services\"])}')"

# Verify event topics integrity
py -3 -c "import json; t=json.load(open('event_topics.json')); print(f'Topics: {len(t[\"topics\"])}'); bad=[x for x in t['topics'] if x.get('consumer_services') and not any(x['consumer_services'])]; print(f'Bad: {len(bad)}')"
```

**Test counts (as of 2026-06-21):** 105 total (78 backend/services/ + 27 services/)

---

## DOCUMENT_FRESHNESS_POLICY

| Document type | Max age before review required |
|---|---|
| Authority documents (00_authority/) | Review on any architectural change |
| Governance documents (07_governance/) | Review quarterly or on governance phase change |
| ADRs (06_decisions/) | Immutable once Active; create new ADR to supersede |
| Service specs (docs/specs/) | Review on any API change to the service |
| Architecture docs (docs/architecture/) | Review on any structural change |
| Reports (08_reports/) | Regenerate at each governance phase boundary |

---

## CONTRACT_COMPATIBILITY_POLICY

Before modifying any interface that is consumed by another service:

1. Check `docs/anchors/` â€” is this a canonical anchor? If yes, changes require owner approval.
2. Check `docs/contracts/` â€” is there an interface contract? If yes, update the contract before changing code.
3. Check `event_topics.json` â€” if changing an event producer, update all `consumer_services` entries.
4. Check `service-manifest.json` â€” if adding/removing a service, update the manifest.
5. Check `docs/specs/` â€” if changing an API route, update the spec first.
6. Run the full test suite after any interface change.

---

## KNOWN_RISKS

| Risk | Severity | Mitigation |
|---|---|---|
| entitlement-service crashes if backend/shared/events absent | HIGH | R-001 (implement dependency injection) |
| academy-ops crashes if backend/progress-service absent | HIGH | R-003 (implement ProgressRepository protocol) |
| Circular import: commerce â†” subscription-service | HIGH | R-004 (extract shared models) |
| CheckoutService loses data on restart | HIGH | R-005: SAFE-DEFAULT (Phase 3.25) — SQLite persistence sprint; BaseRepository pattern; no owner decision required |
| HS256 on 3 services is a security gap | HIGH | R-012 (RS256 migration sprint) |
| Docker Compose + deploy YAML exist in infrastructure/ but no active CI pipeline wired | HIGH | R-013: SAFE-DEFAULT (Phase 3.25) — Docker Compose + GitHub Actions confirmed default. Cloud provider: owner selects before production launch. Non-blocking. |
| Frontend has zero tests | HIGH | U9 test plan P7/P8 |
| 25 services without canonical specs | MEDIUM | R-008 (spec writing) |
| python not on PATH â€” use py -3 | LOW | All validation commands updated |

---

## QUICK REFERENCE: WHAT IS THIS PROJECT?

**Meridian LMS** is a multi-tenant SaaS LMS for Pakistan education operators (tuition centers, academies, schools). It handles the full learning lifecycle: enrollment, content delivery, assessment, certification, fee collection (JazzCash/EasyPaisa), attendance tracking, and AI tutoring. It is Pakistan-first with architecture designed for global expansion.

**Who are the users?**
- Education operators (admin) â€” manage branches, batches, teachers, fees
- Teachers â€” manage classes, upload content, mark attendance
- Students/learners â€” consume content, take assessments, pay fees
- Parents — monitor student progress (FGAP-001: confirmed gap — parent-service not in manifest; parent role undefined; parent portal sprint required)

**What is frozen?** Next.js 16, FastAPI Python, RS256 JWT, JazzCash payments, 7-field event envelope, 6-field tenant contract, config resolution hierarchy.

**What requires approval?** See DECISION_ESCALATION_MATRIX.md.


