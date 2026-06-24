# CODEBASE_PLACEMENT_AUDIT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Companion: REPOSITORY_NORMALIZATION_REPORT.md (findings summary)

---

## PURPOSE

Identify all codebase files that are in unexpected locations, directories with unclear ownership, and placement patterns that may cause confusion or errors. Documentation placement issues are in DOCUMENTATION_PLACEMENT_AUDIT.md.

---

## SCOPE

`backend/`, `frontend/`, `infrastructure/`, `services/`, `integrations/`, `shared/`, `validation/`, `scripts/`

---

## FINDING CP-001: Root `shared/models/` Is a Large Library With Undocumented Consumers

**Severity: MEDIUM**
**Files affected: 49 .py files in `shared/models/`**
**Action required: Owner investigation and documentation**

### Background

`shared/` at root level contains:
- `models/` — 49 Python files (the largest module in the root layer)
- `utils/` — 4 files
- `validation/` — 2 files
- `__init__.py`

A library of 49 model files is not incidental. This is a deliberate shared data model layer. The question is: **what imports it?**

### Hypotheses

**Hypothesis A:** `shared/models/` is imported by root `services/<service>/models.py` and `services/<service>/service.py`. In this case, the import graph is:
```
shared/models/  →  services/<service>/  →  (no HTTP layer)
```
This would be the complete root-layer stack. If `backend/services/` has its own model definitions independent of `shared/`, the root layer is fully legacy.

**Hypothesis B:** `shared/models/` is also imported by `backend/services/` as the canonical data model layer. In this case:
```
shared/models/  →  backend/services/<service>/app/
```
This would mean `shared/` is an active dependency of the primary backend.

**Hypothesis C:** `shared/models/` is imported by `docs/qc/*.py` scripts for validation. This would explain why the scripts live in `docs/qc/` — they need to import the same models.

### Risk

If Hypothesis B is true (shared/ is imported by backend/), then:
- Modifying or moving `shared/` would break the backend
- Any developer reorganizing root directories must understand this dependency
- The 282 `.pyc` files in `backend/` may be partly from importing `shared/`

If Hypothesis A is true (shared/ feeds only root services/), then `shared/` is legacy along with `services/`.

### Action Required

**Owner:** Determine who imports `shared/models/`. Run:
```bash
grep -r "from shared" backend/services/ --include="*.py" | head -20
grep -r "import shared" backend/services/ --include="*.py" | head -20
```

If no matches → `shared/` is root-layer only → LEGACY.
If matches found → `shared/` is active backend dependency → must document.

See: ROOT_LEVEL_CLEANUP_PLAN.md RLC-003

---

## FINDING CP-002: Root `integrations/` Relationship to `backend/integrations/` Unclear

**Severity: MEDIUM**
**Files affected: 53 files in `integrations/`, 20 files in `backend/integrations/`**
**Action required: Owner investigation**

### Background

The repository has two `integrations/` directories:

| Location | Files | Subdirs |
|---|---|---|
| `integrations/` (root) | 53 | communication (10), identity (2), payment (8), payments (26), storage (5) |
| `backend/integrations/` | 20 | (not inspected) |

The root `integrations/` has payment, communication, identity, and storage adapters. The `backend/integrations/` has 20 files (purpose unknown without inspection).

### Hypotheses

**Hypothesis A:** Root `integrations/` is the adapter layer for root `services/`. `backend/integrations/` is the adapter layer for `backend/services/`. They serve the same adapters at different levels.

**Hypothesis B:** Root `integrations/` is the canonical adapter library imported by both `services/` and `backend/services/`. `backend/integrations/` is something different (e.g., internal service-to-service integration helpers).

**Hypothesis C:** Root `integrations/` is legacy (from pre-FastAPI era). `backend/integrations/` is the current adapter layer.

### Risk

If both directories implement the same adapter types (payment, communication), using the wrong one in service code will produce subtle bugs (wrong credentials, wrong API version, wrong error handling).

### Action Required

**Owner:** Inspect `backend/integrations/` structure and compare with root `integrations/`. Determine:
1. Do they serve the same adapters?
2. Are they imported independently by different service layers?
3. Is one legacy?

---

## FINDING CP-003: `infrastructure/service-discovery/` Contains Python

**Severity: LOW**
**Files affected: 2 .py files**
**Action required: None (document only)**

### Background

`infrastructure/service-discovery/` contains:
- 2 `.py` files (registration scripts)
- 2 `.yaml` files (configuration)
- Other configuration files

### Analysis

Service discovery registration scripts in an `infrastructure/` directory are correctly placed — deployment scripts belong near deployment configuration. These are likely:
- A script that registers services in a service registry (Consul, etc.)
- A script that validates service registration

**No action needed.** Add note to infrastructure README about Python script presence.

---

## FINDING CP-004: `backend/` Has No Root-Level Architecture Documentation

