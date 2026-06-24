# ROOT_LEVEL_CLEANUP_PLAN

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Companion: REPOSITORY_NORMALIZATION_REPORT.md (findings)

---

## PURPOSE

This plan defines the specific actions required to resolve structural issues at the repository root level. No action in this plan may be executed without explicit owner approval. All actions are reversible (no deletions).

---

## CURRENT ROOT STRUCTURE

```
D:\SaaS\LMS\Repo\
├── backend/          PRIMARY code layer (70 services)
├── docs/             Documentation
├── frontend/         Frontend application
├── infrastructure/   Operational configuration
├── integrations/     Root layer integration adapters (NEEDS-REVIEW)
├── scripts/          Single maintenance script (NEEDS-REVIEW)
├── services/         Root layer service modules (LIKELY LEGACY)
├── shared/           Root layer shared library (NEEDS-REVIEW)
├── validation/       Standalone validation scripts (NEEDS-REVIEW)
├── .gitattributes
├── .gitignore
└── .gitkeep
```

**4 directories are unclassified (NEEDS-REVIEW):** integrations/, services/, shared/, validation/

---

## ACTION PLAN

### RLC-001: Classify Root `services/` Layer

**Priority: HIGH**
**Owner action required: YES — classification decision**
**AI can execute after decision: YES (README.md additions)**

**Background:**
Root `services/` contains 20 thin service modules (models.py + service.py per service) with no HTTP layer and no requirements.txt. These do NOT match the canonical service names in `backend/services/`. The naming suggests they are the pre-FastAPI platform tier.

**Required owner decision:**

OPTION A — Still Active (imported by other root code):
```
services/         (ACTIVE — root platform layer)
```
Action: Add README.md to services/ explaining import graph. Add note to AI_OPERATING_CONTEXT.md about two-layer service architecture.

OPTION B — Fully Legacy (no longer imported):
```
services/         → reclassify as LEGACY
```
Action: Add LEGACY banner to each service's README.md (create if missing). No deletion needed; legacy status prevents confusion.

OPTION C — Partially Active:
Identify which services are active vs. legacy. Apply A to active, B to inactive.

**Decision question for owner:** Does any file in `backend/`, `docs/`, or elsewhere import from `services.<service_name>.*`? If yes → Option A or C. If no → Option B.

---

### RLC-002: Resolve `integrations/payment/` vs `integrations/payments/` Overlap

**Priority: MEDIUM**
**Owner action required: YES — consolidation decision**
**AI can execute after decision: NO (code change)**

**Background:**
`integrations/` contains two payment-related directories:
- `integrations/payment/` — 8 files (probably individual provider adapter)
- `integrations/payments/` — 26 files (more extensive; probably the larger processing layer)

**Required owner decision:**

OPTION A — Both active (different purposes):
Action: Add README.md to each explaining the difference (e.g., `payment/` = provider adapters, `payments/` = processing orchestration).

OPTION B — `payment/` is legacy (superseded by `payments/`):
Action: Move `integrations/payment/*.py` to `integrations/_archive/payment/` and add deprecation notice.

OPTION C — Merge:
Action: Consolidate `payment/` content into `payments/` (requires code change — owner/developer).

**Decision question for owner:** Are both directories imported independently? Which was created first?

---

### RLC-003: Document Root Code Layer Purpose

**Priority: MEDIUM**
**Owner action required: YES — confirm scope**
**AI can execute after decision: YES (README.md creation)**

**Background:**
The following root directories have no README.md or documentation of purpose:
- `integrations/` — 53 files, 5 adapter subdirs
- `shared/` — 59 files, models (49), utils (4), validation (2)
- `validation/` — 4 standalone .py scripts
- `scripts/` — 1 .py maintenance script

**Proposed README content template for each:**

```markdown
# <Directory Name>

Layer: [Root Platform Layer | Infrastructure Utility]
Status: [Active | Legacy | Needs Review]

## Purpose
<One paragraph: what this directory provides>

## Used By
<List of importers: backend/services/<X>, scripts/*, etc.>

## Not Used By
<What this does NOT feed into>

## Relationship to backend/<dir>
<How this relates to backend/integrations/ or backend/shared/>
```

**AI will create these README.md files after owner confirms the status of each directory.**

---

### RLC-004: Verify `.gitignore` Covers `.pytest_cache/`

**Priority: LOW**
**Owner action required: NO — safe to verify**
**AI can execute: YES (read-only check)**

**Background:**
Several `backend/services/` directories contain `.pytest_cache/` subdirectories with cache files. Git does not track `.pyc` files (confirmed: 0 tracked). `.pytest_cache/` should similarly be excluded.

**Action:** Check root `.gitignore` for `.pytest_cache/` entry. If missing, add:
```
.pytest_cache/
```

**Risk:** Low. Adding to .gitignore does not affect existing tracked files.

**Status:** Pending read of .gitignore.

---

### RLC-005: Verify `frontend/.env.local` Is Gitignored

**Priority: MEDIUM**
**Owner action required: NO — security check**
**AI can execute: YES (read-only check, then gitignore update if needed)**

**Background:**
`frontend/.env.local` is present. `.env.local` files typically contain API keys, secrets, or local override values. If it contains actual secrets and is tracked by git, this is a security issue.

**Action:**
1. Check if `.env.local` is in `frontend/.gitignore` or root `.gitignore`
2. Check if it is currently git-tracked
3. If tracked: immediately notify owner — sensitive data may be in git history
4. If gitignored: no action needed

---

## EXECUTION SEQUENCE

| Step | Action | Ref | Owner? | Priority |
|---|---|---|---|---|
| 1 | Verify .gitignore has .pytest_cache/ | RLC-004 | No | Low |
| 2 | Verify .env.local is gitignored | RLC-005 | No | Medium |
| 3 | Owner: classify root services/ | RLC-001 | YES | High |
| 4 | Add README.md to root code dirs | RLC-003 | After #3 | Medium |
| 5 | Owner: resolve payment/ vs payments/ | RLC-002 | YES | Medium |
| 6 | Execute consolidation per decision | RLC-002 | After #5 | Medium |

---

## NOT IN SCOPE FOR THIS PLAN

- Moving application code between layers
- Deleting any directory or file
- Changing Python import paths
- Modifying .gitignore to add new exclusions (requires review)
- Moving frontend/node_modules/ (it is gitignored and local-only)

---

## EXPECTED OUTCOME

After full execution of this plan:

```
D:\SaaS\LMS\Repo\
├── backend/          (unchanged — primary code)
├── docs/             (unchanged)
├── frontend/         (unchanged)
├── infrastructure/   (unchanged)
├── integrations/     README.md added — purpose documented
├── scripts/          README.md added — purpose documented
├── services/         README.md added — status classified (Active/Legacy)
├── shared/           README.md added — purpose documented
└── validation/       README.md added — purpose documented
```

All root-level code directories will have documented purpose and classification. No code will be moved or deleted.
