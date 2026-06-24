# LEGACY_AND_ARCHIVE_PLAN

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Source: FULL REPOSITORY NORMALIZATION AND REALITY AUDIT.md
Companion: REPOSITORY_NORMALIZATION_REPORT.md, ROOT_LEVEL_CLEANUP_PLAN.md

---

## PURPOSE

Document all legacy code and documentation identified in this audit, provide classification rationale, and define a staged plan for reclassification or retirement. Nothing is deleted without explicit owner approval.

---

## LEGACY IDENTIFICATION CRITERIA

A code directory or file is classified LEGACY when it meets **two or more** of:
1. Functionality duplicated by a more complete implementation elsewhere in the repository
2. Naming convention diverges from canonical names (service-manifest.json or DOCUMENTATION_COVERAGE_MATRIX.md)
3. No HTTP layer / not independently deployable
4. No requirements.txt (not dependency-managed)
5. Superseded by a later implementation with more files and richer structure
6. No README.md documenting current purpose

A documentation file is classified LEGACY when:
1. It carries a DEPRECATED or SUPERSEDED banner (already handled in prior phases)
2. It lives in a session archive or `_archive/` folder
3. It describes a system state that is demonstrably past (e.g., 60 services when there are 69)

---

## LEGACY CODE: ROOT LAYER SERVICES

### Classification: LIKELY LEGACY

| Directory | Services | Evidence |
|---|---|---|
| `services/` | 20 | All 6 legacy criteria met (see below) |

**Evidence:**

1. **Duplicated elsewhere:** Every service concept in `services/` has a counterpart in `backend/services/` (e.g., `services/config-service/` → `backend/services/config-service/`).

2. **Naming diverges from canonical:** Root service names use legacy forms:
   - `services/media-pipeline/` → canonical is `media-service` (service-manifest.json)
   - `services/offline-sync/` → canonical is `offline-sync-service`
   - `services/interaction-service/` → canonical is `interaction-layer-service`
   - `services/commerce/` → canonical is `checkout-service`
   - `services/academy-ops/` → canonical is `academy-commerce-service`

3. **No HTTP layer:** Each service has `models.py`, `service.py`, `__init__.py` — no FastAPI router, no main.py, no uvicorn entry point.

4. **No requirements.txt:** Root services cannot be deployed as standalone Python services.

5. **Superseded by richer implementation:** `backend/services/` has `app/`, `tests/`, `events/`, `migrations/` — a complete microservice structure vs. the minimal 2–3 file root layer.

6. **No README.md:** None of the 20 root services has a README.md.

### Legacy Classification Table (Root `services/`)

| Root Service | Canonical Replacement | Files | Status |
|---|---|---|---|
| `services/academy-ops/` | `backend/services/academy-commerce-service/` | 6 | LIKELY LEGACY |
| `services/analytics-service/` | `backend/services/analytics-service/` | 5 | LIKELY LEGACY |
| `services/capability-registry/` | `backend/services/capability-registry/` | 6 | LIKELY LEGACY |
| `services/commerce/` | `backend/services/checkout-service/` | 12 | LIKELY LEGACY |
| `services/config-service/` | `backend/services/config-service/` | 4 | LIKELY LEGACY |
| `services/enterprise-control/` | `backend/services/enterprise-control-service/` | N/A | LIKELY LEGACY |
| `services/entitlement-service/` | `backend/services/entitlement-service/` | N/A | LIKELY LEGACY |
| `services/exam-engine/` | `backend/services/exam-engine/` | N/A | LIKELY LEGACY |
| `services/file-storage/` | `backend/services/file-storage/` (or media-service) | N/A | LIKELY LEGACY |
| `services/integration-service/` | `backend/services/integration-service/` | N/A | LIKELY LEGACY |
| `services/interaction-service/` | `backend/services/interaction-layer-service/` | N/A | LIKELY LEGACY |
| `services/media-pipeline/` | `backend/services/media-service/` | N/A | LIKELY LEGACY |
| `services/media-security/` | `backend/services/media-security-service/` | N/A | LIKELY LEGACY |
| `services/notification-service/` | `backend/services/notification-service/` | N/A | LIKELY LEGACY |
| `services/offline-sync/` | `backend/services/offline-sync-service/` | N/A | LIKELY LEGACY |
| `services/onboarding/` | `backend/services/onboarding-service/` | N/A | LIKELY LEGACY |
| `services/operations-os/` | `backend/services/operations-os-service/` | N/A | LIKELY LEGACY |
| `services/subscription-service/` | `backend/services/subscription-service/` | N/A | LIKELY LEGACY |
| `services/system-of-record/` | `backend/services/system-economics-service/` (or SOR) | N/A | LIKELY LEGACY |
| `services/workflow-engine/` | `backend/services/workflow-engine/` | N/A | LIKELY LEGACY |

**Important caveat:** "LIKELY LEGACY" means the structural evidence strongly suggests legacy status. Owner confirmation is required before any retirement action. If any root service is still imported at runtime, it is ACTIVE regardless of structural signals.

---

## LEGACY CODE: ROOT LAYER SHARED LIBRARY

### Classification: NEEDS-REVIEW (possibly active)

