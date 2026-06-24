# APPROVAL_RECLASSIFICATION_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Source: GOVERNANCE REFINEMENT — SAFE REPOSITORY HYGIENE.md
Companion: SAFE_REPOSITORY_HYGIENE_POLICY.md, REVISED_DECISION_ESCALATION_MATRIX.md

---

## PURPOSE

Review every open owner-approval item from recent audit phases and reclassify each as:
- `SRH` — Safe Repository Hygiene (AI executes without approval)
- `REQUIRES_APPROVAL` — Owner must explicitly authorize
- `PROHIBITED` — Must not be done regardless of instruction

Sources reviewed:
- REPOSITORY_RESTRUCTURING_PLAN.md (9 pending items)
- ROOT_LEVEL_CLEANUP_PLAN.md (5 items)
- DOCUMENTATION_PLACEMENT_AUDIT.md (4 items)
- CODEBASE_PLACEMENT_AUDIT.md (8 items)
- LEGACY_AND_ARCHIVE_PLAN.md (3 items)
- Prior phase deferred items (2 protected anchor items)

---

## RECLASSIFICATION TABLE

### From REPOSITORY_RESTRUCTURING_PLAN.md

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| P1-SEC-001 | Verify `frontend/.env.local` gitignore | REQUIRES_APPROVAL | **RESOLVED** | Executed this session — confirmed gitignored, content non-sensitive |
| P1-SEC-002 | Verify `infrastructure/deployment/*.env` content | REQUIRES_APPROVAL | **SRH** | Read-only verification check; no files modified; security posture improved |
| P2-CLASS-001 | Run import search for root `services/` | REQUIRES_APPROVAL | **AUTONOMOUS** | `grep` is a read-only operation; producing evidence for an owner decision |
| P2-CLASS-002 | Run import search for root `shared/` | REQUIRES_APPROVAL | **AUTONOMOUS** | Same — read-only grep |
| P2-CLASS-003 | Run import search for root `integrations/` | REQUIRES_APPROVAL | **AUTONOMOUS** | Same — read-only grep |
| P2-CLASS-004 | Review `validation/` and `scripts/` files | REQUIRES_APPROVAL | **AUTONOMOUS** | Reading files to classify; no modification |
| P3-README-001 | Add README.md to root code dirs (services/, shared/, integrations/, validation/, scripts/) | REQUIRES_APPROVAL | **SRH** | Orientation documents only; no authority claims; no logic changes; fully reversible |
| P3-README-002 | Add `backend/README.md` | REQUIRES_APPROVAL | **SRH** | Orientation document pointing to existing authority docs; no new claims |
| P3-README-003 | Add README.md to `docs/architecture/capabilities/` and `docs/architecture/schemas/` | REQUIRES_APPROVAL | **SRH** | Explains co-located JSON artifacts; adds context without claiming authority |
| P4-MOVE-001 | Move `docs/qc/*.py` scripts to `validation/` | REQUIRES_APPROVAL | **SRH** | Scripts are non-production QC tools; do not affect runtime, APIs, or business logic; move improves placement without changing content; prerequisite: verify relative paths before moving |
| P4-MOVE-002 | Resolve `integrations/payment/` vs `integrations/payments/` overlap | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | `integrations/payments/` is in PROTECTED_AREAS (production-confirmed payment code); cannot consolidate without owner decision and verification |
| P5-RETIRE-001 | Add LEGACY banners to root services/ (after owner confirms legacy status) | REQUIRES_APPROVAL | **SRH** | Adding a status banner to a README is documentation classification; does not change code; requires owner classification decision first (REQUIRES_APPROVAL for the decision, SRH for the execution) |
| P5-RETIRE-002 | Update `docs/anchors/capability-resolution.md` (4-level config) | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | Protected anchor; content change cascades to all consumers; owner must approve |
| P5-RETIRE-003 | Update `docs/anchors/doc-precedence.md` (TIER 0–5 model) | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | Protected anchor; same rationale |

---

