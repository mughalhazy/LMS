# REPOSITORY_CLASSIFICATION_MATRIX

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Companion: REPOSITORY_TREE_INVENTORY.md (file counts), REPOSITORY_NORMALIZATION_REPORT.md (findings summary)

---

## CLASSIFICATION CODES

| Code | Label | Description |
|---|---|---|
| ACTIVE-SRC | Active Source Code | Production code that is current, deployed, or intended for deployment |
| LEGACY-SRC | Legacy Source Code | Code superseded by or duplicated in another location |
| INFRA-CFG | Infrastructure Config | Deployment, observability, gateway, and secrets configuration |
| FRONTEND-SRC | Frontend Source | Next.js / React source code |
| FRONTEND-DEP | Frontend Dependency | node_modules — not source, not tracked |
| GENERATED | Generated Artifact | Files produced by tools (.pyc, .map, .json outputs) — not authored |
| MISPLACED | Misplaced File | Source code in a non-code directory, or vice versa |
| AUTH-DOC | Authority Document | Tier 0–2 governance/specification document |
| SUPP-DOC | Supporting Document | Tier 3 design, architecture, or data schema document |
| RPT-DOC | Report Document | Tier 4 generated report or audit output |
| HIST-DOC | Historical Document | Tier 5 session record or archive |
| NEEDS-REVIEW | Needs Review | Classification is ambiguous; requires owner decision |

---

## DIRECTORY CLASSIFICATION TABLE

### Root Level

| Path | Classification | Notes |
|---|---|---|
| `.gitattributes` | INFRA-CFG | Git repository configuration |
| `.gitignore` | INFRA-CFG | Exclusion rules |
| `.gitkeep` | INFRA-CFG | Empty-dir placeholder |

---

### backend/ (Primary code layer)

| Path | Classification | Notes |
|---|---|---|
| `backend/__init__.py` | ACTIVE-SRC | Python package initializer |
| `backend/services/<service>/app/` | ACTIVE-SRC | FastAPI service code — 70 services |
| `backend/services/<service>/tests/` | ACTIVE-SRC | pytest test suites |
| `backend/services/<service>/README.md` | SUPP-DOC | Per-service documentation |
| `backend/services/<service>/requirements.txt` | ACTIVE-SRC | Service dependency specification |
| `backend/services/<service>/events/` | ACTIVE-SRC | Event schema definitions |
| `backend/services/<service>/migrations/` | ACTIVE-SRC | Database migration files |
| `backend/services/<service>/.pytest_cache/` | GENERATED | Test runner cache — should be gitignored |
| `backend/services/shared/` | ACTIVE-SRC | Backend-internal shared utilities |
| `backend/integrations/` | ACTIVE-SRC | Backend integration adapters (20 files) |
| `backend/shared/` | ACTIVE-SRC | Backend-level shared module (3 files) |
| `backend/__pycache__/` | GENERATED | Compiled Python — NOT git-tracked |

**backend/ .pyc files (282):** GENERATED — NOT git-tracked per .gitignore

---

### docs/ (Documentation)

#### docs/00_authority/ — TIER 0 (highest authority)

| File | Classification | Notes |
|---|---|---|
| `PROJECT_CHARTER.md` | AUTH-DOC | Project identity, principles, scope |
| `DOMAIN_MODEL.md` | AUTH-DOC | Bounded contexts, service assignments |
| `FEATURE_SCOPE.md` | AUTH-DOC | Feature inventory |
| `PRODUCT_WORKFLOWS.md` | AUTH-DOC | Core workflow authority |
| `FULLSTACK_STITCHING_CONTRACT.md` | AUTH-DOC | Full-stack traceability (draft) |
| `AI_OPERATING_CONTEXT.md` | AUTH-DOC | AI session governance |
| `DECISION_ESCALATION_MATRIX.md` | AUTH-DOC | Decision routing authority |
| `ARCHITECTURAL_GAP_REGISTER.md` | AUTH-DOC | Active gap register |

#### docs/01_backend/ through docs/05_deployment/ — Empty placeholders

| Path | Classification | Notes |
|---|---|---|
| `docs/01_backend/` | AUTH-DOC (empty) | Reserved for backend authority docs |
| `docs/02_frontend/` | AUTH-DOC (empty) | Reserved for frontend docs (Phase 2) |
| `docs/03_ops/` | AUTH-DOC (empty) | Reserved for ops docs |
| `docs/04_testing/` | AUTH-DOC (empty) | Reserved for test strategy |
| `docs/05_deployment/` | AUTH-DOC (empty) | Reserved for deployment docs |

#### docs/06_decisions/ — TIER 0

| File | Classification | Notes |
|---|---|---|
| `ADR-001_PROJECT_FOUNDATION.md` | AUTH-DOC | 8 architectural decisions |

#### docs/07_governance/ — TIER 0

| Files | Classification | Notes |
|---|---|---|
| `DOCUMENTATION_COVERAGE_MATRIX.md` | AUTH-DOC | Canonical service inventory (69 services) |
| Other governance docs | AUTH-DOC | AI operating constraints and rules |

