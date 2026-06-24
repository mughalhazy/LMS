# DUPLICATION_ANALYSIS_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Purpose: Identify all duplicate definitions, architecture descriptions, workflow descriptions, entity definitions, permission definitions, registers, and inventories across 355 documents.

---

## SEVERITY CLASSIFICATION

- **Critical** — Two documents both claim to be the authority on the same topic; consumers cannot determine which is correct
- **High** — Significant content duplication; risk of divergence; one should be suppressed
- **Medium** — Partial duplication; supporting docs overlap; manageable with cross-references
- **Low** — Minor overlap; cosmetic or structural duplication; acceptable with notes

---

## CRITICAL DUPLICATIONS

### DUP-C-001: Certificate Service Spec Duplicate File

**Documents:** docs/specs/GEN_14_certificate_service.md AND docs/specs/certificate-service-spec.md

**Issue:** GEN_14_certificate_service.md covers the same service as certificate-service-spec.md. The GEN_14 prefix is a legacy artifact from the original BATCH document naming convention. Both files exist in the active specs/ directory without deprecation marking.

**Risk:** Any consumer searching for the certificate service spec may read the GEN_14 version and not realize a canonical replacement exists.

**Resolution:** Retire docs/specs/GEN_14_certificate_service.md to docs/_archive/. Add deprecation notice in the file header. certificate-service-spec.md is authoritative.

---

### DUP-C-002: Service Inventory — Three Competing Sources

**Documents:**
1. docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md
2. docs/governance/doc-catalogue.md (v7.3)
3. docs/architecture/service-map.md

**Issue:** All three claim to inventory platform services. DOCUMENTATION_COVERAGE_MATRIX.md (new governance) has 69 services, correct canonical names, and updated counts. doc-catalogue.md has older service names and predates the governance framework. service-map.md may have pre-remediation service names.

**Risk:** Any consumer not reading DOCUMENTATION_COVERAGE_MATRIX.md may get wrong service counts or names.

**Resolution:**
- DOCUMENTATION_COVERAGE_MATRIX.md is authoritative (DOMAIN 19 in AUTHORITY_MAPPING_MATRIX.md)
- doc-catalogue.md: add deprecation notice; classify as OBSOL
- service-map.md: add note that DOCUMENTATION_COVERAGE_MATRIX.md is now canonical for service inventory

---

### DUP-C-003: Document Precedence — Two Conflicting Models

**Documents:**
1. docs/anchors/doc-precedence.md (BATCH > SPEC > ARCH > Legacy)
2. AUTHORITY_MAPPING_MATRIX.md §AUTHORITY_TIER_PRECEDENCE (TIER 0–5 model)

**Issue:** The doc-precedence.md anchor was written before docs/00_authority/ existed. Its BATCH naming convention no longer corresponds to any files in the repository. The new 5-tier model (TIER 0 = Governance Authority being highest) is not reflected in doc-precedence.md. Consumers reading doc-precedence.md would apply the wrong precedence model.

**Risk:** High — AI sessions or maintainers reading doc-precedence.md would resolve conflicts incorrectly, placing SPEC docs above GOVERNANCE docs when the opposite is true.

**Resolution:** Update docs/anchors/doc-precedence.md to adopt the TIER 0–5 model. Requires owner approval (anchor = protected area). Until updated, AUTHORITY_MAPPING_MATRIX.md TIER model is operative.

---

## HIGH DUPLICATIONS

### DUP-H-001: Config Resolution Hierarchy — Five Documents

**Documents:**
1. docs/anchors/capability-resolution.md (6 levels: plan + runtime_override — INCORRECT)
2. docs/00_authority/DOMAIN_MODEL.md (4 levels — CORRECT, post-remediation)
3. docs/00_authority/PROJECT_CHARTER.md §5 (4 levels — CORRECT)
4. docs/00_authority/ADR-001_PROJECT_FOUNDATION.md Decision 3 (4 levels — CORRECT)
5. docs/00_authority/PRODUCT_WORKFLOWS.md WF-009 (4 levels — CORRECT)

**Issue:** The config hierarchy is defined in 5 places. 4 of them are now correct (4 levels) after remediation. capability-resolution.md still documents the wrong 6-level hierarchy because it is a protected anchor.

**Risk:** capability-resolution.md is the canonical anchor. Any consumer reading the anchor directly gets the wrong hierarchy.

**Resolution:** Update capability-resolution.md (owner approval required). Add AI_OPERATING_CONTEXT.md NOTE cross-reference to all 5 docs (already done for 4; anchor doc still pending). After anchor update, recommend cross-reference consolidation (all other docs point to anchor instead of repeating the hierarchy).

---

### DUP-H-002: Domain Model — Three Documents

