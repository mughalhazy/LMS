# REPOSITORY_TREE_INVENTORY

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Method: PowerShell recursive file enumeration with explicit absolute paths

---

## ROOT INVENTORY

Repository root: `D:\SaaS\LMS\Repo`

### Root-Level Files (3)

| File | Purpose |
|---|---|
| `.gitattributes` | Git line-ending and diff settings |
| `.gitignore` | Exclusion rules for git tracking |
| `.gitkeep` | Placeholder to preserve empty directory in git |

### Root-Level Directories (9)

| Directory | File Count | Top Extensions | Classification |
|---|---|---|---|
| `backend/` | 1,577 | .py=749, .pyc=282, .md=132, .json=69 | PRIMARY CODE |
| `docs/` | 289 | .md=259, .json=19, .py=11 | DOCUMENTATION |
| `frontend/` | 41,104 | .js=18685, .ts=7646, .map=6699 | FRONTEND (incl. node_modules) |
| `infrastructure/` | 56 | .json=15, .yml=12, .yaml=8 | OPERATIONS |
| `integrations/` | 53 | .py=35, .pyc=18 | CODE (root layer) |
| `services/` | 97 | .py=83, .pyc=13, .json=1 | CODE (root layer — legacy tier) |
| `shared/` | 59 | .py=36, .pyc=23 | CODE (root layer) |
| `validation/` | 4 | .py=4 | CODE (standalone) |
| `scripts/` | 1 | .py=1 | CODE (maintenance) |

**Total repository files (all directories):** 42,200

---

## BACKEND/ TREE

`backend/` — Primary Python backend. Contains all active microservices.

```
backend/
├── __init__.py                         (makes backend a Python package)
├── services/                           1,552 files — active service layer
│   ├── academy-commerce-service/       app/, tests/
│   ├── ai-tutor-service/               app/, tests/
│   ├── analytics-service/              app/, tests/
│   ├── api-key-service/                app/, tests/
│   ├── assessment-service/             app/, events/, migrations/, src/, tests/
│   ├── attempt-service/                app/, tests/, .pytest_cache/
│   ├── audit-policy-service/           app/, tests/
│   ├── auth-service/                   app/, tests/, .pytest_cache/
│   ├── badge-service/                  app/, tests/
│   ├── capability-registry/            app/, tests/
│   ├── catalog-service/                app/, tests/
│   ├── certificate-service/            app/, tests/
│   ├── checkout-service/               app/, tests/
│   ├── cohort-service/                 app/, tests/, .pytest_cache/
│   ├── config-service/                 app/, tests/
│   ├── content-service/                app/, tests/, .pytest_cache/
│   ├── course-generation-service/      app/, tests/
│   ├── course-service/                 app/, tests/
│   ├── department-service/             app/, tests/
│   ├── email-service/                  app/, tests/
│   ├── enrollment-service/             app/, tests/
│   ├── enterprise-control-service/     app/, tests/
│   ├── entitlement-service/            app/, tests/
│   ├── event-ingestion-service/        app/, tests/
│   ├── exam-engine/                    app/, tests/
│   ├── feature-flag-service/           app/, tests/
│   ├── financial-ledger-service/       app/, tests/
│   ├── group-service/                  app/, tests/
│   ├── hr-helpdesk-service/            app/, tests/
│   ├── hris-sync-service/              app/, tests/
│   ├── institution-service/            app/, tests/
│   ├── integration-service/            app/, tests/
│   ├── interaction-layer-service/      app/, tests/
│   ├── invoice-billing-service/        app/, tests/
│   ├── learning-analytics-service/     app/, tests/
│   ├── learning-path-service/          app/, tests/
│   ├── lesson-service/                 app/, tests/
│   ├── lti-service/                    app/, tests/
│   ├── media-security-service/         app/, tests/
│   ├── media-service/                  app/, tests/
│   ├── notification-service/           app/, tests/
│   ├── offline-sync-service/           app/, tests/
│   ├── onboarding-service/             app/, tests/
│   ├── operations-os-service/          app/, tests/
│   ├── org-service/                    app/, tests/
│   ├── owner-economics-service/        app/, tests/
│   ├── payment-service/                app/, tests/
│   ├── prerequisite-engine-service/    app/, tests/
│   ├── program-service/                app/, tests/
│   ├── progress-service/               app/, tests/
│   ├── push-service/                   app/, tests/
│   ├── quiz-engine/                    app/, tests/
│   ├── rbac-service/                   app/, tests/
│   ├── recommendation-service/         app/, tests/
│   ├── reporting-service/              app/, tests/
│   ├── revenue-service/                app/, tests/
│   ├── review-service/                 app/, tests/
│   ├── scorm-service/                  app/, tests/
│   ├── session-service/                app/, tests/
│   ├── shared/                         (internal backend shared utilities)
│   ├── skill-analytics-service/        app/, tests/
│   ├── skill-inference-service/        app/, tests/
│   ├── sso-service/                    app/, tests/
│   ├── subscription-service/           app/, tests/
│   ├── system-economics-service/       app/, tests/
│   ├── tenant-service/                 app/, tests/
│   ├── usage-metering-service/         app/, tests/
│   ├── user-service/                   app/, tests/
│   ├── webhook-service/                app/, tests/
│   └── workflow-engine/                app/, tests/
├── integrations/                       20 files — integration adapters
├── shared/                             3 files — backend-level shared
└── __pycache__/                        1 file — compiled Python (NOT git-tracked)
```

