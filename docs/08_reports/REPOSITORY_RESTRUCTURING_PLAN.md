# REPOSITORY_RESTRUCTURING_PLAN

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Synthesizes: All 8 companion audit documents

---

## PURPOSE

Define the ordered, prioritized action plan for restructuring the repository based on all findings from the Full Repository Normalization and Reality Audit. This plan is the single authoritative reference for what must be done, by whom, and in what order.

---

## SCOPE BOUNDARIES

**In scope:**
- Root directory documentation and classification
- Placement of scripts and generated artifacts
- Security verification (gitignore coverage)
- Adding README.md orientation documents
- Retiring legacy code directories via classification banners

**Out of scope (do not begin):**
- Frontend source code development (Phase 2)
- Backend service implementation changes
- CI/CD pipeline creation
- Database migrations
- Infrastructure provisioning
- Deleting any directory or file

---

## CURRENT STATE SUMMARY

| Layer | Directories | Files | Status |
|---|---|---|---|
| Primary backend (backend/services/) | 70 services | 1,552 | ACTIVE — current production code layer |
| Documentation (docs/) | 30+ | 289 | CLEAN — governance framework established |
| Frontend source (frontend/ excl. node_modules) | 5 | 75 | UNSTARTED — Phase 2 work pending |
| Infrastructure (infrastructure/) | 7 | 56 | ACTIVE — correctly placed |
| Root service layer (services/) | 20 | 97 | LIKELY LEGACY — requires owner confirmation |
| Root shared library (shared/) | 3 | 59 | UNCLASSIFIED — may be active dependency |
| Root integrations (integrations/) | 5 | 53 | UNCLASSIFIED — may be active dependency |
| Standalone scripts (validation/, scripts/) | — | 5 | UNCLASSIFIED |

---

## PRIORITY 1 — SECURITY (Execute Immediately)

### P1-SEC-001: Verify `frontend/.env.local` Is Not Tracked

**Status: RESOLVED** — Verified during this audit session.

- `frontend/.env.local` is excluded by `frontend/.gitignore` (`.env*`) and root `.gitignore` (`.env.local`)
- File contents: `NEXT_TELEMETRY_DISABLED=1` (non-sensitive)
- No credential exposure risk

**No action needed.**

### P1-SEC-002: Verify `.env` Files in `infrastructure/deployment/`

**Status: PENDING — Owner action**
**Owner action required: YES**

Read `infrastructure/deployment/*.env` files to confirm they contain placeholder values, not actual deployment secrets. If real secrets are present, they must be removed from git history.

---

## PRIORITY 2 — CLASSIFICATION (Owner Decision Required)

### P2-CLASS-001: Classify Root `services/` as Active or Legacy

**Owner action required: YES**
**AI can execute after: YES (README.md additions)**

**Decision method:**
```bash
grep -r "from services\." backend/ --include="*.py" | head -5
grep -r "import services\." backend/ --include="*.py" | head -5
```

**If no matches:** Root `services/` is LEGACY. Proceed to P3-README-001.
**If matches found:** Root `services/` is ACTIVE. Proceed to P3-README-002.

See: LEGACY_AND_ARCHIVE_PLAN.md Phase A

---

### P2-CLASS-002: Classify Root `shared/` Import Dependency

**Owner action required: YES**
**AI can execute after: YES (README.md additions)**

**Decision method:**
```bash
grep -r "from shared\." backend/ --include="*.py" | head -10
grep -r "import shared\." backend/ --include="*.py" | head -10
```

**If no matches:** Root `shared/` is LEGACY.
**If matches found:** Root `shared/` is an ACTIVE backend dependency — must document carefully.

---

### P2-CLASS-003: Classify Root `integrations/` Dependency

**Owner action required: YES**

**Decision method:**
```bash
grep -r "from integrations\." backend/ --include="*.py" | head -10
grep -r "from integrations\." services/ --include="*.py" | head -10
```

Also resolve: `integrations/payment/` vs `integrations/payments/` — which is canonical?

---

### P2-CLASS-004: Classify `validation/` and `scripts/` Purpose