### From ROOT_LEVEL_CLEANUP_PLAN.md

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| RLC-001 | Classify root `services/` (owner decides Active/Legacy) | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | Architectural classification decision with import/runtime implications; owner must decide |
| RLC-001 (AI part) | After RLC-001 decision: add README.md to services/ | REQUIRES_APPROVAL | **SRH** | Executing the documentation of an owner decision; no code change |
| RLC-002 | Resolve `integrations/payment/` vs `integrations/payments/` | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | Protected production payment code |
| RLC-003 | Add README.md to root code dirs | REQUIRES_APPROVAL | **SRH** | Orientation documentation; see P3-README-001 |
| RLC-004 | Verify `.pytest_cache/` in `.gitignore` | REQUIRES_APPROVAL | **RESOLVED** | Verified this session — `.pytest_cache/` is already in root `.gitignore` |
| RLC-005 | Verify `frontend/.env.local` gitignore | REQUIRES_APPROVAL | **RESOLVED** | Verified this session — gitignored; non-sensitive content |

---

### From DOCUMENTATION_PLACEMENT_AUDIT.md

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| DP-001 | Move `docs/qc/*.py` to `validation/` | REQUIRES_APPROVAL | **SRH** | Non-production QC scripts; no runtime impact; placement improvement only; prerequisite: verify no breaking relative paths |
| DP-002 | Classify/document JSON files in `docs/architecture/capabilities/` and `schemas/` | REQUIRES_APPROVAL | **SRH** | Adding README notes explaining co-location rationale; no content change |
| DP-003 | `docs/governance/spec_index.json` status | REQUIRES_APPROVAL | **SRH** | Determining if it is consumed by any tool is a read-only investigation (AUTONOMOUS); adding a status note is SRH |
| DP-004 | Empty placeholder dirs (01_backend through 05_deployment) | REQUIRES_APPROVAL | **SRH** | Adding PLACEHOLDER.md files with phase context is orientation documentation |

---

### From CODEBASE_PLACEMENT_AUDIT.md

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| CP-001 | Investigate `shared/models/` consumers (grep) | REQUIRES_APPROVAL | **AUTONOMOUS** | Read-only grep to gather evidence for owner decision |
| CP-001 (AI part) | Add README.md to `shared/` describing status after owner confirms | REQUIRES_APPROVAL | **SRH** | Documentation of an owner decision |
| CP-002 | Investigate `integrations/` vs `backend/integrations/` (grep) | REQUIRES_APPROVAL | **AUTONOMOUS** | Read-only grep; no files modified |
| CP-002 (exec) | Consolidate or retire `integrations/` directories | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | Both directories are in PROTECTED_AREAS |
| CP-003 | Document `infrastructure/service-discovery/*.py` presence | REQUIRES_APPROVAL | **SRH** | Adding a README note; no code change |
| CP-004 | Add `backend/README.md` | REQUIRES_APPROVAL | **SRH** | Orientation document; see P3-README-002 |
| CP-005 | Verify `.pytest_cache/` gitignore | REQUIRES_APPROVAL | **RESOLVED** | Confirmed this session |
| CP-006 | Verify `frontend/.env.local` gitignore | REQUIRES_APPROVAL | **RESOLVED** | Confirmed this session |
| CP-007 | Verify `infrastructure/deployment/*.env` content | REQUIRES_APPROVAL | **SRH** | Read-only security verification |
| CP-008 | Add README to `validation/` after owner classifies | REQUIRES_APPROVAL | **SRH** | Orientation documentation after classification |

---

### From LEGACY_AND_ARCHIVE_PLAN.md

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| Phase A | Import analysis to confirm legacy status | REQUIRES_APPROVAL | **AUTONOMOUS** | Read-only grep; no files modified |
| Phase B | Add LEGACY classification to root services/ directories | REQUIRES_APPROVAL | **SRH** (after Phase A + owner confirmation) | Status banner in README; no code change; reversible |
| Phase C | Create LEGACY README.md in each legacy-confirmed service | REQUIRES_APPROVAL | **SRH** | Documentation addition; no code change |
| Phase D | Move `services/` to `_legacy/services/` | REQUIRES_APPROVAL | **REQUIRES_APPROVAL** | File system restructuring of code directories; import path impact; owner sign-off required |

