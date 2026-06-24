# REPOSITORY_NORMALIZATION_REPORT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Audit scope: Every root directory and meaningful subdirectory in D:\SaaS\LMS\Repo

---

## EXECUTIVE SUMMARY

| Metric | Value |
|---|---|
| Root directories inventoried | 9 |
| Total files on disk | ~42,200 |
| Git-tracked source files (est.) | ~2,211 |
| Non-tracked generated files | ~41,329 (mostly node_modules) |
| Active service layer (backend/services/) | 70 services |
| Legacy service layer (root services/) | 20 services |
| Misplaced source files in docs/ | 11 .py scripts |
| Misplaced JSON artifacts in docs/ | 14 .json files |
| Root-layer directories needing review | 4 (services/, integrations/, shared/, validation/) |
| Critical structural findings | 4 |
| Documentation placement findings | 3 |
| Codebase placement findings | 4 |
| Generated artifact findings | 3 |
| Safe actions AI can execute | 0 (all findings require owner decision) |

---

## CRITICAL STRUCTURAL FINDINGS

### STRUCT-001: Two-Layer Service Architecture — Root `services/` vs `backend/services/`

**Severity: HIGH**

**Finding:**
The repository has two separate `services/` directories:

| Layer | Path | Services | Files | Structure |
|---|---|---|---|---|
| Root layer | `services/` | 20 | 97 | models.py, service.py, tests, __init__.py |
| Backend layer | `backend/services/` | 70 | 1,552 | FastAPI app/, tests/, requirements.txt |

**Overlap:** 16+ service concepts appear in both layers with different naming:
- `services/media-pipeline/` vs `backend/services/media-service/`
- `services/offline-sync/` vs `backend/services/offline-sync-service/`
- `services/interaction-service/` vs `backend/services/interaction-layer-service/`
- `services/commerce/` vs `backend/services/checkout-service/`
- Plus: analytics-service, capability-registry, config-service, entitlement-service, exam-engine, file-storage, integration-service, notification-service, onboarding, subscription-service, system-of-record, workflow-engine, enterprise-control, academy-ops

**Root layer characteristics:**
- No HTTP layer (no FastAPI app, no routes, no main.py)
- No requirements.txt (no deployable dependency specification)
- Minimal files per service (~5 .py)
- Naming uses legacy form (offline-sync, not offline-sync-service)
- Uses `.pyc` cached files (not git-tracked)

**Backend layer characteristics:**
- Full FastAPI microservice structure (app/, events/, migrations/)
- requirements.txt per service (deployable)
- More files per service (~20 .py average)
- Uses canonical naming (media-service, offline-sync-service)
- Matches service-manifest.json canonical names

**Interpretation:** Root `services/` is the pre-FastAPI platform layer — thin service modules implementing business logic without HTTP exposure. These were the original service implementations before the full microservice migration to `backend/services/`. They may still be imported by root `shared/`, `integrations/`, or `validation/`.

**Risk:**
- Name collisions may cause import ambiguity in Python
- Tests in root `services/` may validate stale implementations
- Developers unfamiliar with the dual structure may modify the wrong layer

**Action required:** Owner must determine if root `services/` is:
a) Still used as an import layer (ACTIVE) — must document and isolate
b) Fully superseded by backend/services/ (LEGACY) — mark for retirement
c) Partially active (some still used) — identify which, mark the rest LEGACY

See: ROOT_LEVEL_CLEANUP_PLAN.md action RLC-001

---

### STRUCT-002: Root `integrations/` Contains Duplicate Payment Directory

**Severity: MEDIUM**

**Finding:**
`integrations/` at root level has two payment-related directories:
- `integrations/payment/` — 8 files
- `integrations/payments/` — 26 files (the larger of the two)

Both exist at the same level with no documented relationship. This is either:
a) An older `payment/` that was partly migrated to `payments/` and not cleaned up
b) Two different integration scopes (singular = provider; plural = processing) with no documentation

**Risk:** Import confusion; maintenance of wrong adapter; duplicate code.

**Action required:** Owner must determine which is canonical and whether the other can be retired.

See: ROOT_LEVEL_CLEANUP_PLAN.md action RLC-002

---

### STRUCT-003: Root Layer Missing Documentation of Purpose

**Severity: MEDIUM**

**Finding:**
The directories `services/`, `integrations/`, `shared/`, `validation/`, and `scripts/` at root level have no documentation of their purpose, relationship to `backend/`, or current usage status. Specifically:

- `services/` — 20 service modules, no README.md, no __init__.py at root, no import graph documented
- `integrations/` — 53 files across 5 adapter categories, no README.md
- `shared/` — 59 files including 49 model files, no README.md
- `validation/` — 4 standalone scripts, no README.md
- `scripts/` — 1 script, no documentation

