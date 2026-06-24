# DOCUMENT_CLASSIFICATION_MATRIX

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Purpose: Classification of all 355 documents by type, authority level, and lifecycle status.
See DOCUMENT_INVENTORY.md for full per-document listing.

---

## CLASSIFICATION TIER MODEL

The documentation structure has five tiers. Higher tiers take precedence over lower tiers when documents conflict.

```
TIER 0 — GOVERNANCE AUTHORITY
  docs/00_authority/       (5 docs — platform identity, domain, features, workflows, contracts)
  docs/06_decisions/       (1 doc  — ADR architectural decisions)
  docs/07_governance/      (2 docs — AI operating context, escalation matrix)

TIER 1 — CANONICAL ANCHORS
  docs/anchors/            (5 docs — event envelope, tenant contract, capability resolution,
                                     country layer, doc precedence)

TIER 2 — SERVICE AND INTERFACE CONTRACTS
  docs/specs/              (58 docs — per-service API contracts)
  docs/specs/features/     (19 docs — per-feature contracts)
  docs/contracts/          (11 docs — interface contracts)
  docs/integrations/       (6 docs  — integration specs)
  docs/data/auth-service-storage-contract.md (1 doc — auth data contract)
  docs/architecture/api-versioning-strategy.md (1 doc — sole authority on versioning)

TIER 3 — SUPPORTING DESIGN AND ARCHITECTURE
  docs/architecture/       (18 supporting docs — design detail behind Tier 0/1 decisions)
  docs/designs/            (45 docs — service and feature design documents)
  docs/data/               (11 supporting docs — schemas and data models)
  docs/api/                (6 supporting docs — API surface documentation)
  docs/market/             (3 docs — market authority, no cross-tier conflict)

TIER 4 — REPORTS AND HISTORICAL
  docs/08_reports/         (6 docs  — governance reports)
  docs/architecture/       (6 report docs — point-in-time audit reports)
  docs/api/                (2 report docs)
  docs/data/               (2 report docs)
  docs/qc/                 (28 docs — QC validation reports)
  workspace/sessions/      (81 docs — session outputs)
  workspace/audit/         (7 docs  — audit files)

TIER 5 — RETIRED, OBSOLETE, WORKING DRAFTS
  docs/_archive/           (10 docs — retired)
  docs/governance/         (1 obsolete doc-catalogue + 5 historical archive)
  workspace/archive/       (8 docs  — retired/historical)
  docs/specs/*-v0.md       (3 docs  — retired v0 specs)
  docs/anchors/doc-precedence.md (1 obsolete — needs update)
  workspace/foundation/    (3 historical)
  workspace/design-system/ (3 drafts)
  workspace/page-definitions/ (3 drafts)
```

---

## CLASSIFICATION BY TYPE

### Authority Documents (AUTH) — 127 total

Documents that are the single authoritative source for their information domain. When an AUTH document conflicts with a non-AUTH document, the AUTH document wins.

**Governance Authority (8)**
- docs/00_authority/PROJECT_CHARTER.md
- docs/00_authority/DOMAIN_MODEL.md
- docs/00_authority/FEATURE_SCOPE.md
- docs/00_authority/PRODUCT_WORKFLOWS.md
- docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md
- docs/07_governance/AI_OPERATING_CONTEXT.md
- docs/07_governance/DECISION_ESCALATION_MATRIX.md
- docs/architecture/api-versioning-strategy.md

**Canonical Anchors (4)**
- docs/anchors/event-envelope.md
- docs/anchors/tenant-contract.md
- docs/anchors/capability-resolution.md *(PENDING UPDATE — config hierarchy)*
- docs/anchors/country-layer-architecture.md