**Owner action required: YES**

Review the 4 files in `validation/` and 1 file in `scripts/`. Determine:
- Are these maintenance utilities or production scripts?
- Who runs them and when?
- Do they import from `shared/` or `backend/`?

---

## PRIORITY 3 — DOCUMENTATION (AI Can Execute After P2)

### P3-README-001: Add README.md to Root Code Directories

**Owner action required: After P2 classification decisions**
**AI can execute: YES**

Create README.md in:
- `services/` — status determined by P2-CLASS-001
- `shared/` — status determined by P2-CLASS-002
- `integrations/` — status determined by P2-CLASS-003
- `validation/` — status determined by P2-CLASS-004
- `scripts/` — status determined by P2-CLASS-004

Template: see ROOT_LEVEL_CLEANUP_PLAN.md RLC-003

---

### P3-README-002: Add `backend/README.md`

**Owner action required: NO**
**AI can execute: YES**

Add orientation document to `backend/` directory pointing to:
- Service list: `docs/07_governance/DOCUMENTATION_COVERAGE_MATRIX.md`
- Architecture: `docs/architecture/core-system-architecture.md`
- Per-service docs: `backend/services/<name>/README.md`

---

### P3-README-003: Add README to `docs/architecture/capabilities/` and `docs/architecture/schemas/`

**Owner action required: NO**
**AI can execute: YES**

Note that these directories contain JSON data artifacts co-located with their documentation. Explains the B0P0X naming convention and relationship to capability-registry service.

---

### P3-GITIGNORE-001: Update `docs/governance/spec_index.json` Status

**Owner action required: Verify consumer**

Determine if any script or tool reads `docs/governance/spec_index.json`. If not consumed, retire it or note it as a generated artifact.

---

## PRIORITY 4 — CODE PLACEMENT (Owner Approval Required)

### P4-MOVE-001: Move `docs/qc/*.py` Scripts to `validation/`

**Owner action required: YES**
**Risk: LOW (script move — may need path updates)**

Move 11 Python validation scripts from `docs/qc/` to `validation/`:
```
docs/qc/b7p01_*.py → validation/b7p01_*.py
...
docs/qc/performance_smoke_tests.py → validation/performance_smoke_tests.py
```

Before moving: inspect each script for relative path references (`../..` etc.) and update paths accordingly.

After moving: verify scripts still run correctly from `validation/` directory.

See: DOCUMENTATION_PLACEMENT_AUDIT.md DP-001

---

### P4-MOVE-002: Resolve `integrations/payment/` vs `integrations/payments/` Overlap

**Owner action required: YES**
**Risk: MEDIUM (affects import paths)**

After P2-CLASS-003 decision, consolidate the two payment adapter directories or document their distinct purposes.

See: ROOT_LEVEL_CLEANUP_PLAN.md RLC-002

---

## PRIORITY 5 — LEGACY RETIREMENT (Owner Approval Required)

### P5-RETIRE-001: Add LEGACY Banners to Classified Legacy Directories

**Owner action required: After P2 classification**
**AI can execute: YES**

For each directory confirmed as LEGACY in P2, add a README.md with LEGACY classification banner.

No files are moved or deleted. Classification is documentation-only.

### P5-RETIRE-002: Update `docs/anchors/capability-resolution.md` (Previously Deferred)

**Owner action required: YES (protected anchor)**

Carried over from Phase 1 audit:
- Remove PLAN level from config hierarchy
- Remove runtime_override
- Correct to 4-level: GLOBAL → COUNTRY → SEGMENT → TENANT

### P5-RETIRE-003: Update `docs/anchors/doc-precedence.md` (Previously Deferred)

**Owner action required: YES (protected anchor)**

Carried over from Phase 1 audit:
- Replace BATCH > SPEC > ARCH > Legacy model
- Adopt TIER 0–5 model per AUTHORITY_MAPPING_MATRIX.md

---

## PRIORITY 6 — LONG-TERM (Phase 3+)

These are not actionable in the current phase but should be tracked:

