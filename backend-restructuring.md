# LMS Repo — Backend Restructuring Proposal
**Status:** PROPOSAL — awaiting approval before any execution
**Created:** 2026-05-17
**Source:** Two-round parallel agent audit (8 agents total)

---

## Current Top-Level Zones

```
D:\LMS\Repo\
├── backend/services/      43 FastAPI microservices (Python) + 1 shared/ folder
│   └── shared/            infra utils (db, events, context, models)
├── services/              19 platform domain services (pure Python, no FastAPI)
├── shared/                26 domain contract models + utils + validation + control_plane
├── integrations/          5 adapter groups (communication, identity, payment[DEPRECATED], payments[CANONICAL], storage)
├── docs/                  270+ docs across 8 subfolders
├── frontend/              Next.js 16.2 / React 19 / Tailwind 4
├── infrastructure/        7 infra config folders (deployment, observability, api-gateway, event-bus, service-discovery, load-testing, secrets-management)
├── validation/            validation/tests/ — 4 integration test files (misplaced)
├── spec_index.json        Specification index (orphaned at root)
└── fix_repo_anchor_paths.py  Utility script (orphaned at root)
```

---

## Issues Found

### ISSUE 1 — Two services/ layers with confusing names

| Layer | Path | What it is |
|---|---|---|
| Platform domain layer | `services/` (root) | 19 pure Python services, dynamic loading via control_plane, no web framework |
| HTTP microservice layer | `backend/services/` | 43 FastAPI services, event-driven, stateful |

These are intentionally separate tiers. Root services/ imports FROM shared/ domain contracts. Backend services/ also import from shared/ for alignment. No reverse cross-imports (confirmed by import audit).

**Proposed rename:** `services/` → `platform/`
**Blast radius:** 12 files total (4 production: subscription-service, tenant-service, payment-service, attempt-service; 8 test files)
**Risk:** MEDIUM — targeted and manageable but requires dedicated sprint
**Recommendation:** Deferred — import-refactor sprint

---

### ISSUE 2 — validation/ is misplaced

4 integration test files at `validation/tests/` (not directly in validation/). They import from both `services/` and `backend/services/` to test cross-service flows.

**Proposed:** Move `validation/tests/` contents → new root `tests/` folder
**Risk:** LOW — no pytest.ini at repo root; service-level configs use relative paths
**Recommendation:** Execute (Tier 2)

---

### ISSUE 3 — Frontend dead routes

In `frontend/app/`:

| Route | Status | Recommendation |
|---|---|---|
| `courses/` | Active LMS route | Keep |
| `courses-v2/` | Superseded experiment | Archive |
| `courses-v3/` | Superseded experiment | Archive |
| `ui-test/` | Dev sandbox page | Archive |
| `job-inquiry-landing/` | Completely unrelated recruitment/writing site | Pending user decision |

**Proposed:** Move dead routes into `frontend/app/_archive/` with _ prefix (Next.js App Router excludes _ folders from routing — confirmed for Next.js 16.2)
**Risk:** ZERO — App Router convention, no code changes
**Recommendation:** Execute (Tier 1)

---

### ISSUE 4 — integrations/payment/ has LIVE PRODUCTION imports (NOT just tests)

Both `integrations/payment/` (old) and `integrations/payments/` (canonical) exist. Verified production imports:
- `services/subscription-service/payment_integration.py` (production)
- `services/commerce/service.py` lines 18–20 (production)
- 6 test files across codebase

**Proposed:** Migration sprint required — migrate above 2 production files to `integrations/payments/`, then remove `integrations/payment/`
**Risk:** MEDIUM — requires code change + testing before folder removal
**Recommendation:** Deferred — migration sprint

---

### ISSUE 5 — docs/architecture/ is a 105+ file catch-all

Mixes macro platform design docs (ARCH_01-08), per-service business phase designs (B*P* codes), and domain/capability model docs.

**Proposed split:**
```
docs/architecture/
├── core/       ARCH_01-08 macro platform design
├── services/   B*P* per-service design docs
└── models/     domain + capability model docs
```
**Risk:** ZERO — docs not imported by code
**Recommendation:** Execute (Tier 2)

---

### ISSUE 6 — docs/qc/ mixes formats

54 files: Markdown reports, Python scripts, and JSON output files together.

**Proposed split:**
```
docs/qc/
├── reports/    .md QC reports (human-readable)
└── scripts/    .py validation scripts + .json outputs
```
**Risk:** ZERO
**Recommendation:** Execute (Tier 2)

---

### ISSUE 7 — docs/specs/ is a 67-file flat folder

67 specs with no internal grouping. Verified categories:

| Category | Count |
|---|---|
| Per-service specs | 24 |
| Feature specs | 11 |
| Cross-cutting / architecture | 10 |
| Business / operational | 8 |
| SPEC_ numbered canonical series | 9 |
| AI-related | 5 |
| Deprecated (superseded by SPEC_01) | 1 |

**Proposed split:**
```
docs/specs/
├── services/   SPEC_* + per-service specs (~33 files)
├── features/   feature specs (11 files)
├── ai/         AI_01-05 (5 files)
├── business/   business + operational (8 files)
└── cross/      migration, capability map, behavioral contract (10 files)
```
**Risk:** ZERO
**Recommendation:** Execute (Tier 2)

---

### ISSUE 8 — docs/ has no root README

