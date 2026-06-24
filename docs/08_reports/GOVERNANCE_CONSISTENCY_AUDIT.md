# GOVERNANCE_CONSISTENCY_AUDIT

Status: Active
Authority Level: High
Last Reviewed: 2026-06-21
Owner: AI
Source: PHASE 1 GOVERNANCE VALIDATION.md

---

## Scope

Cross-document consistency audit across all 7 Phase 1 governance documents:

| Document | Status | Authority |
|---|---|---|
| docs/00_authority/PROJECT_CHARTER.md | Active | Critical |
| docs/00_authority/FEATURE_SCOPE.md | Active | High |
| docs/00_authority/DOMAIN_MODEL.md | Active | Critical |
| docs/00_authority/PRODUCT_WORKFLOWS.md | Active | High |
| docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md | **Draft** | High |
| docs/07_governance/AI_OPERATING_CONTEXT.md | Active | Critical |
| docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md | Active | Critical |

Audit checks: contradictions, duplicate definitions, missing terminology, inconsistent naming, workflow mismatches, domain entity mismatches, feature scope mismatches, architectural assumption conflicts.

---

## CRITICAL Issues

Issues that directly compromise the accuracy of an authority document or will cause implementation errors.

---

### GCA-C-001: ADR-001 implementation description omits PLAN level from config hierarchy

**Type:** Contradiction + Architectural assumption conflict
**Documents:** ADR-001_PROJECT_FOUNDATION.md vs all other docs
**Evidence:**

ADR-001 Decision 6:
> Implementation: services/config-service/service.py (4-level ConfigLevel enum: GLOBAL, COUNTRY, SEGMENT, TENANT)

All other documents define a 5-level hierarchy:
- PROJECT_CHARTER §9 Principle 2: `global → country → segment → plan → tenant`
- AI_OPERATING_CONTEXT FROZEN_DECISIONS: `global→country→segment→plan→tenant`
- PRODUCT_WORKFLOWS WF-009: `global → country → segment → plan → tenant (deep-merge)`
- DOMAIN_MODEL §4: `global → country → segment → plan → tenant → runtime_override (optional)`

**Impact:** ADR-001's implementation claim (4-level enum: GLOBAL, COUNTRY, SEGMENT, TENANT) excludes PLAN. If accurate, the config-service does not implement plan-level config isolation, which would mean all plan-differentiated capabilities resolve incorrectly. If inaccurate, ADR-001 is wrong. Either case is critical.

**Action required:** Verify services/config-service/service.py ConfigLevel enum. If PLAN exists: fix ADR-001. If PLAN does not exist: this is an implementation gap — config-service must be updated.

---

### GCA-C-002: ADR-001 Governance Session History records wrong output location for Governance Phase 1

**Type:** Factual error
**Documents:** ADR-001_PROJECT_FOUNDATION.md
**Evidence:**