**backend/services/ service count:** 69 named services + shared/ subdir + __pycache__/ *(corrected from 70 — 2026-06-23)*

Standard service structure per service:
```
<service-name>/
├── README.md
├── requirements.txt
├── app/               (FastAPI application code)
├── tests/             (pytest test suite)
└── [optional] events/, migrations/, src/, .pytest_cache/
```

---

## DOCS/ TREE

`docs/` — All project documentation. 289 files.

```
docs/
├── 00_authority/       8 governance authority documents (AUTH — TIER 0)
├── 01_backend/         8 Phase 2 authority documents (API_CONTRACT, BACKEND_ARCHITECTURE, DATABASE_SCHEMA, ERROR_CONTRACT, EVENT_AND_QUEUE_ARCHITECTURE, INTEGRATION_CATALOG, SERVICE_CATALOG, VALIDATION_RULES) *(was EMPTY — corrected 2026-06-23)*
├── 02_frontend/        EMPTY — placeholder for frontend docs (Phase 2)
├── 03_fullstack_contracts/  5 cross-cutting contract documents (AUTH_AND_TENANCY_CONTRACT, DATA_SHAPE_REGISTRY, ERROR_CONTRACT, FULLSTACK_STITCHING_CONTRACT, USER_ROLES_AND_PERMISSIONS) *(directory name corrected from 03_ops — 2026-06-23)*
├── 04_testing/         EMPTY — placeholder for testing docs
├── 05_deployment/      EMPTY — placeholder for deployment docs
├── 06_decisions/       1 ADR document (AUTH — TIER 0)
├── 07_governance/      AI governance docs (AUTH — TIER 0)
├── 08_reports/         Audit and normalization reports (RPT — TIER 4)
├── _archive/           10+ retired documents (RETD — TIER 5)
├── anchors/            Canonical contracts (AUTH — TIER 1)
├── architecture/       24 .md + capabilities/ (4 .json) + schemas/ (4 .json)
├── contracts/          11 interface contract .md files
├── data/               13 schema documentation .md files
├── designs/            45 service design .md files
├── governance/         doc-catalogue.md (OBSOL) + spec_index.json
├── integrations/       5 integration spec .md files
├── market/             Market and GTM docs
├── qc/                 36 .md reports + 11 .py scripts + 9 .json report outputs
└── specs/              53 service spec .md files + features/ subfolder
```

**docs/ anomalies:**
- `docs/qc/` contains 11 executable Python source files (misplacement finding — see DOCUMENTATION_PLACEMENT_AUDIT.md)
- `docs/qc/` contains 9 JSON generated output files (generated artifact — see GENERATED_ARTIFACT_REGISTER.md)
- `docs/architecture/capabilities/` contains 4 JSON capability definition files (non-documentation artifact)
- `docs/architecture/schemas/` contains 4 JSON schema files (non-documentation artifact)
- `docs/governance/spec_index.json` — JSON index artifact in docs
- `docs/specs/B0P04_core_capabilities.json` — JSON file in specs directory

---

## FRONTEND/ TREE

`frontend/` — Next.js frontend application. 41,104 total files.

```
frontend/
├── node_modules/       41,029 files — NOT git-tracked (gitignored, local-only)
├── app/                9 files — Next.js app directory
├── components/         45 files — React component library
├── lib/                1 file — Utility library
├── public/             6 files — Static assets
├── AGENTS.md           AI agent context for frontend work
├── CLAUDE.md           Claude Code context for frontend work
├── .env.local          Environment configuration (should be gitignored)
├── .gitignore          Frontend-specific gitignore
├── .npmrc              npm configuration
├── components.json     shadcn/ui component registry
├── eslint.config.mjs   ESLint configuration
├── next-env.d.ts       Next.js TypeScript declarations
├── next.config.ts      Next.js configuration
├── package-lock.json   Locked dependency tree
├── package.json        Project manifest and scripts
├── postcss.config.mjs  PostCSS configuration
├── README.md           Frontend README
└── tsconfig.json       TypeScript configuration
```