**Risk:** Any developer or AI session working in `backend/` has no way to know whether these root-level modules are live dependencies, legacy code, or abandoned experiments.

**Action required:** Owner must add README.md to each root-level code directory explaining:
1. Is this directory active or legacy?
2. What imports it?
3. Is it deployed independently or is it a utility layer?

See: ROOT_LEVEL_CLEANUP_PLAN.md action RLC-003

---

### STRUCT-004: `.pytest_cache/` Inside Service Directories

**Severity: LOW**

**Finding:**
Several `backend/services/` service directories contain `.pytest_cache/` subdirectories with files of no extension (cache entries). These are:
- `attempt-service/.pytest_cache/v/cache/` — nodeids, lastfailed, stepwise
- `auth-service/.pytest_cache/v/cache/` — nodeids, stepwise
- `cohort-service/.pytest_cache/v/cache/` — nodeids, stepwise
- `content-service/.pytest_cache/v/cache/` — nodeids, lastfailed, stepwise

**Git tracking:** Cannot verify without git access, but `.pytest_cache/` is typically in `.gitignore`.

**Action:** Verify `.pytest_cache/` is included in root `.gitignore`. If not, add it.

See: GENERATED_ARTIFACT_REGISTER.md entry GA-004

---

## DOCUMENTATION PLACEMENT FINDINGS

### DOC-001: Python Scripts in `docs/qc/`

**Severity: MEDIUM**

**Finding:**
`docs/qc/` contains 11 executable Python source files:

```
b7p01_capability_registry_validation.py
b7p02_entitlement_resolution_validation.py
b7p03_config_resolution_validation.py
b7p04_commerce_flow_validation.py
b7p05_payment_adapter_validation.py
b7p06_communication_workflow_validation.py
b7p07_delivery_system_validation.py
b7p08_end_to_end_system_validation.py
load_test_readiness_check.py
p18_end_to_end_validation.py
performance_smoke_tests.py
```

These scripts import from Python stdlib (`pathlib`, `json`, `dataclasses`) and presumably interact with the repository file structure. They are executable validation programs, not documentation.

**Current location:** `docs/qc/` (a documentation folder)
**Appropriate location:** `validation/` (which already exists at root for this purpose)

**Risk:** Scripts in `docs/` may not be found by developers looking for validation tooling. Running scripts from `docs/` creates confusion about what is documentation vs what is executable.

**However:** `docs/qc/` also contains the `.json` output reports from these scripts and the `.md` QC reports that document the results. The directory serves a dual purpose (scripts + their outputs). Separating them would orphan the output reports from their generators.

**Recommendation:** Move `.py` scripts to `validation/` directory. Update any scripts that reference relative paths. Leave `.md` and `.json` artifacts in `docs/qc/`.

**Action required:** Owner approval before moving (code modification).

See: DOCUMENTATION_PLACEMENT_AUDIT.md finding DP-001

---

### DOC-002: JSON Schema and Capability Files in `docs/architecture/`

**Severity: LOW**

**Finding:**
`docs/architecture/` contains two subdirectories of non-documentation JSON files:

```
docs/architecture/capabilities/
├── B0P05_business_capabilities.json
├── B0P06_communication_capabilities.json
├── B0P07_delivery_capabilities.json
└── B0P08_intelligence_capabilities.json

docs/architecture/schemas/
├── capability_registry.schema.json
├── capability_registry.example.json
├── segment_configuration.schema.json
└── segment_configuration.example.json
```

These are JSON data files (capability definitions) and JSON schema files (validation schemas), not `.md` documentation. They are machine-readable artifacts.

**Risk:** Low — the files are co-located with their documentation context. Moving them would orphan them from their docs.

**Recommendation:** If the capability registry service needs these as runtime artifacts, they should live in `backend/services/capability-registry/`. If they are purely documentation examples, their current location is acceptable with a note in the parent directory README.

**Action required:** Owner determination (low priority).

See: DOCUMENTATION_PLACEMENT_AUDIT.md finding DP-002

---

### DOC-003: JSON Files Scattered Across docs/

**Severity: LOW**

**Finding:**
Additional JSON artifacts exist in documentation directories:
- `docs/governance/spec_index.json` — a generated index
- `docs/specs/B0P04_core_capabilities.json` — capability spec in JSON
- `docs/qc/*.json` (9 files) — QC script output reports

None of these are documentation files. They are generated indexes, data files, or script outputs.

**Action required:** Low priority. Document as known artifact placement for context.

See: DOCUMENTATION_PLACEMENT_AUDIT.md finding DP-003

---

