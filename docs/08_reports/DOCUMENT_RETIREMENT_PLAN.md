# DOCUMENT_RETIREMENT_PLAN

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Purpose: For every document identified as Retired, Obsolete, or Duplicate, provide a rationale and recommended action. No documents are deleted — retirement is handled via status changes and cross-references. Valuable information is preserved.

---

## RETIREMENT PRINCIPLES

1. No deletion — all retirement is via status classification and deprecation banners
2. A retired document must carry a deprecation banner naming its replacement
3. A retired document moves to docs/_archive/ or workspace/archive/ only if it currently lives in an active directory
4. Historical records (HIST) need no banner — their session folder context implies non-authority
5. Duplicate documents must be retired to prevent competing authority claims

---

## TIER 1 — IMMEDIATE RETIREMENT (AI Can Execute)

These documents can be retired by AI in the current session without owner approval.

### R-001: Retire GEN_14_certificate_service.md

**File:** docs/specs/GEN_14_certificate_service.md
**Classification:** DUPL
**Superseded by:** docs/specs/certificate-service-spec.md
**Action:** Add deprecation banner to GEN_14_certificate_service.md; move file to docs/_archive/GEN_14_certificate_service.md
**Rationale:** Legacy naming artifact (GEN_14 prefix from prior BATCH convention). Identical content covered by certificate-service-spec.md. Causes DUPL-C-001 conflict — consumers may implement against the wrong file.

**Deprecation banner to add before moving:**
```
> DEPRECATED — Superseded by: docs/specs/certificate-service-spec.md
> Reason: Legacy GEN_14 naming artifact. certificate-service-spec.md is the canonical spec.
> Last reviewed: 2026-06-22
```

---

### R-002: Add Deprecation Banners to v0 Spec Files

**Files:**
- docs/specs/auth-service-spec-v0.md
- docs/specs/tenant-service-spec-v0.md
- docs/specs/features/rbac-service-spec-v0.md

**Classification:** RETD (already classified; banners missing)
**Action:** Add deprecation banner to each file. Do not move (the -v0 naming convention is the primary signal; the banner reinforces it).

**Banner template:**
```
> DEPRECATED — Superseded by: [canonical spec path]
> Reason: v0 was replaced by v1 canonical spec during normalisation.
> Last reviewed: 2026-06-22
```

- auth-service-spec-v0.md → Superseded by: docs/specs/auth-service-spec.md
- tenant-service-spec-v0.md → Superseded by: docs/specs/tenant-service-spec.md
- rbac-service-spec-v0.md → Superseded by: docs/specs/rbac-service-spec.md

---

### R-003: Deprecation Notice on doc-catalogue.md

**File:** docs/governance/doc-catalogue.md
**Classification:** OBSOL
**Action:** Add deprecation notice at top of file. Do not move (it may be linked from other docs). Note what supersedes it.

**Deprecation notice to add:**
```
> SUPERSEDED — This catalogue (v7.3, dated 2026-06-02) uses a pre-governance authority model.
> For document inventory: see docs/08_reports/DOCUMENT_INVENTORY.md
> For service coverage: see docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md
> For authority mapping: see docs/08_reports/AUTHORITY_MAPPING_MATRIX.md
> This file is retained as a Historical Record of the pre-governance documentation state.
> Last reviewed: 2026-06-22
```

---

### R-004: Deprecation Banner on workspace/foundation/product-build-spec.md

**File:** workspace/foundation/product-build-spec.md
**Classification:** HIST (superseded former authority)
**Action:** Add deprecation banner at top.

**Banner:**
```
> SUPERSEDED — Former "Master Spec" authority.
> Replaced by: docs/00_authority/PROJECT_CHARTER.md (project identity and principles)
> Any reference to "Master Spec §N.N" should now resolve to docs/00_authority/PROJECT_CHARTER.md
> This file is retained as a Historical Record of the pre-governance specification state.
> Last reviewed: 2026-06-22
```

---

### R-005: Deprecation Banner on workspace/foundation/behavioral-spec.md

**File:** workspace/foundation/behavioral-spec.md
**Classification:** HIST (superseded former authority)
**Action:** Add deprecation banner at top.

**Banner:**
```
> SUPERSEDED — Former behavioral authority.
> Replaced by: docs/00_authority/PRODUCT_WORKFLOWS.md (workflow authority)
>              docs/00_authority/FEATURE_SCOPE.md (feature scope authority)
> This file is retained as a Historical Record of the pre-governance behavioral specification state.
> Last reviewed: 2026-06-22
```