**frontend/ non-node_modules file count:** 75 files (61 source + 14 config/meta)

---

## INFRASTRUCTURE/ TREE

`infrastructure/` — Operational deployment and runtime configuration. 56 files.

```
infrastructure/
├── api-gateway/        5 files (.yaml=3, .md=2) — API gateway configuration
├── deployment/         10 files (.env=2, .yml=2) — Deployment manifests
├── event-bus/          9 files (.json=7, .md=1) — Event bus schemas and config
├── load-testing/       3 files (.js=2, .md=1) — Load test scripts
├── observability/      15 files (.yml=10, .json=3) — Prometheus, Grafana, etc.
├── secrets-management/ 6 files (.json=2, .yaml=2) — Secret store configuration
└── service-discovery/  8 files (.py=2, .yaml=2) — Service registry
```

---

## ROOT LAYER SERVICES TREE

`services/` — Root-level service layer (legacy platform tier). 97 files.

```
services/
├── academy-ops/           models.py, service.py, test files, __init__.py
├── analytics-service/     models.py, service.py, __init__.py
├── capability-registry/   models.py, service.py, test files, __init__.py
├── commerce/              models.py, service.py, test files, __init__.py
├── config-service/        models.py, service.py, __init__.py
├── enterprise-control/    models.py, service.py, __init__.py
├── entitlement-service/   models.py, service.py, test files, __init__.py
├── exam-engine/           models.py, service.py, test files, __init__.py
├── file-storage/          models.py, service.py, __init__.py
├── integration-service/   models.py, service.py, __init__.py
├── interaction-service/   models.py, service.py, __init__.py
├── media-pipeline/        models.py, service.py, __init__.py
├── media-security/        models.py, service.py, __init__.py
├── notification-service/  models.py, service.py, __init__.py
├── offline-sync/          models.py, service.py, __init__.py
├── onboarding/            models.py, service.py, __init__.py
├── operations-os/         models.py, service.py, __init__.py
├── subscription-service/  models.py, service.py, __init__.py
├── system-of-record/      models.py, service.py, __init__.py
└── workflow-engine/       models.py, service.py, __init__.py
```

**Characteristics:** 20 services, ~5 .py files each, no FastAPI app structure, no requirements.txt.
These are thin service-layer modules (models + service class + tests) without HTTP layer.
Naming diverges from `backend/services/` canonical names (e.g., `media-pipeline` vs `media-service`).

---

## ROOT LAYER SHARED TREE

`shared/` — Root-level shared library. 59 files.

```
shared/
├── __init__.py
├── models/             49 files — data model definitions
├── utils/              4 files — utility functions
├── validation/         2 files — validation helpers
└── __pycache__/        1 file — compiled Python (NOT git-tracked)
```

`integrations/` — Root-level integration adapters. 53 files.

```
integrations/
├── communication/      10 files — messaging adapters
├── identity/           2 files — identity provider adapters
├── payment/            8 files — payment gateway adapters
├── payments/           26 files — payment processing (note: both payment/ and payments/ exist)
├── storage/            5 files — storage provider adapters
└── __pycache__/        1 file — compiled Python (NOT git-tracked)
```

`validation/` — Standalone validation scripts. 4 .py files.

`scripts/` — Maintenance scripts. 1 .py file.

---

## GIT TRACKING VERIFICATION

| Artifact Type | Files on Disk | Git-Tracked | Status |
|---|---|---|---|
| `.pyc` compiled Python | ~336 total | **0** | Local-only — gitignored correctly |
| `.pytest_cache/v/cache/*` | ~75 (no-extension) | Not verified | Should be gitignored |
| `frontend/node_modules/` | 41,029 | **0** | Local-only — gitignored correctly |
| `.env.local` | 1 | Not verified | Should be gitignored |

**Finding:** `.pyc` files are NOT tracked in git despite being present on disk. `.gitignore` is working correctly for compiled Python files. `frontend/node_modules/` is also NOT tracked.

---

## TOTALS SUMMARY

| Category | Directories | Files |
|---|---|---|
| Backend code (backend/) | 75+ | 1,577 |
| Documentation (docs/) | 30+ | 289 |
| Frontend source (frontend/ excl. node_modules) | 5 | 75 |
| Frontend deps (frontend/node_modules/) | — | 41,029 |
| Infrastructure config (infrastructure/) | 7 | 56 |
| Root layer code (services/, integrations/, shared/) | 27 | 209 |
| Standalone scripts (validation/, scripts/) | — | 5 |
| **Tracked source total (excl. node_modules)** | — | **~2,211** |
| **Total on disk** | — | **~42,200** |