#### docs/08_reports/ — TIER 4

| File | Classification | Notes |
|---|---|---|
| `REMEDIATION_REPORT.md` | RPT-DOC | Phase 1 governance audit remediation |
| `DOCUMENT_INVENTORY.md` | RPT-DOC | 355-document inventory |
| `DOCUMENT_CLASSIFICATION_MATRIX.md` | RPT-DOC | Document type breakdown |
| `AUTHORITY_MAPPING_MATRIX.md` | RPT-DOC | Domain-to-authority mapping |
| `DOCUMENT_NORMALIZATION_REPORT.md` | RPT-DOC | Normalization phase findings |
| `DUPLICATION_ANALYSIS_REPORT.md` | RPT-DOC | 17 duplication findings |
| `CONFLICT_ANALYSIS_REPORT.md` | RPT-DOC | 21 conflict findings |
| `DOCUMENT_RETIREMENT_PLAN.md` | RPT-DOC | 12 retirement actions |
| `NORMALIZATION_REMEDIATION_REPORT.md` | RPT-DOC | Normalization remediation results |
| `REPOSITORY_TREE_INVENTORY.md` | RPT-DOC | This audit — tree inventory |
| `REPOSITORY_CLASSIFICATION_MATRIX.md` | RPT-DOC | This audit — classification (this file) |
| `REPOSITORY_NORMALIZATION_REPORT.md` | RPT-DOC | This audit — summary |
| `ROOT_LEVEL_CLEANUP_PLAN.md` | RPT-DOC | This audit — cleanup plan |
| `DOCUMENTATION_PLACEMENT_AUDIT.md` | RPT-DOC | This audit — doc placement |
| `CODEBASE_PLACEMENT_AUDIT.md` | RPT-DOC | This audit — code placement |
| `GENERATED_ARTIFACT_REGISTER.md` | RPT-DOC | This audit — generated artifacts |
| `LEGACY_AND_ARCHIVE_PLAN.md` | RPT-DOC | This audit — legacy plan |
| `REPOSITORY_RESTRUCTURING_PLAN.md` | RPT-DOC | This audit — restructuring plan |

#### docs/_archive/ — TIER 5

All files: HIST-DOC — Retired documents retained for audit trail.

#### docs/anchors/ — TIER 1

| Files | Classification | Notes |
|---|---|---|
| `tenant-contract.md` | AUTH-DOC | Tenant payload canonical definition |
| `event-envelope.md` | AUTH-DOC | Event envelope canonical contract |
| `country-layer-architecture.md` | AUTH-DOC | Country layer canonical model |
| `capability-resolution.md` | AUTH-DOC (STALE) | Config hierarchy — 6-level wrong; awaiting owner update |
| `doc-precedence.md` | AUTH-DOC (OBSOL) | Document precedence — BATCH model obsolete; awaiting owner update |

#### docs/architecture/ — TIER 3

| Item | Classification | Notes |
|---|---|---|
| 24 `.md` architecture documents | SUPP-DOC | Supporting design detail |
| `capabilities/B0P05_business_capabilities.json` | MISPLACED | JSON capability data in docs/ |
| `capabilities/B0P06_communication_capabilities.json` | MISPLACED | JSON capability data in docs/ |
| `capabilities/B0P07_delivery_capabilities.json` | MISPLACED | JSON capability data in docs/ |
| `capabilities/B0P08_intelligence_capabilities.json` | MISPLACED | JSON capability data in docs/ |
| `schemas/capability_registry.schema.json` | MISPLACED | JSON schema in docs/ |
| `schemas/capability_registry.example.json` | MISPLACED | JSON example in docs/ |
| `schemas/segment_configuration.schema.json` | MISPLACED | JSON schema in docs/ |
| `schemas/segment_configuration.example.json` | MISPLACED | JSON example in docs/ |

#### docs/contracts/, docs/integrations/, docs/specs/ — TIER 2

| Item | Classification | Notes |
|---|---|---|
| 11 `.md` interface contracts | AUTH-DOC | Service-boundary contracts |
| 5 `.md` integration specs | AUTH-DOC | Third-party integration contracts |
| 53+ `.md` service specs | AUTH-DOC | Per-service API specifications |
| `specs/B0P04_core_capabilities.json` | MISPLACED | JSON in specs directory |

#### docs/data/, docs/designs/ — TIER 3

| Item | Classification | Notes |
|---|---|---|
| 13 `.md` data schema docs | SUPP-DOC | Storage contract and schema docs |
| 45 `.md` design docs | SUPP-DOC | Implementation design guidance |

#### docs/governance/ — TIER 2/OBSOL

| File | Classification | Notes |
|---|---|---|
| `doc-catalogue.md` | HIST-DOC (OBSOL) | Pre-governance master catalogue; superseded notice added |
| `spec_index.json` | MISPLACED | JSON index in governance folder |

#### docs/qc/ — TIER 4 + MISPLACED