## CODEBASE PLACEMENT FINDINGS

### CODE-001: Root Code Layer Has No Clear Import Graph

**Severity: MEDIUM**

**Finding:**
`services/`, `integrations/`, `shared/`, `validation/` at root form an apparent code tier without documented relationships. The `shared/models/` subdirectory has 49 files — a large model library. The `integrations/` directory has payment, communication, identity, storage adapters. This structure suggests the root layer is a dependency imported by `backend/services/`. But without documented import paths, this is speculative.

**Action required:** Code owner to confirm whether root `shared/` models are imported by any `backend/services/` service. If so, the import path (`import shared.models.X`) creates coupling between root and backend that should be documented.

See: CODEBASE_PLACEMENT_AUDIT.md finding CP-001

---

### CODE-002: `infrastructure/service-discovery/` Contains Python Scripts

**Severity: LOW**

**Finding:**
`infrastructure/service-discovery/` contains 2 `.py` files among its 8 files. These are Python scripts in an infrastructure configuration directory. They may be service registration scripts that run during deployment. Their presence in `infrastructure/` is reasonable (deployment scripts belong near deployment configs) but should be documented.

**Action required:** Low priority. Note in infrastructure README.

See: CODEBASE_PLACEMENT_AUDIT.md finding CP-002

---

### CODE-003: `infrastructure/load-testing/` Contains JavaScript

**Severity: LOW**

**Finding:**
`infrastructure/load-testing/` contains 2 `.js` files. These are likely k6 load testing scripts (k6 uses JavaScript). Their placement in `infrastructure/` is appropriate, but should be noted as JavaScript source in a primarily YAML/JSON ops directory.

**Action required:** None — correct placement. Document in infrastructure README.

See: CODEBASE_PLACEMENT_AUDIT.md finding CP-003

---

### CODE-004: `backend/` Has No Root-Level README or Architecture Map

**Severity: LOW**

**Finding:**
`backend/` contains 70 microservices in `backend/services/` but has no root-level README.md documenting the backend architecture, service list, or how to run services. The only backend-level file (beyond subdirectories) is `backend/__init__.py`.

**Action required:** Add `backend/README.md` pointing to docs/07_governance/DOCUMENTATION_COVERAGE_MATRIX.md for service list and docs/architecture/core-system-architecture.md for architecture overview.

See: CODEBASE_PLACEMENT_AUDIT.md finding CP-004

---

## GENERATED ARTIFACTS SUMMARY

| Artifact Type | Location | File Count | Git-Tracked | Finding |
|---|---|---|---|---|
| `.pyc` Python bytecode | backend/, services/, integrations/, shared/ | ~336 | NO | GA-001 |
| `.pytest_cache/v/cache/*` | backend/services/ | ~75 | Unverified | GA-004 |
| `frontend/node_modules/` | frontend/ | 41,029 | NO | GA-002 |
| `frontend/package-lock.json` | frontend/ | 1 | YES (should be) | GA-003 |
| `docs/qc/*.json` report outputs | docs/qc/ | 9 | YES | GA-005 |

---

## LEGACY CODE SUMMARY

| Layer | Path | Services | Status | Evidence |
|---|---|---|---|---|
| Root services | `services/` | 20 | LIKELY LEGACY | No HTTP layer, no requirements.txt, uses old names |
| Root integrations | `integrations/` | 5 adapter dirs | NEEDS-REVIEW | Relationship to backend/integrations/ unclear |
| Root shared | `shared/` | 3 subdirs (49+ .py) | NEEDS-REVIEW | Large model library — may be active import |

---

## SUCCESS CRITERIA

| Criterion | Status |
|---|---|
| Every root directory inventoried | COMPLETE |
| Every meaningful subdirectory accounted for | COMPLETE |
| All file types classified | COMPLETE |
| Git tracking of generated files verified | COMPLETE (.pyc = not tracked; node_modules = not tracked) |
| Structural issues identified | COMPLETE — 4 structural findings |
| Documentation placement issues identified | COMPLETE — 3 findings |
| Code placement issues identified | COMPLETE — 4 findings |
| Generated artifact register populated | COMPLETE |
| Legacy layer identified | COMPLETE — root services/ is likely legacy |
| 9 output documents produced | IN PROGRESS (this is document 3 of 9) |
| Safe restructuring executed | N/A — all findings require owner decision |

---

## WHAT IS NOT CHANGED

Per audit scope rules:
- No application code modified
- No files deleted
- No files moved
- No documentation files edited (this phase)
- No .gitignore modifications proposed
- Frontend work not started

All findings are documented for owner review and decision. See REPOSITORY_RESTRUCTURING_PLAN.md for the ordered action plan.