270+ files, no navigation index at root.

**Proposed:** Create `docs/README.md`
**Risk:** ZERO — additive
**Recommendation:** Execute (Tier 1)

---

### ISSUE 9 — Two orphaned files at repo root

| File | What it is | Proposed home |
|---|---|---|
| `spec_index.json` | Specification index | `docs/spec_index.json` |
| `fix_repo_anchor_paths.py` | Anchor path utility script | `infrastructure/scripts/fix_repo_anchor_paths.py` |

**Risk:** LOW — need to verify nothing hardcodes root path before moving
**Recommendation:** Execute after path verification (Tier 2)

---

### ISSUE 10 — No .dockerignore at repo root

No root `.dockerignore` means `docs/`, `workspace/`, `validation/`, and `frontend/` get sent in Docker build context for backend service builds — wasteful.

**Proposed:** Create `D:\LMS\Repo\.dockerignore`
**Risk:** ZERO — additive
**Recommendation:** Execute (Tier 1)

---

### ISSUE 11 — CI matrix builds only 39 of 43 backend services

GitHub Actions at `infrastructure/deployment/cicd/deploy-backend.yml` has a build matrix for 39 services. 4 services not covered, likely the non-Python ones (quiz-engine, scorm-service, lesson-service + 1 more).

**Recommendation:** Investigate which 4 are excluded and whether they need a separate CI job for Node.js/TypeScript builds. Flag for sprint.

---

### ISSUE 12 — Two docker-compose.yml files with unclear scope

`infrastructure/deployment/docker-compose.yml` = core stack
`infrastructure/observability/docker-compose.yml` = standalone monitoring stack

**Proposed:** Add comment header to each file clarifying scope. No moves.
**Recommendation:** Execute (Tier 1 — additive comment only)

---

### ISSUE 13 — Dual-source backend services (code issue)

Three backend services have parallel implementations:
- `content-service`: `app/` (FastAPI wrapper) + `content_service/` (framework-agnostic module)
- `media-service`: `app/` + `src/media_service/`
- `assessment-service`: `app/` + `src/`

Each has multiple `main.py` entry points — runtime ambiguity risk.

**Recommendation:** Code cleanup sprint — not a folder move

---

## Confirmed NOT Issues

| Item | Finding |
|---|---|
| `shared/models/plan.py` vs `backend/services/shared/models/plan.py` | Intentionally different models — not drift |
| Root `services/` vs `backend/services/shared/` | Intentional two-tier architecture |
| `docs/anchors/`, `docs/data/`, `docs/integrations/` | All correctly organized, no misplacements |
| Next.js `_` prefix archive approach | Confirmed valid for Next.js 16.2 App Router |

---

## Execution Plan

### Tier 1 — Zero-risk, additive only (ready to execute)
1. Create `docs/README.md` — navigation index
2. Create `.dockerignore` at repo root
3. Add comment headers to both docker-compose.yml files
4. Archive frontend dead routes: `courses-v2`, `courses-v3`, `ui-test` into `frontend/app/_archive/`

### Tier 2 — Safe moves, no code changes (ready to execute)
5. Move `validation/tests/` → `tests/` (new root folder)
6. Move `spec_index.json` → `docs/spec_index.json`
7. Move `fix_repo_anchor_paths.py` → `infrastructure/scripts/`
8. Split `docs/architecture/` into core/ + services/ + models/
9. Split `docs/qc/` into reports/ + scripts/
10. Split `docs/specs/` into services/ + features/ + ai/ + business/ + cross/

### Deferred Sprints (require code changes)
| Sprint | Scope | Priority |
|---|---|---|
| payment/ migration | Migrate 2 production files from integrations/payment/ to integrations/payments/ | High |
| services/ rename | Rename root services/ to platform/ — 12 files to update | Medium |
| CI coverage | Add CI jobs for 4 non-matrix backend services | Medium |
| Dual-source cleanup | Consolidate content-service, media-service, assessment-service app/ vs src/ | Low |

---

## Final Proposed Tree (delta — changes only)

```
D:\LMS\Repo\
├── .dockerignore               NEW
├── backend/services/           UNCHANGED (43 services)
├── services/                   UNCHANGED (rename deferred)
├── shared/                     UNCHANGED
├── integrations/
│   └── payment/                UNCHANGED (migration sprint required first)
├── docs/
│   ├── README.md               NEW
│   ├── spec_index.json         MOVED from repo root
│   ├── architecture/
│   │   ├── core/               NEW subfolder (ARCH_* docs)
│   │   ├── services/           NEW subfolder (B*P* docs)
│   │   └── models/             NEW subfolder (model docs)
│   ├── qc/
│   │   ├── reports/            NEW subfolder (.md reports)
│   │   └── scripts/            NEW subfolder (.py + .json)
│   └── specs/
│       ├── services/           NEW subfolder
│       ├── features/           NEW subfolder
│       ├── ai/                 NEW subfolder
│       ├── business/           NEW subfolder
│       └── cross/              NEW subfolder
├── frontend/
│   └── app/
│       └── _archive/           NEW (houses _courses-v2, _courses-v3, _ui-test)
├── infrastructure/
│   └── scripts/
│       └── fix_repo_anchor_paths.py  MOVED from repo root
├── tests/                      NEW (was validation/tests/)
└── workspace/                  UNCHANGED
```