| Directory | Files | Key Content | Status |
|---|---|---|---|
| `shared/models/` | 49 | Data model definitions | NEEDS-REVIEW |
| `shared/utils/` | 4 | Utility functions | NEEDS-REVIEW |
| `shared/validation/` | 2 | Validation helpers | NEEDS-REVIEW |

**Unlike `services/`, `shared/` may be actively imported by `backend/services/`.** A library of 49 model files is large enough to be a significant dependency. This cannot be classified as legacy without import analysis.

**Owner action:** Run import analysis (see ROOT_LEVEL_CLEANUP_PLAN.md RLC-003).

---

## LEGACY CODE: ROOT LAYER INTEGRATIONS

### Classification: NEEDS-REVIEW

| Directory | Files | Content | Status |
|---|---|---|---|
| `integrations/communication/` | 10 | Messaging adapters | NEEDS-REVIEW |
| `integrations/identity/` | 2 | Identity provider adapters | NEEDS-REVIEW |
| `integrations/payment/` | 8 | Payment adapters | NEEDS-REVIEW |
| `integrations/payments/` | 26 | Payment processing | NEEDS-REVIEW |
| `integrations/storage/` | 5 | Storage adapters | NEEDS-REVIEW |

Similar analysis as `shared/` — integration adapters may be imported by the active service layer. The `payment/` vs `payments/` overlap is itself a legacy signal (see ROOT_LEVEL_CLEANUP_PLAN.md RLC-002).

---

## LEGACY DOCUMENTATION: ALREADY HANDLED

The following document legacy situations were resolved in prior audit phases and are documented here for completeness:

| Document | Classification | Resolution |
|---|---|---|
| `workspace/foundation/product-build-spec.md` | HIST (superseded) | SUPERSEDED banner added; points to PROJECT_CHARTER.md |
| `workspace/foundation/behavioral-spec.md` | HIST (superseded) | SUPERSEDED banner added; points to PRODUCT_WORKFLOWS.md + FEATURE_SCOPE.md |
| `docs/governance/doc-catalogue.md` | OBSOL (superseded) | SUPERSEDED notice added; points to DOCUMENT_INVENTORY.md + DCM |
| `docs/_archive/GEN_14_certificate_service.md` | RETD (duplicate) | Moved to archive; deprecation banner added |
| `docs/specs/auth-service-spec-v0.md` | RETD | DEPRECATED banner added |
| `docs/specs/tenant-service-spec-v0.md` | RETD | DEPRECATED banner added |
| `docs/specs/features/rbac-service-spec-v0.md` | RETD | DEPRECATED banner added |
| `workspace/ops/pending.md` | HIST | HISTORICAL reclassification note added |
| `workspace/ops/gap-register.md` | HIST | HISTORICAL reclassification note added |
| `docs/anchors/capability-resolution.md` | STALE (pending) | Awaiting owner: 6-level → 4-level fix |
| `docs/anchors/doc-precedence.md` | OBSOL (pending) | Awaiting owner: BATCH model → TIER 0–5 |

---

## STAGED RETIREMENT PLAN: ROOT SERVICES LAYER

### Phase A: Confirmation (Owner Required)

**Prerequisite for all subsequent phases.**

Owner must confirm:
1. Which (if any) root services/ directories are still imported at runtime
2. Whether root shared/ models are imported by backend/services/
3. Whether root integrations/ adapters are imported by backend/services/

**Method:** Import search:
```bash
grep -r "from services\." backend/ --include="*.py"
grep -r "import services\." backend/ --include="*.py"
grep -r "from shared\." backend/ --include="*.py"
grep -r "from integrations\." backend/ --include="*.py"
```

### Phase B: Classification (AI Can Execute After Phase A)

After import analysis:

**If no backend/ imports found:**
- Mark all root services/ as LEGACY (add LEGACY banner to each service's README.md)
- Mark shared/ models as LEGACY
- Mark integrations/ as LEGACY

**If some backend/ imports found:**
- Mark importing services as ACTIVE
- Mark non-imported services as LEGACY
- Document import graph in a new LAYER_ARCHITECTURE.md

### Phase C: Documentation (AI Can Execute)

For each LEGACY-classified directory: create README.md with:
```markdown
# <service-name> — LEGACY

Status: LEGACY
Last active: [date of last git commit to this directory]

This service module was part of the pre-FastAPI platform layer.
It has been superseded by: backend/services/<canonical-name>/

This directory is retained for audit trail purposes.
Do not import this module in new code.
```

### Phase D: Archival (Owner Approval Required)

Long-term: retire legacy root services by moving to a `_legacy/` directory:
```
services/ → _legacy/services/
```

**This phase requires explicit owner approval.** Do not execute without sign-off.

---

## PRIORITY MATRIX

| Layer | Current Status | Risk If Active | Risk If Legacy | Priority |
|---|---|---|---|---|
| `services/` | LIKELY LEGACY | High (silent bugs) | Low (just clutter) | HIGH — classify first |
| `shared/models/` | NEEDS-REVIEW | Critical (break backend) | Low | HIGH — verify imports |
| `integrations/` | NEEDS-REVIEW | Medium (wrong adapter) | Low | MEDIUM |
| `validation/`, `scripts/` | NEEDS-REVIEW | Low | None | LOW |