---

### Carried from Prior Audit Phases

| Ref | Action | Previous | New | Rationale |
|---|---|---|---|---|
| R-009 | Update `docs/anchors/capability-resolution.md` | REQUIRES_APPROVAL (owner) | **REQUIRES_APPROVAL** | No change — protected anchor; content is wrong (6-level) but requires owner |
| R-010 | Update `docs/anchors/doc-precedence.md` | REQUIRES_APPROVAL (owner) | **REQUIRES_APPROVAL** | No change — protected anchor; BATCH model is obsolete but requires owner |

---

## RECLASSIFICATION SUMMARY

| Category | Count |
|---|---|
| Reclassified to SRH | **16** |
| Reclassified to AUTONOMOUS | **7** |
| Remain REQUIRES_APPROVAL | **9** |
| Resolved this session (no longer open) | **5** |
| **Total items reviewed** | **37** |

---

## SRH ACTIONS — EXECUTION QUEUE

The following SRH items may be executed in the next session without additional owner approval:

### Batch 1 — No Prerequisites (Execute First)

| ID | Action | Location |
|---|---|---|
| SRH-001 | Add `backend/README.md` | `backend/` |
| SRH-002 | Add README.md to `docs/architecture/capabilities/` | `docs/architecture/capabilities/` |
| SRH-003 | Add README.md to `docs/architecture/schemas/` | `docs/architecture/schemas/` |
| SRH-004 | Verify `docs/governance/spec_index.json` consumer (then add status note) | `docs/governance/` |
| SRH-005 | Add PLACEHOLDER.md to `docs/01_backend/` through `docs/05_deployment/` | `docs/01_backend/` etc. |
| SRH-006 | Verify `infrastructure/deployment/*.env` content (read-only security check) | `infrastructure/deployment/` |

### Batch 2 — Move `docs/qc/*.py` to `validation/`

| ID | Action | Prerequisite |
|---|---|---|
| SRH-007 | Read each `docs/qc/*.py` to verify no breaking relative path imports | None |
| SRH-008 | Move 11 `.py` scripts from `docs/qc/` to `validation/` | SRH-007 complete |
| SRH-009 | Update any relative path imports in moved scripts | SRH-008 complete |

### Batch 3 — Requires Owner Classification Decision First

| ID | Action | Owner Decision Needed |
|---|---|---|
| SRH-010 | Add README.md to `services/` with LEGACY status | P2-CLASS-001 + RLC-001: owner confirms services/ is legacy |
| SRH-011 | Add README.md to `shared/` with appropriate status | P2-CLASS-002: owner confirms shared/ consumers |
| SRH-012 | Add README.md to `integrations/` with appropriate status | P2-CLASS-003: owner confirms integrations/ consumers |
| SRH-013 | Add README.md to `validation/` and `scripts/` | P2-CLASS-004: owner reviews these 5 files |
| SRH-014 | Add LEGACY banners to each `services/<svc>/` README | SRH-010 complete |

---

## ACTIONS REMAINING AS REQUIRES_APPROVAL

These items still need explicit owner authorization before AI can act:

| ID | Action | Reason |
|---|---|---|
| OWN-001 | Confirm root `services/` as Active or Legacy | Architectural decision with runtime implications |
| OWN-002 | Confirm root `shared/` import dependency | May be active backend dependency |
| OWN-003 | Confirm root `integrations/` relationship to `backend/integrations/` | Protected area overlap |
| OWN-004 | Resolve `integrations/payment/` vs `integrations/payments/` | Production payment code; protected |
| OWN-005 | Update `docs/anchors/capability-resolution.md` | Protected anchor; content wrong |
| OWN-006 | Update `docs/anchors/doc-precedence.md` | Protected anchor; model obsolete |
| OWN-007 | Move `services/` to `_legacy/services/` (Phase D) | Code restructuring; import impact |
| OWN-008 | Merge/retire `integrations/payment/` | Production payment adapter |
| OWN-009 | D-001 through D-005 (U11 architectural questions) | Pre-existing open decisions |