| Item | Classification | Notes |
|---|---|---|
| 36 `.md` QC reports | RPT-DOC | Historical validation reports |
| 11 `.py` validation scripts | **MISPLACED** | Executable source code in docs/ folder |
| 9 `.json` output reports | GENERATED | Script output artifacts in docs/ folder |

---

### frontend/ (Frontend application)

| Path | Classification | Notes |
|---|---|---|
| `frontend/app/` | FRONTEND-SRC | Next.js app router pages (9 files) |
| `frontend/components/` | FRONTEND-SRC | React components (45 files) |
| `frontend/lib/` | FRONTEND-SRC | Shared utilities (1 file) |
| `frontend/public/` | FRONTEND-SRC | Static assets (6 files) |
| `frontend/AGENTS.md` | AUTH-DOC | AI agent context — frontend scope |
| `frontend/CLAUDE.md` | AUTH-DOC | Claude Code context — frontend scope |
| `frontend/.env.local` | NEEDS-REVIEW | Environment file — should be gitignored |
| `frontend/node_modules/` | FRONTEND-DEP | 41,029 files — NOT git-tracked |
| `frontend/package.json` | ACTIVE-SRC | Dependency manifest |
| `frontend/package-lock.json` | GENERATED | Lockfile — generated by npm |
| `frontend/*.config.*` | ACTIVE-SRC | Build and tool configuration |

---

### infrastructure/ (Operational configuration)

| Path | Classification | Notes |
|---|---|---|
| `infrastructure/api-gateway/` | INFRA-CFG | API gateway YAML configs |
| `infrastructure/deployment/` | INFRA-CFG | Deployment manifests + .env files |
| `infrastructure/event-bus/` | INFRA-CFG | Event bus schema and config |
| `infrastructure/load-testing/` | INFRA-CFG | Load test scripts (.js) |
| `infrastructure/observability/` | INFRA-CFG | Monitoring stack configs |
| `infrastructure/secrets-management/` | INFRA-CFG | Secret store configs |
| `infrastructure/service-discovery/` | INFRA-CFG | Service registry config + scripts |

---

### Root layer directories (services/, integrations/, shared/)

| Path | Classification | Notes |
|---|---|---|
| `services/` (20 dirs) | LEGACY-SRC | Thin service modules — superseded by backend/services/ |
| `services/<svc>/models.py` | LEGACY-SRC | Data models; equivalent in backend/services/<svc>/app/ |
| `services/<svc>/service.py` | LEGACY-SRC | Service class; superseded by FastAPI app layer |
| `services/<svc>/test_*.py` | LEGACY-SRC | Tests for legacy layer |
| `services/<svc>/*.pyc` | GENERATED | NOT git-tracked |
| `integrations/communication/` | NEEDS-REVIEW | May or may not overlap with backend/integrations/ |
| `integrations/identity/` | NEEDS-REVIEW | May or may not overlap |
| `integrations/payment/` | NEEDS-REVIEW | Partial overlap with integrations/payments/ |
| `integrations/payments/` | NEEDS-REVIEW | Overlaps with integrations/payment/ — dual directory issue |
| `integrations/storage/` | NEEDS-REVIEW | May or may not overlap |
| `integrations/<dir>/*.pyc` | GENERATED | NOT git-tracked |
| `shared/models/` | NEEDS-REVIEW | 49 files — may be consumed by root services/ |
| `shared/utils/` | NEEDS-REVIEW | 4 utility files |
| `shared/validation/` | NEEDS-REVIEW | 2 validation helpers |
| `shared/<dir>/*.pyc` | GENERATED | NOT git-tracked |

---

### Standalone root scripts

| Path | Classification | Notes |
|---|---|---|
| `validation/` (4 .py files) | NEEDS-REVIEW | Standalone validation — purpose and usage unclear |
| `scripts/` (1 .py file) | NEEDS-REVIEW | Single maintenance script — identity unclear |

---

## CLASSIFICATION SUMMARY

| Code | Count (directories) | Notes |
|---|---|---|
| ACTIVE-SRC | backend/ (70 services) | Primary production layer |
| LEGACY-SRC | services/ (20 dirs) | Platform-layer pre-backend modules |
| INFRA-CFG | infrastructure/ (7 dirs) | All operational |
| FRONTEND-SRC | frontend/ (4 dirs + root files) | Next.js application |
| FRONTEND-DEP | frontend/node_modules/ | Not tracked; local only |
| GENERATED | .pyc (336), .pytest_cache (~75), node_modules | Not tracked |
| MISPLACED | docs/qc/*.py (11), docs/**/*.json (14) | Source in docs; JSON in docs |
| AUTH-DOC | docs/00_authority/, anchors/, contracts/, specs/ | Governance and service contracts |
| SUPP-DOC | docs/architecture/, docs/designs/, docs/data/ | Supporting design detail |
| RPT-DOC | docs/08_reports/, docs/qc/*.md | Reports and audit outputs |
| HIST-DOC | docs/_archive/, workspace/sessions/ | Historical records |
| NEEDS-REVIEW | integrations/, shared/, validation/, scripts/ | Root layer — ownership unclear |
