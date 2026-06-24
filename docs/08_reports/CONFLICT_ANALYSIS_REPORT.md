# CONFLICT_ANALYSIS_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Purpose: Identify all conflicting authorities, terminology, architecture descriptions, workflow descriptions, module counts, entity definitions, ownership models, operational guidance, and governance rules across 355 documents.

---

## SEVERITY CLASSIFICATION

- **Critical** — Active conflict between two documents both in regular use; direct implementation risk
- **High** — Conflict in authoritative documents; one authoritative source is wrong or outdated
- **Medium** — Conflict in supporting documents; authority docs are correct; supporting docs lag
- **Low** — Cosmetic or terminology-level inconsistency; no implementation risk

---

## CRITICAL CONFLICTS

### CONF-C-001: Config Resolution Hierarchy — Anchor vs Code vs Governance Docs

**Status: PARTIALLY RESOLVED — Anchor pending owner update**

**Conflict:**
- docs/anchors/capability-resolution.md: `global → country → segment → plan → tenant → runtime_override (optional)` (6 levels)
- docs/00_authority/DOMAIN_MODEL.md: `global → country → segment → tenant (4 levels)` (CORRECT)
- docs/00_authority/PROJECT_CHARTER.md: `global → country → segment → tenant (4 levels)` (CORRECT)
- docs/06_decisions/ADR-001: `global → country → segment → tenant (4 levels)` (CORRECT)
- Code (shared/models/config.py ConfigLevel enum): GLOBAL, COUNTRY, SEGMENT, TENANT only (CORRECT)

**Root cause:** capability-resolution.md was written before the ConfigLevel enum was verified. It assumed PLAN and runtime_override existed. They do not. The anchor is a protected area and was not updated during remediation.

**Resolution:** Owner must update capability-resolution.md to:
1. Remove PLAN level from config hierarchy
2. Remove runtime_override (optional) from hierarchy
3. Note that plan_type is evaluated by the entitlement service, not the config service

**Authority ruling:** Code is ground truth. 4-level hierarchy is correct.

---

### CONF-C-002: Document Precedence Model — Anchor vs New Governance

**Status: UNRESOLVED — Anchor requires owner update**

**Conflict:**
- docs/anchors/doc-precedence.md: BATCH > SPEC > ARCH > Legacy
- docs/08_reports/AUTHORITY_MAPPING_MATRIX.md: TIER 0 (Governance Authority) > TIER 1 (Anchors) > TIER 2 (Specs/Contracts) > TIER 3 (Supporting) > TIER 4 (Reports) > TIER 5 (Historical)

**Root cause:** doc-precedence.md was written before docs/00_authority/ was established. The BATCH naming convention (B2*, B3*, B5*, B6*) no longer exists in the repository. The model is entirely obsolete.

**Risk:** Any AI session reading doc-precedence.md as an authority would conclude that SPEC docs (Priority 2) outrank what the precedence model calls "Legacy docs" — but docs/00_authority/ would fall into "Legacy/general" (Priority 4) under the old model, which is the exact opposite of correct.

**Resolution:** Owner must update docs/anchors/doc-precedence.md to reflect the new TIER 0–5 model. Until then, AUTHORITY_MAPPING_MATRIX.md TIER model is operative.

---

### CONF-C-003: Certificate Service — Two Active Spec Files

**Status: UNRESOLVED — Retirement required**

**Conflict:**
- docs/specs/certificate-service-spec.md (canonical)
- docs/specs/GEN_14_certificate_service.md (legacy duplicate — same service, active directory)

**Resolution:** See DUP-C-001. Retire GEN_14_certificate_service.md to docs/_archive/.

---

## HIGH CONFLICTS

### CONF-H-001: Architectural Principles — Ordering and Wording

**Status: RESOLVED (Phase 1 Remediation)**

Both docs/00_authority/PROJECT_CHARTER.md §9 and docs/06_decisions/ADR-001 now state the same 8 principles in the same order. Cross-reference notes added. Any future architecture documents must match this canonical list.