**Service Specs (53)**
All docs/specs/*.md except auth-service-spec-v0.md (RETD), tenant-service-spec-v0.md (RETD), GEN_14_certificate_service.md (DUPL), monolith-to-services-migration.md (HIST), adapter-inventory.md (SUPP), capability-domain-map.md (SUPP), capability-inventory.md (SUPP), platform-behavioral-contract.md (SUPP), auth-service-test-plan.md (SUPP)

**Feature Specs (18)**
All docs/specs/features/*.md except rbac-service-spec-v0.md (RETD)

**Interface Contracts (11)**
All docs/contracts/*.md

**Integration Specs (5)**
docs/integrations/auth-lifecycle-events.md, hris-sync-spec.md, lti-consumer-spec.md, lti-provider-spec.md, webhook-system-spec.md

**Market Docs (3)**
docs/market/competitive-intelligence.md, gtm-entry-strategy.md, pakistan-market-pricing-guide.md

**Data Contract (1)**
docs/data/auth-service-storage-contract.md

---

### Working Draft (DRAFT) — 7 total

Documents that are in progress but not yet authoritative.

| Document | Domain | Blocker |
|---|---|---|
| docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md | Cross-layer traceability | Frontend column is TBD — no frontend analysis yet |
| workspace/design-system/design-system.md | Frontend design | Frontend Authority Capture not started |
| workspace/design-system/behavior-to-ui.md | Frontend design | Frontend Authority Capture not started |
| workspace/design-system/framework-gap-register.md | Frontend design | Frontend Authority Capture not started |
| workspace/page-definitions/entity-contracts.md | Frontend design | Frontend Authority Capture not started |
| workspace/page-definitions/page-inventory.md | Frontend design | Frontend Authority Capture not started |
| workspace/page-definitions/ui-framework.md | Frontend design | Frontend Authority Capture not started |

---

### Supporting References (SUPP) — 85 total

Documents that provide implementation detail supporting an authority document. They do not establish policy; they elaborate it.

**Architecture Design (18)**
All docs/architecture/*.md except api-versioning-strategy.md (AUTH) and the 6 audit reports (RPT)

**Design Docs (45)**
All docs/designs/*.md

**API Docs (6)**
docs/api/analytics-api.md, api-gateway-design.md, auth-service-api.md, content-api.md, core-rest-api.md, integration-api.md

**Data Schemas (11)**
All docs/data/*.md except auth-service-storage-contract.md (AUTH) and the 2 validation reports (RPT)

**Integration Overview (1)**
docs/integrations/standards-support.md

**Spec Supporting (4)**
docs/specs/adapter-inventory.md, capability-domain-map.md, capability-inventory.md, platform-behavioral-contract.md, auth-service-test-plan.md

---

### Generated Reports (RPT) — 59 total

Point-in-time validation, QC, or analysis outputs. Not authoritative; represent state at time of generation.

**Governance Reports (6)**
All docs/08_reports/*.md

**Architecture Audit Reports (6)**
docs/architecture/architecture-full-audit-report.md, circular-dependencies-audit-report.md, duplicate-domains-detection-report.md, data-isolation-analysis-report.md, event-ownership-analysis-report.md, service-boundary-analysis-report.md

**API Validation Reports (2)**
docs/api/api-contract-validation-report.md, api-spec-validation-report.md

**Data Validation Reports (2)**
docs/data/database-schema-validation-report.md, data-model-validation-report.md

**QC Reports (27)**
All docs/qc/*.md (except _archive/B3P05 which is HIST)

**QC Archive (1)**
docs/qc/_archive/B3P05_payment_integration_qc_report.md (HIST, not RPT)

---

### Historical Records (HIST) — 84 total

Records of prior phase work. Retained for traceability. Not valid for current implementation decisions.

**Workspace Sessions (81)**
All workspace/sessions/**/*.md

**Prior Spec Documents (2)**
docs/specs/monolith-to-services-migration.md, workspace/archive/code-gap-register.md

**QC Archive (1)**
docs/qc/_archive/B3P05_payment_integration_qc_report.md

**Former Authority Docs (2)**
workspace/foundation/product-build-spec.md (superseded by PROJECT_CHARTER.md)
workspace/foundation/behavioral-spec.md (superseded by PRODUCT_WORKFLOWS.md and FEATURE_SCOPE.md)

**Foundation (1)**
workspace/foundation/market-research.md

**Governance Archive (5)**
docs/governance/_archive/backend-restructuring.md, docs-rename-map.md, noise-kill-tracker.md, normalisation-tracker.md, tracker.md