---

### R-006: Cross-Reference Updates on DDD Map and Boundary Map

**Files:**
- docs/architecture/domain-driven-design-map.md
- docs/architecture/microservice-boundary-map.md

**Classification:** SUPP (not retired; needs supersession note)
**Action:** Add note at top of each file that docs/00_authority/DOMAIN_MODEL.md is the authority for bounded contexts and service assignments. These files remain as supporting detail.

**Note template:**
```
> NOTE: docs/00_authority/DOMAIN_MODEL.md is the authoritative bounded context and service-domain assignment document.
> This document provides supporting design detail. When this document conflicts with DOMAIN_MODEL.md, DOMAIN_MODEL.md takes precedence.
> Last reviewed: 2026-06-22
```

---

### R-007: Cross-Reference Update on service-map.md

**File:** docs/architecture/service-map.md
**Classification:** SUPP (service names may be stale)
**Action:** Add note that DOCUMENTATION_COVERAGE_MATRIX.md is the canonical service inventory. service-map.md provides architectural context only.

---

### R-008: Verify and Cross-Reference on Data Ownership Docs

**Files:**
- docs/designs/data-ownership-rules.md
- docs/architecture/service-data-ownership-rules.md

**Action:**
1. Read both files and compare content
2. Determine if they are redundant or complementary
3. If redundant: retire the older one (add deprecation banner; move to _archive/)
4. If complementary: add cross-references between both and to DOMAIN_MODEL.md §4 as the authority

---

## TIER 2 — OWNER APPROVAL REQUIRED (Anchor Updates)

### R-009: Update docs/anchors/capability-resolution.md

**File:** docs/anchors/capability-resolution.md
**Issue:** Config hierarchy states 6 levels (global → country → segment → plan → tenant → runtime_override). Correct is 4 levels per code.
**Action (requires owner):** Remove PLAN and runtime_override from config hierarchy section. Add note: "plan_type is evaluated by the entitlement service for allow/deny decisions — it is not a config resolution layer. runtime_override is not implemented."
**Blocker:** This is a protected anchor. Cannot modify without explicit owner approval.

---

### R-010: Update docs/anchors/doc-precedence.md

**File:** docs/anchors/doc-precedence.md
**Issue:** BATCH > SPEC > ARCH > Legacy model is obsolete. BATCH naming convention no longer exists. docs/00_authority/ tier is not represented.
**Action (requires owner):** Replace priority model with TIER 0–5 model per AUTHORITY_MAPPING_MATRIX.md.

**New model to adopt:**
```
TIER 0 — docs/00_authority/ + docs/06_decisions/ + docs/07_governance/ (highest)
TIER 1 — docs/anchors/ (canonical contracts)
TIER 2 — docs/specs/ + docs/contracts/ + docs/integrations/ (service and interface contracts)
TIER 3 — docs/architecture/ + docs/designs/ + docs/data/ (supporting design)
TIER 4 — docs/qc/ + docs/08_reports/ (generated reports — not authoritative for decisions)
TIER 5 — workspace/sessions/ + _archive/ (historical — never authoritative)
```

**Blocker:** This is a protected anchor. Cannot modify without explicit owner approval.

---

## TIER 3 — ASSESS AND DEFER (workspace/ops/)

### R-011: Review workspace/ops/ for Unresolved Items

**Files:**
- workspace/ops/pending.md (BOS gaps MO-001–MO-044)
- workspace/ops/gap-register.md (18 gaps)

**Action:**
1. Read both files
2. Identify any unresolved gaps not captured in docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md
3. Transfer any unresolved items to ARCHITECTURAL_GAP_REGISTER.md
4. After transfer: reclassify both files as HIST and add note: "Gaps transferred to docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md on 2026-06-22"

**Priority:** Medium — needed before workspace/ops/ confusion causes tracking errors.

---

### R-012: Review platform-behavioral-contract.md Authority Chain

**File:** docs/specs/platform-behavioral-contract.md
**Issue:** This was the repo-facing translation of the behavioral authority. If it still references workspace/foundation/behavioral-spec.md as its upstream, the authority chain is broken.
**Action:** Review the file. Update references to point to docs/00_authority/PRODUCT_WORKFLOWS.md and docs/00_authority/FEATURE_SCOPE.md as upstream authorities.

---