**Documents:**
1. docs/00_authority/DOMAIN_MODEL.md (authoritative — 9 bounded contexts, post-remediation)
2. docs/architecture/domain-driven-design-map.md (DDD map — may have older bounded contexts)
3. docs/architecture/microservice-boundary-map.md (boundary map — may have pre-remediation service assignments)

**Issue:** Domain model content is present in three places. The DDD map and boundary map may contain older definitions (pre-remediation) that conflict with DOMAIN_MODEL.md.

**Risk:** Medium-high — these are supporting docs (SUPP) so they don't compete for authority, but a developer reading them without knowing to check DOMAIN_MODEL.md could implement against stale definitions.

**Resolution:** Add deprecation/supersession notes to domain-driven-design-map.md and microservice-boundary-map.md headers pointing to DOMAIN_MODEL.md as the authority. Do not delete — retain as supporting detail.

---

### DUP-H-003: Data Ownership Rules — Two Documents

**Documents:**
1. docs/designs/data-ownership-rules.md
2. docs/architecture/service-data-ownership-rules.md

**Issue:** Both documents define data ownership rules per service. Unclear if they are identical, complementary, or divergent. Both exist without cross-reference to each other or to DOMAIN_MODEL.md §4 which is now the governing authority for service-to-data ownership.

**Risk:** Developers may use either as the authority, potentially getting different answers.

**Resolution:** Verify content. Add cross-references in both pointing to DOMAIN_MODEL.md §4 as the authority. Assess whether one can be retired. If divergent: add notes explaining the distinction.

---

### DUP-H-004: Architectural Principles — Two Presentations

**Documents:**
1. docs/00_authority/PROJECT_CHARTER.md §9
2. docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md

**Issue:** The 8 architectural principles appear in both documents. This was intentional (they share the same list per remediation), but any future update to either document must be applied to both to avoid divergence.

**Risk:** Low-medium (currently aligned; divergence risk is future-tense).

**Resolution (already applied):** Both documents include a canonical cross-reference note. Maintain by updating both whenever principles change. Long-term: project charter should reference ADR-001 as authoritative for principles, not repeat them.

---

### DUP-H-005: Former Master Spec vs Current Governance Authority

**Documents:**
1. workspace/foundation/product-build-spec.md (former Master Spec — HIST)
2. docs/00_authority/PROJECT_CHARTER.md (current authority)

**Issue:** product-build-spec.md was the primary authority before the governance framework was established. It may still be referenced by some architecture docs (core-system-architecture.md references "Master Spec §0.1"). It is classified HIST but has no deprecation banner.

**Risk:** Medium — any document that still references "Master Spec §0.1" is pointing to a superseded authority.

**Resolution:** Add deprecation banner to product-build-spec.md pointing to PROJECT_CHARTER.md. Grep for "Master Spec" references across docs/ and update cross-references to point to PROJECT_CHARTER.md.

---

### DUP-H-006: Retired v0 Specs Without Deprecation Banners

**Documents:**
1. docs/specs/auth-service-spec-v0.md
2. docs/specs/tenant-service-spec-v0.md
3. docs/specs/features/rbac-service-spec-v0.md

**Issue:** These files exist in active spec directories (not in _archive/) without explicit deprecation banners. A consumer scanning the specs/ directory may read them as current.

**Risk:** Medium — wrong API definitions could be implemented.

**Resolution:** Add deprecation banners to all three v0 files per the standard from doc-precedence.md. Do not move — the -v0.md naming convention is the signal; banner reinforces it.

---

## MEDIUM DUPLICATIONS

### DUP-M-001: Doc-to-Code Delta Reports — Two Generations

**Documents:**
1. workspace/sessions/U6/DOC_CODE_DELTA_REPORT.md (June 2026)
2. workspace/audit/doc-code-audit-2026-05-31.md (May 2026)
3. workspace/audit/catalogue-anchored-audit-2026-05-31.md (May 2026)

**Issue:** Multiple doc-to-code delta reports from different time windows. They track overlapping problem sets.

**Risk:** Low — all are HIST; no one should be using them as implementation authorities.

**Resolution:** No action required. All three are HIST; cross-reference in SESSION_NOTES only.

---

### DUP-M-002: QC Validation Reports — Overlapping Coverage

**Documents:** docs/qc/end-to-end-system-validation-report.md AND docs/qc/end-to-end-validation-report.md

**Issue:** Two end-to-end validation reports exist with similar names. Unclear if they cover different scope or are near-duplicates.

**Risk:** Low — both are RPT (historical); neither is authoritative.

**Resolution:** Verify if they cover different system scope. If essentially duplicate, add a note on the older one pointing to the newer. No deletion.

---

### DUP-M-003: Capability Inventory — Two References

**Documents:**
1. docs/specs/capability-inventory.md
2. docs/specs/capability-domain-map.md