**Workspace Audit (7)**
All workspace/audit/*.md

**Workspace Archive (6)**
workspace/archive/doc-catalogue-v4.0.md retained as RETD; others are HIST:
workspace/archive/icon-system-v1.md, ms-overlay-register.md, normalisation-findings.md, pattern-checklist.md, stage3-read-tracker.md, ARCHIVE-README.md

---

### Operational Artifacts (OPS) — 4 total

Live operational tracking files.

| Document | Purpose |
|---|---|
| workspace/ops/snapshot.md | Session snapshot — current project state |
| workspace/ops/progress.md | Phase progress tracker |
| workspace/ops/pending.md | Pending work register |
| workspace/ops/gap-register.md | BOS overlay gap register |

**Note:** workspace/ops/ is STALE. The pending.md and gap-register.md reference MO-001–MO-044 BOS gaps and pre-governance blockers. The current active blocker register is docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md. Recommend: retire workspace/ops/ to HIST after reviewing for any unresolved items not captured in governance docs.

---

### Retired Documents (RETD) — 12 total

Documents that have been formally superseded. Must not be used for implementation decisions.

| Document | Superseded By |
|---|---|
| docs/_archive/audit_logging.md | docs/qc/ and docs/architecture/ |
| docs/_archive/cloud_architecture_lms.md | docs/architecture/cloud-architecture-ems-lms.md |
| docs/_archive/cohort_spec.md | docs/specs/cohort-service-spec.md |
| docs/_archive/config_service.md | docs/designs/config-service-design.md |
| docs/_archive/core_system_architecture.md | docs/architecture/core-system-architecture.md |
| docs/_archive/course_service_spec.md | docs/specs/course-service-spec.md |
| docs/_archive/event_driven_architecture.md | docs/architecture/event-driven-architecture.md |
| docs/_archive/feature_inventory.md | docs/00_authority/FEATURE_SCOPE.md |
| docs/_archive/microservice_boundaries.md | docs/architecture/microservice-boundary-map.md |
| docs/_archive/observability_design.md | docs/architecture/observability-architecture.md |
| docs/specs/auth-service-spec-v0.md | docs/specs/auth-service-spec.md |
| docs/specs/tenant-service-spec-v0.md | docs/specs/tenant-service-spec.md |
| docs/specs/features/rbac-service-spec-v0.md | docs/specs/rbac-service-spec.md |
| workspace/archive/ARCHIVE-README.md | N/A (administrative) |
| workspace/archive/doc-catalogue-v4.0.md | docs/governance/doc-catalogue.md v7.3 then DOCUMENTATION_COVERAGE_MATRIX.md |

---

### Duplicate Documents (DUPL) — 1 total

| Document | Duplicate Of | Action |
|---|---|---|
| docs/specs/GEN_14_certificate_service.md | docs/specs/certificate-service-spec.md | Retire to docs/_archive/ |

---

### Obsolete Documents (OBSOL) — 2 total

Documents where the naming convention or content model is from a prior phase and is no longer consistent with the current governance framework.

| Document | Issue | Action |
|---|---|---|
| docs/governance/doc-catalogue.md | v7.3 master catalogue using pre-governance authority model; no longer the single source of doc inventory truth | Reclassify as HIST; add deprecation notice pointing to DOCUMENT_INVENTORY.md and DOCUMENTATION_COVERAGE_MATRIX.md |
| docs/anchors/doc-precedence.md | Priority model (BATCH > SPEC > ARCH > Legacy) predates docs/00_authority/ tier; BATCH naming convention no longer used | Update to reflect new 5-tier authority model; owner review required |

---

## CLASSIFICATION SUMMARY

| Classification | Count | % of Total |
|---|---|---|
| AUTH — Authority Document | 127 | 36% |
| SUPP — Supporting Reference | 85 | 24% |
| HIST — Historical Record | 84 | 24% |
| RPT — Generated Report | 59 | 17% |
| DRAFT — Working Draft | 7 | 2% |
| RETD — Retired Document | 12 | 3% |
| OPS — Operational Artifact | 4 | 1% |
| DUPL — Duplicate Document | 1 | <1% |
| OBSOL — Obsolete Document | 2 | <1% |
| **TOTAL** | **355** | |