ADR-001 Governance Session History table:
> Governance Phase 1 | 2026-06-21 | **workspace/sessions/GOVERNANCE-P1/**

Actual output location: The 12 Governance Phase 1 documents were written to:
- `docs/00_authority/` (5 documents)
- `docs/06_decisions/` (1 document)
- `docs/07_governance/` (2 documents)
- `docs/08_reports/` (4 documents)

No `workspace/sessions/GOVERNANCE-P1/` directory exists.

**Impact:** Any navigation instruction referencing `workspace/sessions/GOVERNANCE-P1/` will fail. The governance session history is incorrect in an authority document.

**Action required:** Update ADR-001 session history row to reference the actual `docs/` output locations.

---

### GCA-C-003: AI_OPERATING_CONTEXT backend service count is ambiguous — "67 services" vs "69 HTTP"

**Type:** Internal contradiction within AI_OPERATING_CONTEXT
**Documents:** AI_OPERATING_CONTEXT.md
**Evidence:**

AI_OPERATING_CONTEXT FROZEN_DECISIONS table, two different rows:
- Row 1: `Backend language | Python (FastAPI) | Repo/backend/services/ **(67 services)**`
- Row 2: `Service count | **72 total: 69 HTTP + 3 class-based** | service-manifest.json + U10`

Row 1 says 67 backend services. Row 2 says 69 HTTP. These cannot both be complete counts of the same thing.

The actual breakdown (per ADR-001 and U10): 67 Python/FastAPI + 2 Node.js = 69 HTTP total + 3 class-based = 72 manifest-registered.

**Impact:** A new AI session reading AI_OPERATING_CONTEXT — which is specifically designed to be loaded first — will see "67 services" in the frozen decisions table and 69 elsewhere. This is the highest-traffic governance document and the inconsistency will propagate to any session that relies on it.

**Action required:** Change Row 1 to read: `Backend language | Python (FastAPI) | Repo/backend/services/ (67 Python/FastAPI + 2 Node.js = 69 HTTP total)` or align with Row 2's "69 HTTP" phrasing.

---

## HIGH Issues

Issues that create domain model gaps or naming inconsistencies that will confuse implementers.

---

### GCA-H-001: "media-service" (FEATURE_SCOPE) vs "media-pipeline" (DOCUMENTATION_COVERAGE_MATRIX) — different names for the same service

**Type:** Inconsistent naming
**Documents:** FEATURE_SCOPE.md vs DOCUMENTATION_COVERAGE_MATRIX.md
**Evidence:**

FEATURE_SCOPE §1.11: `Media management | **media-service**, media-security-service | backend/services/`
DOCUMENTATION_COVERAGE_MATRIX (specced list): `**media-pipeline** | docs/specs/media-pipeline-spec.md`

"media-service" and "media-pipeline" are used to refer to what appears to be the same backend service. The spec file name (media-pipeline-spec.md) implies the canonical service name is "media-pipeline", not "media-service".

**Impact:** Implementers writing tests, specs, or manifests for this service will use inconsistent names.

**Action required:** Verify service-manifest.json and backend/services/ directory — determine canonical name. Update FEATURE_SCOPE to use the canonical name.

---

### GCA-H-002: "system-economics" vs "system-economics-service" — one or two services?

**Type:** Inconsistent naming / possible phantom duplication
**Documents:** FEATURE_SCOPE.md vs DOCUMENTATION_COVERAGE_MATRIX.md
**Evidence:**

DOCUMENTATION_COVERAGE_MATRIX (specced): `**system-economics** | docs/specs/system-economics-spec.md`
DOCUMENTATION_COVERAGE_MATRIX (unspecced): `**system-economics-service** | ❌ NO SPEC`
FEATURE_SCOPE §1.11: `System economics | **system-economics-service** | backend/services/system-economics-service/`

Three possible interpretations: (1) two distinct services exist, one specced and one not; (2) one service with inconsistent naming across documents; (3) "system-economics-service" in the unspecced list is a duplicate entry error.

**Impact:** If two services exist, both need documentation. If one, the naming must be standardized. An implementer reading FEATURE_SCOPE will look for system-economics-service; reading the coverage matrix they'll find system-economics with a spec — and won't know they're the same.

**Action required:** Verify backend/services/ — check whether system-economics/ and system-economics-service/ both exist. Reconcile naming in both documents.

---

### GCA-H-003: course-generation-service is in AI domain (DOMAIN_MODEL) but Learning Structure (FEATURE_SCOPE)

**Type:** Domain classification mismatch
**Documents:** DOMAIN_MODEL.md vs FEATURE_SCOPE.md
**Evidence:**

DOMAIN_MODEL §1: `AI domain → ai-tutor-service, recommendation-service, **course-generation-service**, skill-inference-service`
FEATURE_SCOPE §1.3 Learning Structure: `Course generation (AI) | **course-generation-service**`
FEATURE_SCOPE §1.10 AI Features: does NOT include course-generation-service

**Impact:** Domain ownership determines which team owns the service, which bounded context it participates in, and which aggregate roots it may read/write. Conflicting assignment breaks the single-ownership principle. Downstream: if course-generation-service is in AI domain, it may not have permission to write to Learning Structure aggregates directly.

**Action required:** Decide canonical domain. If AI: move to FEATURE_SCOPE §1.10 AI Features. If Learning Structure: move to DOMAIN_MODEL Learning Structure domain. Update both documents consistently.

---

### GCA-H-004: review-service exists in code but has no DOMAIN_MODEL assignment or FEATURE_SCOPE entry

**Type:** Missing domain entity / feature scope gap
**Documents:** FEATURE_SCOPE.md, DOMAIN_MODEL.md vs DOCUMENTATION_COVERAGE_MATRIX.md
**Evidence:**

DOCUMENTATION_COVERAGE_MATRIX (unspecced): `review-service | ❌ NO SPEC`
DOMAIN_MODEL §1: no mention of review-service
FEATURE_SCOPE: no mention of review-service in any section

**Impact:** A service exists in the codebase (presumably backend/services/review-service/) that has no documented domain ownership, no feature definition, and no architectural assignment. Governance cannot apply to it.

**Action required:** Identify what review-service does (read its service entry in service-manifest.json and backend/services/review-service/). Add to the appropriate DOMAIN_MODEL bounded context and add a FEATURE_SCOPE entry.

---

### GCA-H-005: Course completion ownership unassigned — violates single system of record principle

**Type:** Workflow mismatch / principle violation
**Documents:** PRODUCT_WORKFLOWS.md, DOMAIN_MODEL.md, ADR-001_PROJECT_FOUNDATION.md
**Evidence:**

PRODUCT_WORKFLOWS WF-004 step 6:
> Course completion detected → **enrollment-service or progress-service**

ADR-001 Architectural Principle 1:
> Single system of record — one service owns each entity; no dual writes

DOMAIN_MODEL §1 Learning Runtime: both enrollment-service and progress-service are listed.

"Or" is incompatible with "single system of record". Course completion detection must have exactly one authoritative owner.

**Impact:** Without a designated owner, dual-write risk is real — an enrollment event and a progress event could both trigger certificate issuance, resulting in duplicate certificates.

**Action required:** Assign course completion ownership to either enrollment-service or progress-service. Document the owner in DOMAIN_MODEL §2 alongside the other frozen entities. Update WF-004 to remove "or".

---

### GCA-H-006: Architectural principles are defined twice with different content and ordering

**Type:** Duplicate definitions / no canonical list
**Documents:** PROJECT_CHARTER.md §9 vs ADR-001_PROJECT_FOUNDATION.md Architectural Principles
**Evidence:**

PROJECT_CHARTER §9 lists 8 principles in this order:
1. Tenant-first isolation
2. Config resolution hierarchy
3. Capability resolution sequence
4. Single system of record
5. Event-driven decoupling
6. RS256 JWT standard
7. Pakistan-first commerce
8. Domain/HTTP separation

ADR-001 Architectural Principles lists 8 principles in different order with different wording:
1. Single system of record
2. Tenant isolation
3. No runtime branching on tenant discriminators (MS-CONFIG-01)
4. Fixed capability resolution sequence
5. Canonical event envelope
6. RS256 JWT everywhere
7. Domain/HTTP separation
8. Pakistan-first, globally extensible

Differences:
- PROJECT_CHARTER §9 P2 "Config resolution hierarchy" ≠ ADR-001 P3 "No runtime branching on tenant discriminators" — these are related but different concepts
- PROJECT_CHARTER §9 P5 "Event-driven decoupling" ≠ ADR-001 P5 "Canonical event envelope" — one is about coupling strategy, one is about structure
- ADR-001 P3 explicitly cites MS-CONFIG-01; PROJECT_CHARTER §9 only mentions it as a sub-note to Principle 2

**Impact:** No canonical list of principles. Future AI sessions will cite different principles depending on which document they read first.

**Action required:** Consolidate into a single canonical list. Decide whether PROJECT_CHARTER or ADR-001 is the authority for principles. The other document should reference rather than redefine.

---

### GCA-H-007: DOMAIN_MODEL includes runtime_override as a 6th config layer; all other documents stop at tenant (5 layers)

**Type:** Contradiction / undefined concept
**Documents:** DOMAIN_MODEL.md §4 vs PROJECT_CHARTER, ADR-001, AI_OPERATING_CONTEXT, PRODUCT_WORKFLOWS
**Evidence:**

DOMAIN_MODEL §4 Config hierarchy:
> global → country → segment → plan → tenant → **runtime_override (optional)**

All other documents: `global → country → segment → plan → tenant` (5 layers; no runtime_override)

"runtime_override" is not defined anywhere in the 7 governance documents:
- Not in ADR-001 (which documents all foundational decisions)
- Not in AI_OPERATING_CONTEXT (which lists all frozen decisions)
- Not in docs/anchors/capability-resolution.md (referenced canonical source)
- No service is identified as applying runtime overrides
- No trigger condition or override mechanism is described

**Impact:** Either runtime_override is a real 6th layer that has been omitted from ADR-001 and all other docs (significant governance gap), or DOMAIN_MODEL erroneously added a concept that does not exist (documentation error). Either case corrupts the config hierarchy specification.

**Action required:** Determine if runtime_override is implemented in config-service. If yes: add it to ADR-001 Decision 6 and AI_OPERATING_CONTEXT FROZEN_DECISIONS with a definition. If no: remove from DOMAIN_MODEL §4.

---

## MEDIUM Issues

Issues that create confusion without directly causing implementation errors.

---

### GCA-M-001: BC-INT-02, BC-BILLING-01, CGAP-041 — internal codes referenced but undefined in governance docs

**Type:** Missing terminology
**Documents:** PRODUCT_WORKFLOWS.md, FULLSTACK_STITCHING_CONTRACT.md
**Evidence:**

PRODUCT_WORKFLOWS WF-007: `BC-INT-02: persona-based command shortcuts`
FULLSTACK_STITCHING_CONTRACT FSC-007: `_emit_upsell_trigger() function with BC-BILLING-01/CGAP-041 (from U10)`

These codes are defined in U6/U7 finding registers (workspace/sessions/), not in any governance document. A reader of the governance docs cannot look up what these codes mean without leaving the docs system.

**Action required:** Either define the codes inline in the referencing documents, or replace with descriptive text. Example: replace "BC-INT-02" with "persona-based command shortcuts (ref: U6 B-INT-02)".

---

### GCA-M-002: GEB codes referenced in AI_OPERATING_CONTEXT but not defined in governance docs

**Type:** Missing terminology
**Documents:** AI_OPERATING_CONTEXT.md
**Evidence:**

AI_OPERATING_CONTEXT CURRENT_PHASE:
> Cannot proceed to Phase 1 implementation until: 8 governance blockers (GEB-001 through GEB-008) resolved

GEB (Governance Entry Blocker) codes are defined only in `workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md`. AI_OPERATING_CONTEXT does not include the blocker list or link to the definitions.

**Impact:** A new AI session reading AI_OPERATING_CONTEXT cannot determine what the 8 blockers are without loading the U11 document.

**Action required:** Add a summary table of GEB-001 through GEB-008 to AI_OPERATING_CONTEXT, or add the U11 blockers document explicitly to ACTIVE_AUTHORITY_DOCS.

---

### GCA-M-003: "Runtime orchestrator" referenced in DOMAIN_MODEL and PRODUCT_WORKFLOWS but not defined as a service

**Type:** Undefined entity
**Documents:** DOMAIN_MODEL.md §4, PRODUCT_WORKFLOWS.md WF-009
**Evidence:**

DOMAIN_MODEL §4 Ownership table:
> Final state assembly | **Runtime orchestrator** (never registry/config/entitlement internals)

PRODUCT_WORKFLOWS WF-009 step 5:
> Assemble final_state → **Runtime orchestrator** (never registry/config/entitlement internals)

"Runtime orchestrator" has no service name, no mapping to a backend service, no domain assignment, and no entry in FEATURE_SCOPE or DOMAIN_MODEL bounded contexts.

**Action required:** Define what "runtime orchestrator" means: is it the calling service (i.e., whatever service is initiating the entitlement check)? If so, say "calling service / API handler". If it is a specific service, name it.

---

### GCA-M-004: "interaction-service" vs "interaction-layer" — two names, unclear if same

**Type:** Inconsistent naming
**Documents:** DOCUMENTATION_COVERAGE_MATRIX.md vs U10 service inventory
**Evidence:**

DOCUMENTATION_COVERAGE_MATRIX specced: `interaction-layer | docs/specs/interaction-layer-spec.md`
U10 classification (in session summary): `services/interaction-service/ — ORPHANED`
FEATURE_SCOPE: does not mention interaction-service or interaction-layer

Is services/interaction-service/ the same as what interaction-layer-spec.md specifies? Or is the spec for backend/services/interaction-layer/ (if it exists)?

**Action required:** Verify backend/services/ and services/ directories. Establish whether these are the same service with inconsistent names, or two different things. Update FEATURE_SCOPE to include whichever one(s) is in scope.

---

### GCA-M-005: "interaction-service" and "review-service" absent from FEATURE_SCOPE despite existing in codebase

**Type:** Feature scope gap
**Documents:** FEATURE_SCOPE.md vs DOCUMENTATION_COVERAGE_MATRIX.md
**Evidence:**

DOCUMENTATION_COVERAGE_MATRIX lists both services (one specced, one unspecced) but neither appears in FEATURE_SCOPE's 11 feature groups. No explanation is given for why these services are excluded.

**Action required:** Determine if these services are in scope (add to FEATURE_SCOPE) or out of scope (add explicitly to FEATURE_SCOPE §3 "Out of Scope").

---

### GCA-M-006: Config hierarchy layer count — DOMAIN_MODEL says 6, everything else says 5

This is the sub-issue from GCA-H-007. Medium severity sub-point: even within the 5-layer consensus, DOMAIN_MODEL's (optional) qualifier creates ambiguity about whether 5 layers must always execute or 6 can.

**Documents:** DOMAIN_MODEL.md §4
**Action required:** Resolved by GCA-H-007 fix.

---

### GCA-M-007: PROJECT_CHARTER current phase description ambiguous vs AI_OPERATING_CONTEXT

**Type:** Inconsistent status description
**Documents:** PROJECT_CHARTER.md §6 vs AI_OPERATING_CONTEXT.md
**Evidence:**

PROJECT_CHARTER §6: `Phase: Pre-Governance → Governance Entry (Phase 1)`
AI_OPERATING_CONTEXT: `Phase: Governance Entry (Phase 1 complete — implementation pending)`

PROJECT_CHARTER reads as if Phase 1 is in progress. AI_OPERATING_CONTEXT correctly states Phase 1 documentation is complete. A reader of PROJECT_CHARTER alone will not know the phase is already complete.

**Action required:** Update PROJECT_CHARTER §6 Current Phase to read: `Phase: Governance Entry (Phase 1 documentation complete; implementation pending — see GEB-001 through GEB-008)`.

---

### GCA-M-008: Service spec count inconsistency — "~45 of 69" vs "44/69"

**Type:** Internal inconsistency
**Documents:** DOCUMENTATION_COVERAGE_MATRIX.md
**Evidence:**

DOCUMENTATION_COVERAGE_MATRIX §3 header: `Specced: ~45 of 69 backend services`
DOCUMENTATION_COVERAGE_MATRIX Coverage Summary: `Service specs | 64% (44/69)`

64% × 69 = 44.16 → 44. The header says ~45. The count in the specced table (manually counted) shows 44 named entries.

**Action required:** Fix header to say `44 of 69` (or recount the specced list if a service was missed).

---

### GCA-M-009: "onboarding-service" in WF-001 but not assigned to any DOMAIN_MODEL bounded context

**Type:** Domain entity mismatch
**Documents:** PRODUCT_WORKFLOWS.md WF-001 vs DOMAIN_MODEL.md §1
**Evidence:**

PRODUCT_WORKFLOWS WF-001: `Services involved: ..., onboarding-service`
DOMAIN_MODEL §1: onboarding-service does not appear in Organization domain or Platform domain.
DOCUMENTATION_COVERAGE_MATRIX specced: `onboarding | docs/specs/onboarding-spec.md` (exists)

The service participates in a workflow but has no domain home.

**Action required:** Assign onboarding-service to a bounded context in DOMAIN_MODEL §1. Most naturally: Organization domain (provisioning flow) or Platform domain (cross-cutting).

---

## LOW Issues

Minor issues that do not affect correctness but reduce documentation quality.

---

### GCA-L-001: "offline-sync" vs "offline-sync-service" minor naming inconsistency

FEATURE_SCOPE §1.4 labels the domain-layer service "offline-sync-service" but U10 verified the directory is `services/offline-sync/` (no -service suffix). The backend service is `backend/services/offline-sync-service/`. Minor; correct in FEATURE_SCOPE by noting the domain-layer path.

---

### GCA-L-002: "Rails heritage" used in DOMAIN_MODEL without definition

DOMAIN_MODEL §2 header: "Core Runtime Entities (Rails Heritage — Frozen)" — the term "Rails heritage" is only explained in PROJECT_CHARTER §1 and ADR-001. A reader of DOMAIN_MODEL alone won't know what it means.

**Action required:** Add a one-sentence footnote: "Rails heritage refers to the original Rails LMS runtime (Enterprise LMS V2) whose core entities pre-date the Python microservices layer."

---

### GCA-L-003: "GEN_14" prefix in certificate-service spec filename — unexplained

DOCUMENTATION_COVERAGE_MATRIX references `docs/specs/GEN_14_certificate_service.md`. The "GEN_14" prefix comes from an internal document numbering scheme that is not explained in any governance document.

**Action required:** Low priority. Can document the naming scheme in a Phase 2 docs meta-doc, or simply note it's a legacy naming artifact.

---

### GCA-L-004: Service classification terminology used in PROJECT_CHARTER §4 but not defined in governance docs

PROJECT_CHARTER §4: "3 manifest-deployed, 5 active runtime, 10 duplicated, 2 orphaned" — these classifications are defined in `workspace/sessions/U10/U10_LMS_SERVICE_CLASSIFICATION_MATRIX.md` but not in any governance document. Readers may not know what "duplicated" means in this context.

**Action required:** Add inline definition or footnote: "'duplicated' = services/ entries whose domain logic is fully consumed by a corresponding backend/services/ service; not independently deployed."

---

### GCA-L-005: Principle duplication — config resolution hierarchy defined in 5 documents

Config resolution sequence `global → country → segment → plan → tenant` is defined identically (minus the runtime_override variance addressed in GCA-H-007) in: PROJECT_CHARTER §9, DOMAIN_MODEL §4, AI_OPERATING_CONTEXT, ADR-001, PRODUCT_WORKFLOWS WF-009. Every copy is a maintenance hazard.

**Action required:** Long-term: governance docs should reference `docs/anchors/capability-resolution.md` rather than repeating. For now: note the duplication and add cross-references.

---

### GCA-L-006: Tenant contract defined in both DOMAIN_MODEL §3 and docs/anchors/tenant-contract.md

DOMAIN_MODEL §3 reproduces the full tenant contract JSON. The canonical source is docs/anchors/tenant-contract.md. DOMAIN_MODEL should reference the anchor rather than duplicate it.

**Action required:** Low priority. Add a note: "Reproduced from docs/anchors/tenant-contract.md — anchor is canonical."

---

### GCA-L-007: HS256 exceptions listed with inconsistent detail levels

PROJECT_CHARTER §5: "HS256 — notification, subscription, catalog" (no finding IDs)
ADR-001 Decision 3: "notification-service (B05-002), subscription-service (B10-006), catalog-service" (with U6 finding IDs)

Minor: ADR-001 is more specific. PROJECT_CHARTER could add finding IDs for traceability.

---

### GCA-L-008: "CredentialProfile" aggregate root in DOMAIN_MODEL has no corresponding service

DOMAIN_MODEL §5 Identity Domain: "CredentialProfile (aggregate root)" — no service owns this in FEATURE_SCOPE §1.1 Identity and Access. Either it's owned by auth-service (unstated) or it's a phantom aggregate.

**Action required:** Assign CredentialProfile ownership explicitly in DOMAIN_MODEL §5 or FEATURE_SCOPE §1.1.

---

### GCA-L-009: Badge is classified as "(entity)" but has its own service — inconsistent DDD classification

DOMAIN_MODEL §5: "Badge (entity)" — not an aggregate root
FEATURE_SCOPE §1.5: "Badge issuance | badge-service" — a service exists for it

In DDD, if a service owns an object, that object is typically an aggregate root. Badge being classified as "(entity)" while having a dedicated service is inconsistent.

**Action required:** Evaluate whether Badge should be "(aggregate root)" or whether badge-service should be noted as a sub-service of certificate-service.

---

### GCA-L-010: "academy-ops" in DOMAIN_MODEL has no HTTP API noted — but is used in WF-002 and WF-006 as if callable

DOMAIN_MODEL §7: "academy-ops has no HTTP API — programmatic access only"
PRODUCT_WORKFLOWS WF-002 step 1: "Create branch → AcademyOpsService.create_branch(tenant_id, branch_data)"

The workflows show method calls which implies a calling party. WF-002/WF-006 don't specify who the caller is. FSC-006 correctly identifies academy-commerce-service as the HTTP wrapper. WF-002 should reference academy-commerce-service as the entry point.

---

### GCA-L-011: build_commerce_service_for_pakistan factory pattern undocumented in DOMAIN_MODEL

WF-005 references the factory but DOMAIN_MODEL Commerce section does not mention it. ADR-001 Decision 8 explains it. DOMAIN_MODEL should reference ADR-001 D8 or add a note about the factory pattern.

---

### GCA-L-012: FSC-003 and WF-005 list different sets of HTTP services for the checkout flow

WF-005 "Services involved": `academy-commerce-service (HTTP), services/commerce/ (domain), integrations/payments/, payment-service`

FSC-003 "Backend Component (HTTP)": `backend/services/checkout-service/, backend/services/payment-service/, backend/services/academy-commerce-service/`

WF-005 omits checkout-service from its services list; FSC-003 does not list integrations/payments/ directly. Minor coverage gap between the two.

---

### GCA-L-013: ParentGuardian user type in AI_OPERATING_CONTEXT quick reference — no domain entity or feature backing

AI_OPERATING_CONTEXT: "Parents — monitor student progress (TBD — REQUIRES VERIFICATION)"
DOMAIN_MODEL: no ParentGuardian entity
FEATURE_SCOPE: no parent monitoring feature

Correctly marked TBD, but should be noted for Phase 2 scope decision. Not an error — properly handled — but worth tracking.

---

### GCA-L-014: FULLSTACK_STITCHING_CONTRACT FSC-001 API Endpoint is "TBD" despite auth-service-spec.md existing

FSC-001 API Endpoint: "TBD — REQUIRES VERIFICATION (spec in docs/specs/auth-service-spec.md)"

The spec exists. The endpoint should be extractable from it. This is a gap in FSC population effort, not a fundamental unknown.

---

## Summary Table

| Severity | Count | Issues |
|---|---|---|
| CRITICAL | 3 | GCA-C-001, GCA-C-002, GCA-C-003 |
| HIGH | 7 | GCA-H-001 through GCA-H-007 |
| MEDIUM | 9 | GCA-M-001 through GCA-M-009 |
| LOW | 14 | GCA-L-001 through GCA-L-014 |
| **Total** | **33** | |

---

## Documents Ready to Move Draft → Active

| Document | Current Status | Recommendation | Reason |
|---|---|---|---|
| PROJECT_CHARTER.md | Active | **Remain Active** — fix GCA-C-002 in-place | Phase description needs update (GCA-M-007) |
| FEATURE_SCOPE.md | Active | **Remain Active** — fix HIGH issues | Missing services (GCA-H-004, GCA-M-005), naming (GCA-H-001, GCA-H-002, GCA-H-003) |
| DOMAIN_MODEL.md | Active | **Remain Active** — fix HIGH issues | runtime_override ambiguity (GCA-H-007), course completion ownership (GCA-H-005) |
| PRODUCT_WORKFLOWS.md | Active | **Remain Active** — fix GCA-H-005 | Remove "or" from WF-004 step 6 after owner assigns completion ownership |
| FULLSTACK_STITCHING_CONTRACT.md | **Draft** | **Remain Draft** | Frontend column entirely TBD; frontend audit required (Phase 2). Not eligible for Active until FSC frontend column is populated. |
| AI_OPERATING_CONTEXT.md | Active | **Remain Active** — fix GCA-C-003, GCA-M-002 | Critical service count error; GEB codes undefined |
| ADR-001_PROJECT_FOUNDATION.md | Active | **Remain Active** — fix GCA-C-001, GCA-C-002 | Config hierarchy missing PLAN level; wrong session history path |

**Net verdict on Draft → Active promotions: 0 promotions recommended.** FULLSTACK_STITCHING_CONTRACT.md is the only Draft document and is not eligible for Active until Phase 2 frontend audit is complete.

---

## Recommended Fix Priority

### Fix immediately (blocks accuracy of authority docs):

1. **GCA-C-001** — Verify ConfigLevel enum PLAN level; fix ADR-001 Decision 6
2. **GCA-C-002** — Fix ADR-001 Governance Session History location
3. **GCA-C-003** — Fix AI_OPERATING_CONTEXT backend service count row ("67 services")

### Fix before U12 implementation begins (blocks correct domain model):

4. **GCA-H-005** — Assign course completion ownership (enrollment-service or progress-service)
5. **GCA-H-007** — Resolve runtime_override: implement or remove from DOMAIN_MODEL
6. **GCA-H-003** — Assign course-generation-service to one domain (AI or Learning Structure)
7. **GCA-H-004** — Add review-service to DOMAIN_MODEL and FEATURE_SCOPE

### Fix during Phase 2 governance:

8. **GCA-H-001** — Reconcile media-service vs media-pipeline naming
9. **GCA-H-002** — Reconcile system-economics vs system-economics-service
10. **GCA-H-006** — Consolidate architectural principles into one canonical list
11. **GCA-M-001** — Replace opaque BC/CGAP codes with descriptive text
12. **GCA-M-002** — Add GEB blocker table to AI_OPERATING_CONTEXT
13. **GCA-M-003** — Define "runtime orchestrator" as a service or calling convention
14. **GCA-M-007** — Update PROJECT_CHARTER phase description
15. **GCA-M-008** — Fix service spec count ("~45" vs "44")
16. **GCA-M-009** — Assign onboarding-service to a bounded context

### Fix as available (LOW severity):

17–33. GCA-L-001 through GCA-L-014 — See individual action items above.

---

## Audit Completion

**Audit performed by:** AI (Phase 1 Governance Validation)
**Date:** 2026-06-21
**Source prompt:** PHASE 1 GOVERNANCE VALIDATION.md
**Output:** docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md
**Verdict:** 3 critical issues must be fixed before this document set can be considered consistent.