## TIER 4 — ALREADY RETIRED (Confirm Status)

These documents are already in archive directories. Confirm their status is correct.

| File | Status | Superseded By |
|---|---|---|
| docs/_archive/audit_logging.md | RETD | docs/qc/ and docs/architecture/ |
| docs/_archive/cloud_architecture_lms.md | RETD | docs/architecture/cloud-architecture-ems-lms.md |
| docs/_archive/cohort_spec.md | RETD | docs/specs/cohort-service-spec.md |
| docs/_archive/config_service.md | RETD | docs/designs/config-service-design.md |
| docs/_archive/core_system_architecture.md | RETD | docs/architecture/core-system-architecture.md |
| docs/_archive/course_service_spec.md | RETD | docs/specs/course-service-spec.md |
| docs/_archive/event_driven_architecture.md | RETD | docs/architecture/event-driven-architecture.md |
| docs/_archive/feature_inventory.md | RETD | docs/00_authority/FEATURE_SCOPE.md |
| docs/_archive/microservice_boundaries.md | RETD | docs/architecture/microservice-boundary-map.md |
| docs/_archive/observability_design.md | RETD | docs/architecture/observability-architecture.md |
| docs/governance/_archive/* (5 files) | HIST | No replacements needed; historical traceability |
| workspace/archive/doc-catalogue-v4.0.md | RETD | docs/governance/doc-catalogue.md v7.3 → DOCUMENTATION_COVERAGE_MATRIX.md |
| workspace/archive/ms-overlay-register.md | HIST | Closed 2026-04-11 — no further action |

**Status: Confirmed correct. No additional action needed.**

---

## RETIREMENT PLAN EXECUTION SEQUENCE

Execute in this order to avoid leaving documents in an inconsistent state:

| Step | Action | Ref | Risk |
|---|---|---|---|
| 1 | Add deprecation banner to GEN_14_certificate_service.md and move to docs/_archive/ | R-001 | Low |
| 2 | Add deprecation banners to 3 v0 spec files in place | R-002 | Low |
| 3 | Add deprecation notice to docs/governance/doc-catalogue.md | R-003 | Low |
| 4 | Add deprecation banner to workspace/foundation/product-build-spec.md | R-004 | Low |
| 5 | Add deprecation banner to workspace/foundation/behavioral-spec.md | R-005 | Low |
| 6 | Add supersession notes to DDD map and boundary map | R-006 | Low |
| 7 | Add canonical service inventory note to service-map.md | R-007 | Low |
| 8 | Verify and cross-reference data ownership docs | R-008 | Low |
| 9 | Review workspace/ops/ for unresolved gaps; transfer to ARCHITECTURAL_GAP_REGISTER.md | R-011 | Medium |
| 10 | Review platform-behavioral-contract.md authority chain | R-012 | Medium |
| 11 | Owner: update capability-resolution.md (4-level config) | R-009 | HIGH — protected anchor |
| 12 | Owner: update doc-precedence.md (TIER 0–5 model) | R-010 | HIGH — protected anchor |

---

## DOCUMENTS NOT RECOMMENDED FOR RETIREMENT

The following categories should NOT be retired despite being superseded in authority:

| Category | Reason to Retain |
|---|---|
| All docs/architecture/*.md (supporting) | Provide design detail not in governance docs; useful for implementation guidance |
| All docs/designs/*.md | Implementation detail for each service; no governance-level authority conflict |
| All docs/qc/*.md | Historical validation trail; useful for regression comparisons |
| All workspace/sessions/*.md | Complete audit trail of discovery decisions; U10/U11 are GEB authority source |
| All docs/data/*.md | Schema detail not replicated in governance docs |
| workspace/audit/*.md | Audit methodology records; useful for Phase 2 audit planning |
| workspace/design-system/*.md | Pre-phase drafts; needed as starting point for Frontend Authority Capture |
| workspace/page-definitions/*.md | Pre-phase drafts; needed as starting point for Frontend Authority Capture |

---

## INFORMATION PRESERVATION NOTES

No valuable information is lost through this retirement plan because:

1. All retired docs remain on disk in _archive/ directories
2. Deprecation banners point to the canonical replacement
3. Session outputs (HIST) retain the full audit trail
4. The only true deletion candidate is GEN_14_certificate_service.md (exact duplicate) — it is being moved to _archive/, not deleted
5. workspace/ops/ gap tracking is being transferred to ARCHITECTURAL_GAP_REGISTER.md before retirement