| Item | When | Owner |
|---|---|---|
| Move legacy `services/` to `_legacy/services/` | After P5-RETIRE-001 confirmed | Owner |
| Backend authority docs to `docs/01_backend/` | Backend Authority Capture phase | Owner |
| Frontend authority docs to `docs/02_frontend/` | Phase 2 | Owner |
| Test strategy to `docs/04_testing/` | Phase 3 | Owner |
| Deployment strategy to `docs/05_deployment/` | Phase 3 | Owner |
| Move capability JSON from docs/ to service | Long-term | Developer |

---

## EXECUTION SUMMARY TABLE

| Ref | Action | Priority | Owner Required | AI Executes | Status |
|---|---|---|---|---|---|
| P1-SEC-001 | Verify .env.local gitignore | 1 — Security | No | Yes | DONE (this session) |
| P1-SEC-002 | Verify infrastructure/*.env content | 1 — Security | YES | No | PENDING |
| P2-CLASS-001 | Classify root services/ | 2 — Classification | YES | After decision | PENDING |
| P2-CLASS-002 | Classify root shared/ | 2 — Classification | YES | After decision | PENDING |
| P2-CLASS-003 | Classify root integrations/ | 2 — Classification | YES | After decision | PENDING |
| P2-CLASS-004 | Classify validation/ and scripts/ | 2 — Classification | YES | After decision | PENDING |
| P3-README-001 | Add README.md to root code dirs | 3 — Documentation | After P2 | YES | PENDING |
| P3-README-002 | Add backend/README.md | 3 — Documentation | No | YES | PENDING |
| P3-README-003 | Add README to capabilities/ + schemas/ | 3 — Documentation | No | YES | PENDING |
| P4-MOVE-001 | Move docs/qc/*.py to validation/ | 4 — Placement | YES | After approval | PENDING |
| P4-MOVE-002 | Resolve payment/ vs payments/ | 4 — Placement | YES | After approval | PENDING |
| P5-RETIRE-001 | Add LEGACY banners | 5 — Retirement | After P2 | YES | PENDING |
| P5-RETIRE-002 | Update capability-resolution.md | 5 — Retirement | YES (anchor) | No | PENDING |
| P5-RETIRE-003 | Update doc-precedence.md | 5 — Retirement | YES (anchor) | No | PENDING |

---

## WHAT DOES NOT CHANGE

The following are confirmed stable and require no action from this audit:

| Item | Status | Reason |
|---|---|---|
| `backend/services/` (70 services) | UNCHANGED | Primary active layer; fully structured |
| `docs/` governance framework | UNCHANGED | Established and remediated in prior phases |
| `infrastructure/` | UNCHANGED | Correctly structured operations config |
| All `.gitignore` coverage | CONFIRMED CORRECT | .pyc, .pytest_cache, node_modules, .env all gitignored |
| `frontend/node_modules/` | LOCAL ONLY | Not tracked; correct behavior |
| All `.pyc` files | LOCAL ONLY | Not tracked; correct behavior |
| All remediation from prior phases | UNCHANGED | 31+ findings resolved; 2 anchor items pending owner |

---

## AUDIT CLOSURE

This audit (FULL REPOSITORY NORMALIZATION AND REALITY AUDIT) is complete when all 9 output documents are produced:

| Document | Status |
|---|---|
| REPOSITORY_TREE_INVENTORY.md | DONE |
| REPOSITORY_CLASSIFICATION_MATRIX.md | DONE |
| REPOSITORY_NORMALIZATION_REPORT.md | DONE |
| ROOT_LEVEL_CLEANUP_PLAN.md | DONE |
| DOCUMENTATION_PLACEMENT_AUDIT.md | DONE |
| CODEBASE_PLACEMENT_AUDIT.md | DONE |
| GENERATED_ARTIFACT_REGISTER.md | DONE |
| LEGACY_AND_ARCHIVE_PLAN.md | DONE |
| REPOSITORY_RESTRUCTURING_PLAN.md | DONE (this document) |

**Audit status: COMPLETE**

All findings documented. No files modified. No code changed. All restructuring actions require owner review before execution. Priority ordering established above.
