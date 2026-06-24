# ARCHITECTURAL_GAP_REGISTER

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

---

## Purpose

Records all discovered architectural gaps. These are gaps between documented intent and verified reality, or areas where reality is unknown.

Source: U6 findings, U10 forensic audit, U11 remediation plan, Governance Phase 1 audit.

---

## Critical Gaps (Must Fix Before Governance)

### AG-001: Reverse Dependency — entitlement-service → backend/shared/events

**Type:** Architecture violation
**Impact:** entitlement-service cannot be run without backend/ on path; cascades to commerce and academy-ops
**Evidence:** services/entitlement-service/service.py line ~12: `from backend.services.shared.events.envelope import EventEnvelope, build_event`
**Remediation:** R-001 (dependency injection)
**Governance blocker:** GEB-001

---

### AG-002: Reverse Dependency — system-of-record → backend/progress-service

**Type:** Architecture violation
**Impact:** academy-ops crashes if progress-service absent; entire academy operations domain is coupled to backend/
**Evidence:** services/system-of-record/service.py lines 39-55: `_load_progress_module()` loads `backend/services/progress-service/src/`
**Remediation:** R-003 (ProgressRepository Protocol)
**Governance blocker:** GEB-001

---

### AG-003: Circular Import — commerce ↔ subscription-service

**Type:** Circular dependency
**Impact:** Latent initialization crash; any import added to billing.py or models.py referencing service.py will break
**Evidence:** commerce/service.py loads subscription-service via importlib; subscription-service.py imports `from services.commerce.billing import BillingService` and `from services.commerce.models import SubscriptionPlan`
**Remediation:** R-004 (model extraction to shared/)
**Governance blocker:** GEB-002

---

### AG-004: CheckoutService Has No Persistent Storage

**Type:** Production-readiness gap
**Impact:** All checkout sessions, orders, transactions, and idempotency records lost on process restart; JazzCash duplicate charge risk
**Evidence:** services/commerce/checkout.py: `self._sessions: dict`, `self._orders: dict`, `self._idempotency_index: dict`
**Remediation:** R-005 (repository protocol injection; owner decision D-001)
**Governance blocker:** GEB-003

---

### AG-005: Three Services Use HS256 (Security Debt)

**Type:** Security gap
**Impact:** HS256 allows any party with the shared secret to forge tokens; platform security standard is RS256
**Evidence:** U6 B05-002 (notification), U6 B10-006 (subscription), U7 new finding (catalog)
**Affected:** notification-service, subscription-service, catalog-service
**Remediation:** R-012 (RS256 migration)
**Governance blocker:** GEB-004

---

### AG-006: No CI/CD Pipeline or Dockerfiles

**Type:** Infrastructure gap
**Impact:** Tests cannot be automatically enforced; governance cannot be enforced without automated pipeline
**Evidence:** Zero Dockerfiles, zero .github/workflows/ or equivalent found in Repo (U10 confirmed)
**Remediation:** R-013 (owner decision D-003)
**Governance blocker:** GEB-007

---

### AG-007: 25 Backend Services Have No Canonical Specs

**Type:** Documentation gap
**Impact:** Contract tests impossible; API governance framework cannot cover unspecced services
**Evidence:** U6 high finding; 25 services identified; see DOCUMENTATION_COVERAGE_MATRIX.md
**Remediation:** R-008 (25 spec files)
**Governance blocker:** GEB-005

---

### AG-008: Class-Based Service Startup Undocumented

**Type:** Operational gap
**Impact:** Three deployed services (capability-registry, config-service, entitlement-service) have no documented startup mechanism
**Evidence:** service-manifest.json `service:ClassName` pattern; no startup scripts in Repo; no documentation
**Remediation:** R-009 (owner decision D-002)
**Governance blocker:** GEB-006

---

## High Gaps (Fix During Governance)

### AG-009: Reverse Dependency — commerce → backend/shared/events (best-effort)

**Type:** Architecture violation (degraded)
**Impact:** Revenue anomaly detection events silently dropped if backend/ absent
**Evidence:** services/commerce/service.py: `try: from backend.services.shared.events.envelope import publish_event except ImportError: publish_event = None`
**Remediation:** R-002 (dependency injection, same pattern as R-001)

---

### AG-010: Runtime sys.path Mutation Accumulates

**Type:** Runtime risk
**Impact:** sys.path grows unbounded during services/ initialization (14+ appends); potential module resolution conflicts
**Evidence:** Every `_load_module()` call in services/: `sys.path.append(str(module_path.parent))` without deduplication; config-service loaded under 3 different names by different callers
**Remediation:** R-010 (two-line guard)

---

### AG-011: Frontend Has Zero Tests

**Type:** Test coverage gap
**Impact:** Frontend regressions cannot be detected automatically; no E2E validation of critical user journeys
**Evidence:** U9 confirmed — no Vitest config, no Playwright config, no test scripts in package.json
**Remediation:** U9 test plan P7 (Vitest) + P8 (Playwright)

---

### AG-012: doc-catalogue.md Contains Stale D:\LMS Path

**Type:** Documentation accuracy
**Impact:** Stale workspace path in the master documentation index
**Evidence:** docs/governance/doc-catalogue.md header: `Location: D:\LMS\Repo\doc-catalogue.md` and `Git: D:\LMS master`
**Remediation:** R-015 (trivial fix — update two fields)
**Governance blocker:** GEB-008