**Residual risk:** Documents in docs/architecture/ and docs/designs/ that predate remediation may contain their own principle statements that differ. These are SUPP documents; they do not compete for authority but may mislead.

---

### CONF-H-002: Service Names — Canonical vs Legacy Names in Supporting Docs

**Status: RESOLVED in governance docs; residual risk in supporting docs**

**Resolved in governance docs:**
- media-service (not media-pipeline)
- system-economics-service (not system-economics)
- interaction-layer-service (not interaction-layer)
- offline-sync-service (not offline-sync)

**Residual risk:** docs/architecture/service-map.md, docs/designs/*.md, and docs/qc/*.md may still use legacy names. These are SUPP/RPT (not authoritative) but could confuse developers.

**Authority:** infrastructure/deployment/service-manifest.json is the ground truth. DOCUMENTATION_COVERAGE_MATRIX.md now reflects canonical names.

**Resolution needed:** Scan docs/architecture/service-map.md and key design docs for legacy service names. Update or note supersession.

---

### CONF-H-003: "Master Spec" References in Architecture Documents

**Status: UNRESOLVED — Cross-reference updates needed**

**Conflict:**
- docs/architecture/core-system-architecture.md references "Master Spec §0.1 Heritage Statement" and "Master Spec §1.5"
- workspace/foundation/product-build-spec.md was the "Master Spec" — now superseded by docs/00_authority/PROJECT_CHARTER.md

**Risk:** Architecture documents that resolve conflicts by deferring to "Master Spec" are now deferring to a superseded document. Any new AI session reading core-system-architecture.md would follow the wrong authority chain.

**Resolution:** 
1. Add deprecation banner to workspace/foundation/product-build-spec.md
2. Update "Master Spec" cross-references in core-system-architecture.md to point to PROJECT_CHARTER.md
3. Grep docs/ for "Master Spec" occurrences and update all references

---

### CONF-H-004: "Global Capability Platform" vs Platform Identity in Older Docs

**Status: PARTIALLY RESOLVED**

**Conflict:**
- Older docs use "Enterprise LMS V2" or "Enterprise LMS" as the platform name
- docs/00_authority/PROJECT_CHARTER.md establishes "Global Capability Platform" as the canonical identity
- core-system-architecture.md has a normalisation note clarifying this (added in prior phase)

**Residual risk:** docs/designs/ and docs/qc/ documents may still refer to "Enterprise LMS" without the clarifying note.

**Resolution:** This was partially addressed in prior phases via the docs/designs/terminology-bridge.md document. No further action required for supporting docs — the terminology-bridge.md handles this.

---

### CONF-H-005: Ownership of Course Completion

**Status: RESOLVED (Phase 1 Remediation)**

Previously: PRODUCT_WORKFLOWS.md WF-004 said "enrollment-service or progress-service"
Resolved: progress-service owns `lms.progress.course_completed.v1` (verified from event_topics.json)

No further conflict.

---

### CONF-H-006: review-service and course-generation-service Domain Assignments

**Status: RESOLVED (Phase 1 Remediation)**

- review-service: correctly in Learning Runtime domain (DOMAIN_MODEL.md and FEATURE_SCOPE.md updated)
- course-generation-service: correctly in AI domain (FEATURE_SCOPE.md §1.10)

No further conflict.

---

### CONF-H-007: Service Count Ambiguity

**Status: RESOLVED (Phase 1 Remediation)**

Previously: AI_OPERATING_CONTEXT.md said "67 services" ambiguously
Resolved: Corrected to "67 Python/FastAPI + 2 Node.js = 69 HTTP total"

Residual risk: Older docs (qc/, architecture/) may reference different counts (60, 64, 65, etc.) as services were added over time. These are all RPT/SUPP and historical.

---

## MEDIUM CONFLICTS

### CONF-M-001: Workflow Complexity Codes (BC-INT-02 etc.)

**Status: RESOLVED (Phase 1 Remediation)**

BC-INT-02 was an opaque code in PRODUCT_WORKFLOWS.md WF-007. Replaced with descriptive text. No remaining BC-* codes without definitions in governance documents.

Residual: workspace/ops/pending.md and workspace/audit/ documents may still reference BC-* codes. These are OPS/HIST documents and not authoritative.

---

### CONF-M-002: "Runtime Orchestrator" as a Service

**Status: RESOLVED (Phase 1 Remediation)**

DOMAIN_MODEL.md previously implied "runtime orchestrator" was a service. Corrected to "Calling service / API handler" — clarifying it is a caller pattern, not a dedicated service.

Residual: docs/designs/ documents may still reference "runtime orchestrator" as a service concept. These are SUPP and the DOMAIN_MODEL.md is authoritative.

---

### CONF-M-003: "Platform Behavioral Contract" — Two Levels

**Documents:**
1. workspace/foundation/behavioral-spec.md (former behavioral authority — HIST)
2. docs/specs/platform-behavioral-contract.md (repo-facing behavioral contracts — SUPP)
3. docs/00_authority/PRODUCT_WORKFLOWS.md (current workflow authority — AUTH)

**Conflict:** behavioral-spec.md was the behavioral authority. It is now HIST. platform-behavioral-contract.md is a SUPP translation of that authority into named contracts. PRODUCT_WORKFLOWS.md is the new workflow authority.

**Risk:** platform-behavioral-contract.md may reference behavioral-spec.md for authority, which is now superseded.

**Resolution:** Review platform-behavioral-contract.md to ensure it references PRODUCT_WORKFLOWS.md (not behavioral-spec.md) as its upstream authority. Add cross-reference.

---

### CONF-M-004: Phase Status Description

**Status: RESOLVED (Phase 1 Remediation)**

PROJECT_CHARTER.md §6 now says "Governance Entry (Phase 1 documentation complete; implementation pending — see GEB-001 through GEB-008)". No conflict with ADR-001 or AI_OPERATING_CONTEXT.md.

---

### CONF-M-005: Authentication Token Standard Exceptions

**Documents:**
1. docs/06_decisions/ADR-001 Decision 5 (RS256 canonical; HS256 exceptions listed)
2. docs/00_authority/PROJECT_CHARTER.md §9 Principle 6 (RS256 stated; exceptions brief)
3. docs/architecture/security-architecture.md (may have different exception handling detail)

**Risk:** ADR-001 is more detailed (lists specific HS256 exception services). PROJECT_CHARTER.md is a summary. If they diverge, ADR-001 is authoritative for the decision detail.

**Resolution:** Add cross-reference note to PROJECT_CHARTER.md §9 Principle 6 pointing to ADR-001 Decision 5 for exception list detail. (Low priority — no current divergence.)

---

### CONF-M-006: Stale Service Names in QC Reports

**Documents:** docs/qc/*.md (27 reports)

**Issue:** QC reports were generated at various points in the project lifecycle. Some may reference:
- media-pipeline instead of media-service
- system-economics instead of system-economics-service
- 60, 64, or 65 services instead of 69

**Risk:** Low — QC reports are RPT (historical); no implementation decisions should reference them.

**Resolution:** No action needed for RPT documents. Document this as a known limitation of historical reports.

---

### CONF-M-007: workspace/ops/ vs docs/08_reports/ Gap Registers

**Documents:**
1. workspace/ops/gap-register.md (BOS gap register — OPS, likely stale)
2. workspace/ops/pending.md (pending items — OPS, likely stale)
3. docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md (current active register)

**Conflict:** workspace/ops/ registers track pre-governance gaps using older terminology (MO-001–MO-044, BOS overlay gaps). The current active gap register is docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md (GEB-001–008).

**Resolution:** Review workspace/ops/pending.md for any unresolved MO- items not captured in governance docs. If all MO- gaps are resolved or superseded, retire workspace/ops/pending.md and gap-register.md to HIST.

---

## LOW CONFLICTS

### CONF-L-001: Country Naming — Pakistan vs Global-First vs Pakistan-First

**Documents:** Various design docs use "Pakistan market" with varying emphasis. PROJECT_CHARTER.md is clear: "Pakistan-first positioning."

**Resolution:** Terminology is consistent in governance docs. Supporting docs may vary but this is cosmetic.

### CONF-L-002: "Segment" vs "Plan" Terminology

**Documents:** Older docs use "plan" as a config resolution discriminator. Post-remediation docs use "plan_type" correctly as an entitlement concept (not config).

**Resolution:** Governance docs are correct. Supporting docs may have legacy usage. docs/designs/terminology-bridge.md should note this distinction.

### CONF-L-003: Module Count References

**Documents:** workspace/sessions/U0/ and workspace/sessions/U1/ report different module/feature counts from different inspection passes. These are all HIST.

**Resolution:** No action. All HIST documents; FEATURE_SCOPE.md is the authority on feature inventory.

### CONF-L-004: "Academy" vs "Academy Commerce" Service Naming

**Documents:** Some docs reference "academy-service" while others reference "academy-commerce-service". Service manifest confirms "academy-commerce-service" as canonical.

**Resolution:** Correct in governance docs (post-remediation). Supporting docs may lag — acceptable for SUPP classification.

---

## CONFLICT SUMMARY

| ID | Severity | Domain | Status | Action |
|---|---|---|---|---|
| CONF-C-001 | Critical | Config resolution hierarchy | Partially resolved | Owner update capability-resolution.md |
| CONF-C-002 | Critical | Document precedence model | Unresolved | Owner update doc-precedence.md |
| CONF-C-003 | Critical | Certificate spec duplicate | Unresolved | AI — retire GEN_14 file |
| CONF-H-001 | High | Architectural principles | Resolved | Maintain sync |
| CONF-H-002 | High | Service names in supporting docs | Partially resolved | AI — scan + note in service-map.md |
| CONF-H-003 | High | "Master Spec" references | Unresolved | AI — deprecation banner + cross-ref updates |
| CONF-H-004 | High | Platform identity naming | Partially resolved | terminology-bridge.md handles it |
| CONF-H-005 | High | Course completion ownership | Resolved | — |
| CONF-H-006 | High | review + course-gen domain | Resolved | — |
| CONF-H-007 | High | Service count | Resolved | — |
| CONF-M-001 | Medium | BC-* opaque codes | Resolved | — |
| CONF-M-002 | Medium | Runtime orchestrator | Resolved | — |
| CONF-M-003 | Medium | Behavioral contract authority | Unresolved | Review platform-behavioral-contract.md |
| CONF-M-004 | Medium | Phase status | Resolved | — |
| CONF-M-005 | Medium | HS256 exception detail | Low risk | Add cross-reference (low priority) |
| CONF-M-006 | Medium | Stale service names in QC | Accepted | No action — historical reports |
| CONF-M-007 | Medium | Gap registers competing | Unresolved | Review workspace/ops/ for unresolved items |
| CONF-L-001 | Low | Country naming | Accepted | — |
| CONF-L-002 | Low | Segment vs plan terminology | Accepted | terminology-bridge.md |
| CONF-L-003 | Low | Module count references | Accepted | All HIST |
| CONF-L-004 | Low | Academy service naming | Accepted | Correct in governance docs |

---

## OPEN ITEMS REQUIRING OWNER ACTION

| Ref | Action | Reason |
|---|---|---|
| CONF-C-001 | Update docs/anchors/capability-resolution.md — correct to 4-level config hierarchy | Protected anchor; AI cannot modify without approval |
| CONF-C-002 | Update docs/anchors/doc-precedence.md — adopt TIER 0–5 model | Protected anchor; BATCH naming obsolete; new governance tier not represented |