**Issue:** Both documents cover capability inventory content. capability-inventory.md is the full list; capability-domain-map.md maps capabilities to domains. They are complementary but may duplicate the capability list.

**Risk:** Low — both are SUPP and clearly serve different functions (list vs. mapping).

**Resolution:** Ensure cross-references between the two. Both remain as SUPP.

---

### DUP-M-004: Session Classification Work Duplicates This Output

**Documents:**
1. workspace/sessions/U2/DOCUMENT_CLASSIFICATION_MATRIX.md (pre-governance, June 2026)
2. docs/08_reports/DOCUMENT_CLASSIFICATION_MATRIX.md (this session — post-governance)

**Issue:** U2 produced a classification matrix before the governance framework existed. This session produces a new one with the governance framework as context. Both exist simultaneously.

**Risk:** Low — U2 matrix is HIST; this session's matrix is the active one.

**Resolution:** U2 matrix remains HIST. No change needed, but sessions referencing classification should point to docs/08_reports/DOCUMENT_CLASSIFICATION_MATRIX.md.

---

### DUP-M-005: Normalization Reports

**Documents:**
1. workspace/sessions/U3/DOC_NORMALIZATION_REPORT.md (pre-governance normalization)
2. docs/08_reports/DOCUMENT_NORMALIZATION_REPORT.md (this session — post-governance)

**Issue:** Two normalization reports at different governance maturity levels.

**Risk:** None — U3 is HIST; this session's report is active.

**Resolution:** No action required.

---

## LOW DUPLICATIONS

### DUP-L-001: Architecture Cross-Document Repetition

Multiple architecture documents (core-system-architecture.md, multi-tenant-isolation-model.md, domain-driven-design-map.md) each contain a summary of the same layered architecture. This is expected and acceptable in supporting documents but creates maintenance risk if the architecture changes.

**Resolution:** Accept as supporting-document repetition. Add cross-reference notes to point to DOMAIN_MODEL.md and PROJECT_CHARTER.md as authoritative.

### DUP-L-002: Authentication Architecture Described in Multiple Places

docs/designs/auth-rsa-key-design.md, docs/architecture/security-architecture.md, and docs/specs/auth-service-spec.md all contain RS256 key management detail. ADR-001 Decision 5 is the policy authority.

**Resolution:** These are complementary at different levels of abstraction. Accept; add cross-references.

### DUP-L-003: Tenant Payload Definition

The 6-field tenant payload (tenant_id, name, country_code, segment_type, plan_type, addon_flags) appears in docs/anchors/tenant-contract.md (authority) and is repeated in docs/architecture/multi-tenant-isolation-model.md, docs/designs/tenant-extension-model.md, and docs/00_authority/DOMAIN_MODEL.md.

**Resolution:** Acceptable repetition in supporting docs. Each supporting doc should reference tenant-contract.md as the authority.

---

## DUPLICATION SUMMARY

| ID | Severity | Domain | Action Required | Owner |
|---|---|---|---|---|
| DUP-C-001 | Critical | Certificate spec duplicate | Retire GEN_14_certificate_service.md to _archive/ | AI |
| DUP-C-002 | Critical | Service inventory — 3 sources | Add deprecation to doc-catalogue.md; note on service-map.md | AI |
| DUP-C-003 | Critical | Document precedence model | Update doc-precedence.md to TIER 0–5 model | Owner (anchor) |
| DUP-H-001 | High | Config resolution hierarchy | Update capability-resolution.md (owner); add cross-refs | Owner (anchor) |
| DUP-H-002 | High | Domain model — 3 docs | Add supersession notes to DDD map and boundary map | AI |
| DUP-H-003 | High | Data ownership rules | Verify + cross-reference to DOMAIN_MODEL.md §4 | AI |
| DUP-H-004 | High | Architectural principles | Maintain sync; long-term: PROJECT_CHARTER references ADR-001 | AI (future) |
| DUP-H-005 | High | Master Spec vs governance | Add deprecation banner to product-build-spec.md | AI |
| DUP-H-006 | High | v0 spec files without banners | Add deprecation banners to 3 v0 files | AI |
| DUP-M-001 | Medium | Delta reports | No action (all HIST) | — |
| DUP-M-002 | Medium | E2E validation reports | Verify scope; note on older | AI |
| DUP-M-003 | Medium | Capability inventory | Ensure cross-references | AI |
| DUP-M-004 | Medium | Classification matrix | No action (U2 is HIST) | — |
| DUP-M-005 | Medium | Normalization report | No action (U3 is HIST) | — |
| DUP-L-001 | Low | Architecture repetition | Add cross-reference notes | AI |
| DUP-L-002 | Low | Auth architecture | Add cross-references | AI |
| DUP-L-003 | Low | Tenant payload | Add cross-references | AI |