**Severity: LOW**
**Files affected: No README.md in backend/**
**Action required: Add README.md (AI can execute)**

### Background

`backend/` is the primary code layer with 70 microservices. It has no root-level README.md. A developer entering `backend/` for the first time has no orientation document.

### Recommended README Content

```markdown
# backend/

Primary Python/FastAPI backend for the Global Capability Platform.

## Contents
- `services/` — 70 FastAPI microservices (see docs/07_governance/DOCUMENTATION_COVERAGE_MATRIX.md for service list)
- `integrations/` — External integration adapters
- `shared/` — Backend-internal shared utilities

## Architecture
See: docs/architecture/core-system-architecture.md

## Service List
See: docs/07_governance/DOCUMENTATION_COVERAGE_MATRIX.md

## Running Services
Each service has its own README.md and requirements.txt in services/<service-name>/
```

**AI can execute:** Yes — this is documentation addition, not code modification.

---

## FINDING CP-005: `backend/services/` Has 70+ Services But Only Some Have `.pytest_cache/`

**Severity: LOW**
**Files affected: ~4 services with .pytest_cache/**
**Action required: Verify gitignore, then no action**

### Background

Only some services (attempt-service, auth-service, cohort-service, content-service) have `.pytest_cache/` directories. This means:
- Tests were run locally in only those services
- The cache directories are generated artifacts

### Analysis

**If `.pytest_cache/` is in root `.gitignore`:** Correct behavior — these are local artifacts.
**If `.pytest_cache/` is NOT in root `.gitignore`:** They may get committed on the next `git add`.

### Action

Check `.gitignore`:

```
cat .gitignore | grep pytest_cache
```

If missing, add:
```
.pytest_cache/
```

This is a safe, non-destructive `.gitignore` update.

---

## FINDING CP-006: `frontend/.env.local` Must Be Verified as Gitignored

**Severity: HIGH (security)**
**Files affected: `frontend/.env.local`**
**Action required: Immediate verification**

### Background

`frontend/.env.local` is present in the repository. `.env.local` files are used by Next.js for local environment overrides. They commonly contain:
- API keys (Next.js public API keys, Stripe keys, etc.)
- Local database URLs
- Authentication secrets
- Feature flag overrides

If `frontend/.env.local` contains actual credentials and is tracked by git, those credentials are in the git history and may have been exposed.

### Action (AI can execute — read-only check)

1. Read `frontend/.gitignore` — check for `.env.local` entry
2. Check root `.gitignore` — check for `.env.local` entry
3. Check if file is git-tracked (requires git access with safe.directory)

**If tracked:** Immediately alert owner — credential rotation may be required.
**If gitignored:** No action needed.

**This is the highest-priority finding in this audit.**

---

## FINDING CP-007: `infrastructure/deployment/` Has `.env` Files

**Severity: MEDIUM (security)**
**Files affected: 2 `.env` files in `infrastructure/deployment/`**
**Action required: Verify these are template/example files, not real secrets**

### Background

`infrastructure/deployment/` contains 2 `.env` files. Deployment environment files should be:
- Templates (`.env.example`, `.env.template`) — safe to commit
- Actual secret files (`.env`, `.env.production`) — should NOT be committed

### Action

Verify these files are example/template files with placeholder values, not actual deployment secrets.

---

## FINDING CP-008: Root `validation/` Purpose Is Unclear

**Severity: LOW**
**Files affected: 4 .py files**
**Action required: Document or incorporate**

### Background

`validation/` at root has 4 .py files. Given that `docs/qc/` has 11 .py validation scripts and `backend/services/*/tests/` has per-service tests, the purpose of a root `validation/` directory is unclear.

### Possible Interpretations

**A:** Cross-service validation (tests that span multiple services) — these are integration tests that don't belong to any single service.

**B:** Repository-level validation (checks that docs/code are in sync) — co-purpose with `docs/qc/*.py` scripts.

**C:** Legacy standalone scripts from pre-test-suite era.

### Action

Owner: review the 4 files and classify as A, B, or C. AI will add README.md after classification.

---

## CODEBASE PLACEMENT SUMMARY

| Finding | Severity | Location | Issue | Action |
|---|---|---|---|---|
| CP-001 | Medium | `shared/models/` | 49-file model library, consumers unknown | Owner investigation |
| CP-002 | Medium | `integrations/` vs `backend/integrations/` | Relationship unknown | Owner investigation |
| CP-003 | Low | `infrastructure/service-discovery/*.py` | Python in infrastructure dir | Document (acceptable) |
| CP-004 | Low | `backend/` (no README) | Missing orientation doc | AI can add README.md |
| CP-005 | Low | `backend/services/*/.pytest_cache/` | Generated cache dirs | Verify gitignore |
| CP-006 | **HIGH** | `frontend/.env.local` | Potential credential exposure | Immediate verification |
| CP-007 | Medium | `infrastructure/deployment/*.env` | Potential secrets in deployment config | Verify template vs. real |
| CP-008 | Low | `validation/` (4 files) | Purpose undocumented | Owner classification |

---

## IMMEDIATE ACTIONS (No Owner Approval Required)

The following can be executed by AI without code changes:

1. **CP-006**: Read `frontend/.gitignore` to verify `.env.local` is excluded → **execute now**
2. **CP-004**: Add `backend/README.md` → execute after owner confirms content
3. **CP-005**: Read root `.gitignore` to verify `.pytest_cache/` is excluded
