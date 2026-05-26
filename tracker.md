# Repo Restructuring Tracker
**Status:** REVERT COMPLETE — all files confirmed in original flat locations (verified 2026-05-26)
**Last updated:** 2026-05-26

---

## What Was Moved (Unauthorised — Being Reverted)

| # | What | From | To | Revert Status |
|---|---|---|---|---|
| 1 | courses-v2/ | frontend/app/courses-v2/ | frontend/app/_archive/courses-v2/ | COMPLETE |
| 2 | courses-v3/ | frontend/app/courses-v3/ | frontend/app/_archive/courses-v3/ | COMPLETE |
| 3 | ui-test/ | frontend/app/ui-test/ | frontend/app/_archive/ui-test/ | COMPLETE |
| 4 | 4 test files | validation/tests/ | tests/ (root) | COMPLETE |
| 5 | spec_index.json | repo root | docs/spec_index.json | COMPLETE |
| 6 | fix_repo_anchor_paths.py | repo root | infrastructure/scripts/ | COMPLETE |
| 7 | 29 arch files | docs/architecture/ (flat) | docs/architecture/core/ | COMPLETE |
| 8 | 43 arch files | docs/architecture/ (flat) | docs/architecture/services/ | COMPLETE |
| 9 | 17 arch files | docs/architecture/ (flat) | docs/architecture/models/ | COMPLETE |
| 10 | 28 qc files | docs/qc/ (flat) | docs/qc/reports/ | COMPLETE |
| 11 | 20 qc files | docs/qc/ (flat) | docs/qc/scripts/ | COMPLETE |
| 12 | 38 spec files | docs/specs/ (flat) | docs/specs/services/ | COMPLETE |
| 13 | 11 spec files | docs/specs/ (flat) | docs/specs/features/ | COMPLETE |
| 14 | 5 spec files | docs/specs/ (flat) | docs/specs/ai/ | COMPLETE |
| 15 | 7 spec files | docs/specs/ (flat) | docs/specs/business/ | COMPLETE |
| 16 | 6 spec files | docs/specs/ (flat) | docs/specs/cross/ | COMPLETE |

## New Files Created (To Be Deleted on Revert)

| File | Action |
|---|---|
| docs/README.md | DELETE |
| .dockerignore | DELETE |
| docker-compose headers (deployment) | REMOVE COMMENT |
| docker-compose headers (observability) | REMOVE COMMENT |

---

## Restructuring Proposal (APPROVED ITEMS — Pending User Go-Ahead)

> Nothing below this line has been executed. Awaiting explicit user approval per item.

### Tier 1 — Zero risk, additive
- [ ] Create docs/README.md
- [ ] Create .dockerignore
- [ ] Add scope headers to docker-compose.yml files
- [ ] Archive frontend dead routes (courses-v2, courses-v3, ui-test)

### Tier 2 — Safe moves
- [ ] Move validation/tests/ → tests/
- [ ] Move spec_index.json → docs/spec_index.json
- [ ] Move fix_repo_anchor_paths.py → infrastructure/scripts/
- [ ] Split docs/architecture/ into core/ + services/ + models/
- [ ] Split docs/qc/ into reports/ + scripts/
- [ ] Split docs/specs/ into services/ + features/ + ai/ + business/ + cross/

### Deferred Sprints (require code changes — separate approval)
- [ ] integrations/payment/ migration
- [ ] services/ → platform/ rename
- [ ] CI matrix gap (4 missing services)
- [ ] Dual-source cleanup (content/media/assessment)