---

## Medium Gaps

### AG-013: 10 DUPLICATED services/ Entries — Relationship Undocumented

**Type:** Documentation gap
**Impact:** Ambiguity about which layer is authoritative for each duplicated service
**Services:** analytics-service, exam-engine, integration-service, media-pipeline, media-security, notification-service, offline-sync, onboarding, subscription-service, workflow-engine
**Remediation:** R-007 (document domain/HTTP relationship)

---

### AG-014: 2 ORPHANED services/ Entries

**Type:** Dead code risk
**Services:** file-storage (1 py, 0 tests), interaction-service (1 py, 0 tests)
**Remediation:** R-006 (owner decision D-004)

---

### AG-015: Duplicate Reconciliation Implementations

**Type:** Duplication risk
**Files:** services/commerce/reconciliation.py AND integrations/payments/reconciliation.py
**Impact:** Risk of divergence if both updated independently
**Remediation:** R-011 (owner decision D-005)

---

### AG-016: Duplicate Lesson Completion Event Topics

**Type:** Event topology confusion
**Topics:** lms.lesson.completed.v1 AND lms.progress.lesson_completed.v1 (both exist)
**Impact:** Consumers may listen to one but not the other; completion tracking may be incomplete
**Source:** U7 OI-001 (unresolved)
**Remediation:** Owner design decision required

---

### AG-017: Communication Adapter Duplication

**Type:** Architecture ambiguity
**Evidence:** backend/integrations/ AND integrations/ both contain communication adapter code
**Source:** U7 OI-002 (unresolved)
**Remediation:** Owner import audit required

---

### AG-018: Fullstack Stitching Contract — Frontend Column TBD

**Type:** Documentation gap
**Impact:** Cannot trace feature from frontend to backend without this
**Evidence:** Frontend not analyzed in U0-U11; frontend has zero tests
**Remediation:** Phase 2 governance — frontend audit required

---

## Missing Architecture

| Component | Gap |
|---|---|
| Deployment architecture | No Dockerfiles, no Kubernetes/ECS configs, no deployment docs |
| CI/CD pipeline | Completely absent from repository |
| Monitoring and alerting | Observability architecture documented but no confirmed implementation |
| Redis usage | LTI nonce Redis (U9 H-010) and DLQ persistence (U9 H-006) — not confirmed in code |
| Database scheme | Progress, course, lesson, enrollment migrations confirmed; other service DBs TBD |
| Load balancing | TBD – REQUIRES VERIFICATION |

---

## Missing Workflows

| Workflow | Gap |
|---|---|
| JazzCash webhook receipt and reconciliation trigger | Not confirmed in code path (WF-005 step 8) |
| Parent monitoring workflow | Referenced in product vision; no implementation found |
| Compliance reporting workflow | docs/specs/features/compliance-reporting-spec.md exists; no confirmed backend service |
| Adaptive learning trigger workflow | Design doc exists; no confirmed implementation |

---

## Missing Domain Entities

| Entity | Status |
|---|---|
| NotificationTemplate | TBD – REQUIRES VERIFICATION |
| WorkflowDefinition | docs/designs/workflow-engine.md; no confirmed entity in code |
| ParentGuardian profile | Conceptual; no confirmed service |
| AttendanceSession | Referenced in shared/models/timetable.py; confirmed |
| TeacherBatchEconomics | Confirmed in shared/models/teacher_economics.py |

---

## Missing Permissions Documentation

| Service | Permission Gap |
|---|---|
| academy-commerce-service | No RBAC mapping confirmed |
| checkout-service | Permission model TBD |
| payment-service | Permission model TBD |
| 23 unspecced services | No permission model documented |

---

## Missing Testing Coverage

| Area | Gap |
|---|---|
| Frontend | Zero tests (confirmed U9) |
| services/ importlib composition chain | Not tested end-to-end |
| Reverse dependencies | None tested (TCGAP-001) |
| Pakistan commerce E2E | Not confirmed tested |
| HS256 → RS256 migration | No RS256 validation tests exist |
| Load testing | Planned but not implemented |
| Security testing | Planned but not implemented |

---

## Conflicting Documentation

| ID | Conflict | Source |
|---|---|---|
| CR-001 | U6 classified services/ as "NOT HTTP services" ↔ manifest registers 3 as deployed services | U10 confirmed X-03 error |
| CR-002 | U5 claimed "0 broken references" ↔ doc-catalogue.md stale D:\LMS header | U0-U9 audit |
| CR-003 | OI-001: two lesson completion event topics exist — which is canonical? | U7 open item |
| CR-004 | communication adapter duplication: backend/integrations/ vs integrations/ | U7 OI-002 |

---

## Unverified Assumptions

| Assumption | Risk if Wrong |
|---|---|
| backend/checkout-service handles DB persistence (D-001) | CheckoutService in-memory = production gap |
| CI/CD exists outside repository (D-003) | May need to build from scratch |
| class-based services are started by an external runner | May be started inline; unknown behavior |
| Adaptive learning engine is not yet implemented | May be partially implemented and untested |
| Parent/guardian portal exists in frontend | May not exist at all |
