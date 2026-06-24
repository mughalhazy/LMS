# Normalisation Tracker

**Scope:** 201 active .md files across 8 active folders (excludes 2 _archive folders, 3 archived files)
**Criteria:** Broken references · Stale content · Missing cross-references · Within-doc continuity breaks
**NOT in scope:** Gap filling · Destruction · Creation · Restructuring · Assumptions
**Status:** COMPLETE — all 201 files read; findings presented for review

---

## Folder Progress

| Folder | Files | Status |
|--------|-------|--------|
| docs/anchors/ | 5 | COMPLETE |
| docs/api/ | 8 | COMPLETE |
| docs/architecture/ | 78 active | COMPLETE |
| docs/data/ | 13 | COMPLETE |
| docs/integrations/ | 6 | COMPLETE |
| docs/market/ | 3 | COMPLETE |
| docs/qc/ | 27 | COMPLETE |
| docs/specs/ | 63 | COMPLETE |

---

## Findings Legend

| Code | Meaning |
|------|---------|
| BROKEN-REF | File reference points to wrong path or non-existent file |
| STALE | Within-doc content contradicts current known state |
| MISSING-XREF | Related doc exists but is not referenced where it should be |
| TRIM | Redundant section that duplicates a canonical anchor |
| CLEAN | No normalisation issues found |

---

## Folder 01 — docs/anchors/ (5 files) — COMPLETE

### event-envelope.md
**Status:** CLEAN
- Canonical 7-field schema (event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata)
- References DATA_02 and ARCH_05 as reconciled docs — correct

### doc-precedence.md
**Status:** CLEAN
- BATCH > SPEC > ARCH > Legacy priority order defined
- Deprecation banner standard defined

### capability-resolution.md
**Status:** CLEAN
- 184-line canonical anchor defining capability → config → entitlement → final_state resolution sequence
- Properly cross-references B2P01, B2P02, B2P05, B2P06

### country-layer-architecture.md
**Status:** CLEAN
- Canonical adapter-binding pattern for country layer
- QC alignment matrix with B7P reports present

### tenant-contract.md
**Status:** CLEAN
- Canonical 6-field tenant JSON model (tenant_id, name, country_code, segment_type, plan_type, addon_flags)
- Canonical naming resolution: display_name→name, enabled_addons→addon_flags

---

## Folder 02 — docs/api/ (8 files) — COMPLETE

### analytics-api.md
**Status:** MISSING-XREF (Finding #36)
- Has title "# Analytics API Endpoints", 4-row table stub
- No cross-references to analytics-service-spec.md, learning-analytics-spec.md, or AI_04

### api-contract-validation-report.md
**Status:** MISSING-XREF (Finding #37)
- Raw pipe table, no H1 title, no purpose statement, no cross-references

### api-gateway-design.md
**Status:** MISSING-XREF (Finding #38)
- Raw 5-row pipe table of gateway components, no H1 title, no cross-references

### api-spec-validation-report.md
**Status:** MISSING-XREF (Finding #39)
- Raw newline-separated text (no table), no H1 title, no cross-references

### auth-service-api.md
**Status:** MISSING-XREF (Finding #40)
- Has H1 title, substantive route table and schemas
- No cross-references to auth-service-spec.md or user-service-spec.md

### content-api.md
**Status:** MISSING-XREF (Finding #41)
- Raw text stub with 4 endpoint blocks, no H1 title, no cross-references

### core-rest-api.md
**Status:** MISSING-XREF (Finding #42)
- Has H1 title "# Core REST APIs for LMS", raw pipe table of CRUD endpoints
- No cross-references to service ownership specs

### integration-api.md
**Status:** MISSING-XREF (Finding #43)
- 4-row raw pipe table stub, no H1 title, no cross-references

---

## Folder 03 — docs/architecture/ (78 active .md)

### core-system-architecture.md
**Status:** CLEAN
- 271-line comprehensive doc; 7 domain sections; NORMALISATION NOTE (renamed from Enterprise LMS V2); MS-SCALE-01 contract; Rails entity mapping

### microservice-boundary-map.md
**Status:** CLEAN
- 365-line doc; 8 bounded contexts with full service definitions; explicit ownership rules

### domain-driven-design-map.md
**Status:** CLEAN
- 378-line DDD map; 9 domains; aggregates/entities/value objects/domain services; boundary decisions

### service-data-ownership-rules.md
**Status:** CLEAN
- 59-line ownership matrix; 8 domains; cross-service data access rules

### event-driven-architecture.md
**Status:** TRIM (Finding #1)
- Lines 48–90: Section 3 independently defines 7-field event envelope JSON + rules
- Does NOT reference event-envelope.md anchor
- Fix: remove redundant envelope definition, add reference to docs/anchors/event-envelope.md

### api-versioning-strategy.md
**Status:** CLEAN
- 111-line versioning strategy; URI major versioning; lifecycle states; 6-month minimum deprecation window

### multi-tenant-isolation-model.md
**Status:** CLEAN
- 168-line isolation model; tiered partitioning; RBAC model; API isolation policy

### observability-architecture.md
**Status:** CLEAN
- 214-line observability arch; 4 monitoring systems; canonical logging JSON structure; compliance and scalability sections

### architecture-full-audit-report.md
**Status:** CLEAN
- 106-line audit; Mermaid dependency graph; 4 finding categories all PASS

### circular-dependencies-audit-report.md
**Status:** CLEAN
- 109-line circular dependency audit; Tarjan SCC; found and fixed assessment↔course circular dep; 10/10 scorecard

### cloud-architecture-ems-lms.md
**Status:** MISSING-XREF (Finding #73)
- Raw newline text, no H1, 12 component/technology/purpose rows, no cross-references

### event-domain-catalogue.md
**Status:** MISSING-XREF (Finding #9)
- 20 HRIS/HR events in PascalCase; no reference to companion event-bus-design.md

### security-architecture.md
**Status:** MISSING-XREF (Finding #74)
- Raw 5-row pipe table (SSO, OAuth2, SAML2, data encryption, audit logging), no H1, no cross-references

### service-map.md
**Status:** MISSING-XREF (Finding #75)
- Has H1 "# Enterprise LMS Backend Service Map for LMS", 12 services in plain text
- No cross-references to ARCH_01 or ARCH_02

### duplicate-domains-detection-report.md
**Status:** MISSING-XREF (Finding #11)
- Domain overlap analysis (8 issues); no reference to companion service-boundary-analysis-report.md

### domain-boundaries-backend.md
**Status:** MISSING-XREF (Finding #76)
- Raw domain text blocks, no H1, no cross-references

### event-bus-design.md
**Status:** MISSING-XREF (Finding #10)
- 7 HRIS events in lms. format + 3 infrastructure events; no reference to companion event-domain-catalogue.md

### platform-evolution-model.md
**Status:** MISSING-XREF (Finding #77)
- Has H1 "# DOC_10 Platform Long-Term Evolution Model", 171-line comprehensive strategic doc
- 6 evolution pillars, 3 QC iterations — no cross-references to ARCH_06 or MIG_01

### scalability-strategy.md
**Status:** MISSING-XREF (Finding #78)
- Raw 4-row pipe table (horizontal scaling, stateless, autoscaling, multi-region), no H1, no cross-references

### tenant-customization-catalogue.md
**Status:** MISSING-XREF (Finding #79)
- Raw 24-row pipe table (configuration_area, config_key, description, scope), no H1, no cross-references

### tenant-isolation-strategy.md
**Status:** MISSING-XREF (Finding #80)
- Has H1 "# Multi-Tenant Isolation Strategy"; covers same topic as ARCH_07 without cross-referencing it

### data-isolation-analysis-report.md
**Status:** MISSING-XREF (Finding #81)
- Raw 4-row pipe table with isolation issues, no H1, no cross-references

### event-ownership-analysis-report.md
**Status:** MISSING-XREF (Finding #82)
- Raw pipe table (20 HRIS events with ownership issues), no H1, no cross-references

### service-boundary-analysis-report.md
**Status:** MISSING-XREF (Finding #12)
- Service boundary validation (6 issues); no reference to companion duplicate-domains-detection-report.md

### config-service-design.md
**Status:** CLEAN
- 251-line config service design; 8 modules; MS-CONFIG-01 contract; references capability-resolution.md anchor and ARCH_01

### entitlement-service-design.md
**Status:** MISSING-XREF (Finding #83)
- 226-line doc with H1; 9 modules; deterministic evaluation flow; pseudocode
- Explicitly differentiates from config service and capability registry but no cross-ref links to them

### feature-flag-system-design.md
**Status:** MISSING-XREF (Finding #84)
- 231-line doc with H1; 9 modules; deterministic evaluation sequence; pseudocode
- No cross-references to related docs

### usage-metering-service-design.md
**Status:** MISSING-XREF (Finding #85)
- 247-line doc with H1; 10 sections; canonical usage event model; storage model
- No cross-references to related docs

### capability-registry-service-design.md
**Status:** MISSING-XREF (Finding #86)
- 206-line doc with H1; 8 modules; references docs/architecture/schemas/capability_registry.schema.json (valid) and capability-registry-service-spec.md (valid)
- Does not reference docs/anchors/capability-resolution.md

### tenant-extension-model.md
**Status:** STALE + MISSING-XREF (Findings #54, #87)
- Finding #54 (STALE): Lines 41, 59-67 use `display_name` and `enabled_addons`; canonical names per tenant-contract.md anchor are `name` and `addon_flags`
- Finding #87 (MISSING-XREF): No cross-reference to docs/anchors/tenant-contract.md or ARCH_07

### audit-policy-layer-design.md
**Status:** MISSING-XREF (Finding #88)
- 270-line doc with H1; 10 modules; audit flows; immutable ledger design
- No cross-references to event-envelope.md anchor or related docs

### platform-integration-layer-design.md
**Status:** MISSING-XREF (Finding #89)
- 202-line doc with H1; 6 modules; canonical evaluation order; stateless model
- No cross-references to related docs

### commerce-domain-architecture.md
**Status:** MISSING-XREF (Finding #90)
- 471-line doc with H1; 9 sections; 6 sub-modules; interaction flows; QC conformance checklist
- No cross-references to related docs

### catalog-service-design.md
**Status:** MISSING-XREF (Finding #91)
- 274-line doc with H1; 10 sections; product model with entities; pricing separation contract
- No cross-references to related docs

### checkout-service-design.md
**Status:** MISSING-XREF (Finding #92)
- 297-line doc with H1; 12 sections; domain model; stateless architecture; failure handling
- No cross-references to related docs

### invoice-billing-service-design.md
**Status:** MISSING-XREF (Finding #93)
- 237-line doc with H1; 12 sections; data model with 6 aggregates; invoice lifecycle FSM
- No cross-references to related docs

### subscription-service-design.md
**Status:** MISSING-XREF (Finding #94)
- 310-line doc with H1; 11 sections; plan catalog projection; FSM with transition table
- No cross-references to related docs

### revenue-service-design.md
**Status:** BROKEN-REF (Finding #47)
- Line 275: Behavioral Contract overlay references `BOS§10.1 / GAP-015` (Behavioral Operating Spec confirmed not in D:\LMS\Repo)

### academy-commerce-extensions.md
**Status:** MISSING-XREF (Finding #95)
- 295-line doc with H1; 10 sections; extension-only model; Pakistan regional policy pack
- Inline mention of B3P01 but no formal cross-reference links

### owner-economics-service-design.md
**Status:** MISSING-XREF (Finding #96)
- 83-line doc with H1; References section with valid file refs (B3P06, economic-capabilities-user-spec.md)
- "Master Spec §5.14" informal ref; code file refs are outside docs scope

### academy-operations-domain.md
**Status:** MISSING-XREF (Finding #97)
- 330-line doc with H1; 10 sections; 6 aggregates; 3 workflows; event contract examples
- No cross-references to event-envelope.md anchor or service specs

### school-engagement-domain-design.md
**Status:** MISSING-XREF (Finding #98)
- 312-line doc with H1; preamble references domain-capability-extension-model.md (valid) but no broader cross-refs

### workforce-training-domain-design.md
**Status:** MISSING-XREF (Finding #99)
- 249-line doc with H1; preamble references domain-capability-extension-model.md (valid) but no broader cross-refs

### university-domain-design.md
**Status:** MISSING-XREF (Finding #100)
- 192-line doc with H1; preamble references domain-capability-extension-model.md (valid) but no broader cross-refs

### ai-tutor-assist-design.md
**Status:** MISSING-XREF (Finding #101)
- 177-line doc with H1; MS-AI-01 architectural contract defined; no cross-reference links to related docs

### teacher-ai-assist-design.md
**Status:** MISSING-XREF (Finding #102)
- 128-line doc with H1; well-structured guardrails; no cross-references to related docs

### recommendation-engine-design.md
**Status:** MISSING-XREF (Finding #103)
- 275-line doc with H1; Mermaid diagram; data contracts; strategy/extensibility model; no cross-references

### learner-risk-insights-design.md
**Status:** BROKEN-REF (Finding #48)
- Line 294: Behavioral Contract overlay references `BOS§9.1 / GAP-011` (Behavioral Operating Spec not in D:\LMS\Repo)

### analytics-intelligence-layer-design.md
**Status:** MISSING-XREF (Finding #104)
- 218-line doc with H1; 13 sections; two Mermaid diagrams; InsightArtifact model; no cross-references

### capability-interface-contract.md
**Status:** MISSING-XREF (Finding #105)
- Has H1 "# B1P01 — Capability Interface Contract"; references docs/architecture/schemas/capability_registry.schema.json (valid)
- Does not reference docs/anchors/capability-resolution.md

### communication-adapter-contract.md
**Status:** BROKEN-REF (Finding #49)
- Line 17: Behavioral Contract overlay references `BOS§6.2 / GAP-008` (Behavioral Operating Spec not in D:\LMS\Repo)
- All other refs (interaction-layer-spec.md, adapter-inventory.md) confirmed valid

### config-resolution-interface-contract.md
**Status:** MISSING-XREF (Finding #106)
- Has H1 "# B1P02 — Config Resolution Interface Contract"; well-structured TypeScript interface
- No cross-references to docs/anchors/capability-resolution.md or B2P01

### content-storage-model.md
**Status:** MISSING-XREF (Finding #107)
- Raw pipe/tab-separated text, no H1, 4 content-type rows; no cross-references

### entitlement-interface-contract.md
**Status:** MISSING-XREF (Finding #108)
- Has H1 "# B1P03 — Entitlement Interface Contract"; references config-resolution-interface-contract.md (valid)
- Does not reference docs/anchors/capability-resolution.md

### file-storage-design.md
**Status:** MISSING-XREF (Finding #109)
- Raw 4-row pipe table (storage components, content types, access methods), no H1, no cross-references

### media-security-interface-contract.md
**Status:** MISSING-XREF (Finding #110)
- Has H1 "# B1P07 — Media Security Interface Contract"; TypeScript interfaces; no cross-references

### multi-branch-rbac-model.md
**Status:** BROKEN-REF (Findings #7 and #51)
- Finding #7 (existing): Line 183: wrong folder for org-hierarchy-spec.md (listed under architecture, lives in specs)
- Finding #51 (new): Lines 5 and 184: `LMS_Pakistan_Market_Research_MASTER.md` — source authority reference not in D:\LMS\Repo

### offline-sync-interface-contract.md
**Status:** MISSING-XREF (Finding #111)
- Has H1 "# B1P08 — Offline Sync Interface Contract"; 6 TypeScript interfaces; no cross-references

### payment-provider-adapter-contract.md
**Status:** MISSING-XREF (Finding #112)
- Has H1; references docs/specs/adapter-inventory.md (valid); no broader cross-references to anchors

### system-of-record-design.md
**Status:** BROKEN-REF (Finding #52)
- Line 55: reference `docs/architecture/B3P06` is an incomplete path — missing `_revenue_service_design.md` suffix
- Also has valid references: DATA_01 ✓, ARCH_04 ✓

### storage-adapter-interface-contract.md
**Status:** CLEAN
- Has H1; properly cross-references payment-provider-adapter-contract.md, communication-adapter-contract.md, file-storage-design.md, adapter-inventory.md — all valid

### usage-metering-interface-contract.md
**Status:** MISSING-XREF (Finding #113)
- Has H1 "# B1P04 — Usage Meter Interface Contract"; TypeScript interfaces; no cross-references

### adaptive-learning-engine.md
**Status:** MISSING-XREF (Finding #114)
- Has H1 "# Adaptive Learning Architecture"; 8 components in free-form text; no cross-references

### agi-ready-architecture.md
**Status:** STALE + MISSING-XREF (Findings #55, #115)
- Finding #55 (STALE): H1 title reads "# AGI-Compatible Architecture for LMS LMS" — "LMS LMS" is a duplication artifact
- Finding #115 (MISSING-XREF): Raw pipe tables, no cross-references

### ai-course-generation-pipeline.md
**Status:** MISSING-XREF (Finding #116)
- Raw pipe table, no H1, 4 pipeline stages; no cross-references

### ai-learning-copilot.md
**Status:** MISSING-XREF (Finding #117)
- Has H1 "# AI Learning Assistant for LMS"; raw pipe table 4 rows; no cross-references

### capability-gating-model.md
**Status:** BROKEN-REF (Finding #50)
- Line 131: Behavioral Contract overlay references `BOS§1.1, BOS§12.1 / GAP-018` (Behavioral Operating Spec not in D:\LMS\Repo)
- Reference to DOC_07 (line 153) is valid — billing-and-usage-model.md confirmed in docs/specs/

### product-capabilities-matrix.md
**Status:** MISSING-XREF (Finding #118)
- Has H1; capability matrix with 16 rows; QC iterations; no cross-references to related docs

### global-education-model-framework.md
**Status:** BROKEN-REF (Finding #6)
- Line 92: references `docs/specs/cohort-service-spec.md` — file does not exist; correct is `docs/specs/cohort-service-spec.md`
- Note: progress-tracking-spec.md reference at line 98 is valid

### academy-operational-model.md
**Status:** MISSING-XREF (Finding #119)
- Has H1 "# DOC_04 Academy Operational Model"; 6 lifecycle sections; QC loop; no cross-references

### tutor-operational-model.md
**Status:** MISSING-XREF (Finding #120)
- Has H1 "# DOC_05 Tutor Operational Model"; 7 sections; LMS entity integration table; no cross-references

### ai-capability-definition.md
**Status:** MISSING-XREF (Finding #121)
- Has H1 "# DOC_08: AI Capability Definition"; 188-line comprehensive AI service definition; no cross-references

### terminology-bridge.md
**Status:** CLEAN
- Has H1; references docs/anchors/doc-precedence.md (valid); correctly scoped terminology bridge

### market-enforcements-capability-map.md
**Status:** BROKEN-REF (Finding #53)
- Line 137: references `doc_catalogue.md` — confirmed not in D:\LMS\Repo
- Multiple other refs (offline-sync-interface-contract.md, interaction-layer-spec.md, adapter-inventory.md, B3P03, payment-provider-adapter-contract.md, media-security-interface-contract.md, capability-resolution.md) all valid

### domain-capability-extension-model.md
**Status:** CLEAN
- Has H1; references B2P05, B2P02, B5P01-B5P04 — all valid; correctly scoped extension model

### enterprise-admin-model.md
**Status:** MISSING-XREF (Finding #122)
- Raw pipe table, no H1, 6 admin_component rows; no cross-references

### data-ownership-rules.md
**Status:** MISSING-XREF (Finding #123)
- Raw newline-separated text (service_name/owned_entities/database_tables), no H1; no cross-references

### skills-graph-model.md
**Status:** MISSING-XREF (Finding #124)
- Has H1 "# LMS Skills Graph Model"; 3 pipe tables; no cross-references to DATA_03 or AI_05

---

## Folder 04 — docs/data/ (13 files) — COMPLETE

### analytics-data-model.md
**Status:** MISSING-XREF (Finding #57)
- Raw newline-separated text, no H1, 12 event types with aggregation strategies; no cross-references

### auth-service-storage-contract.md
**Status:** MISSING-XREF (Finding #58)
- Has H1; 5 table definitions (auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events); no cross-refs to auth-service-spec.md

### core-lms-schema.md
**Status:** STALE (Finding #56)
- H1 title reads "# Core LMS Relational Schema (LMS LMS)" — "LMS LMS" is a duplication artifact in the title

### global-education-schema.md
**Status:** MISSING-XREF (Finding #59)
- 264-line schema doc with 9 entities and Rails entity compatibility mapping; no cross-refs to DATA_02/DATA_03

### learning-event-schema.md
**Status:** TRIM (Finding #2)
- Lines 9–17: redundant 7-field envelope table — already defined in docs/anchors/event-envelope.md
- Line 7 already references the anchor
- Fix: remove lines 9–17

### knowledge-graph-schema.md
**Status:** MISSING-XREF (Finding #60)
- 97-line graph schema with 7 node types, 6 edge types; no cross-refs to AI_05/AI_03/DATA_01

### institution-hierarchy-schema.md
**Status:** MISSING-XREF (Finding #61)
- 281-line hierarchy schema (Tenant→Institution→Sub-Institution→Program→Cohort→Session)
- No cross-refs to DATA_01/DATA_05

### cohort-batch-schema.md
**Status:** CLEAN

### assessment-data-schema.md
**Status:** CLEAN

### ai-interaction-schema.md
**Status:** CLEAN

### data-model-validation-report.md
**Status:** CLEAN

### learning-data-model-overview.md
**Status:** CLEAN

### database-schema-validation-report.md
**Status:** CLEAN

---

## Folder 05 — docs/integrations/ (6 files) — COMPLETE

### auth-lifecycle-events.md
**Status:** MISSING-XREF (Finding #62)
- Has H1; 7 published events + 2 consumed events; 7-field envelope example with additive metadata fields (not TRIM)
- No cross-references to event-envelope.md anchor or auth-service-spec.md

### hris-sync-spec.md
**Status:** MISSING-XREF (Finding #63)
- 3-row raw pipe table, no H1, no cross-references

### lti-consumer-spec.md
**Status:** MISSING-XREF (Finding #64)
- Raw text blocks, no H1, no cross-references

### lti-provider-spec.md
**Status:** MISSING-XREF (Finding #65)
- 11-row pipe table, no H1, no cross-references

### standards-support.md
**Status:** MISSING-XREF (Finding #66)
- Raw newline text (SCORM 1.2, SCORM 2004, xAPI, LTI 1.3), no H1, no cross-references

### webhook-system-spec.md
**Status:** MISSING-XREF (Finding #67)
- Raw text blocks with webhook event examples, no H1, no cross-references

---

## Folder 06 — docs/market/ (3 files) — COMPLETE

### competitive-intelligence.md
**Status:** BROKEN-REF (Finding #44)
- Lines 5 and 109: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo
- File lives externally at C:\LMS\LMS New\ (per platform-behavioral-contract.md References)

### gtm-entry-strategy.md
**Status:** BROKEN-REF (Finding #45)
- Lines 5 and 141: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo

### pakistan-market-pricing-guide.md
**Status:** BROKEN-REF (Finding #46)
- Lines 5 and 134: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo

---

## Folder 07 — docs/qc/ (27 files) — COMPLETE

### architecture-consistency-check-report.md
**Status:** CLEAN

### audit-logging-verification-report.md
**Status:** BROKEN-REF (Finding #4)
- Lines 5–6: references `security_architecture.md` (does not exist) → correct: `security-architecture.md`
- Lines 5–6: references `audit-policy-layer-design.md` (does not exist) → correct: `observability-architecture.md`

### auth-service-qc-report.md
**Status:** MISSING-XREF (Finding #68)
- Has H1; 2 evaluation passes; references auth-service-storage-contract.md but not auth-service-spec.md

### capability-registry-validation-report.md
**Status:** CLEAN

### entitlement-resolution-validation-report.md
**Status:** CLEAN

### config-resolution-validation-report.md
**Status:** CLEAN

### commerce-flow-validation-report.md
**Status:** CLEAN

### payment-adapter-validation-report.md
**Status:** CLEAN

### communication-workflow-validation-report.md
**Status:** CLEAN

### delivery-system-validation-report.md
**Status:** CLEAN

### end-to-end-system-validation-report.md
**Status:** CLEAN

### cross-service-dependency-check-report.md
**Status:** BROKEN-REF (Finding #5)
- Line 10: references `core-system-architecture.md` → correct: `core-system-architecture.md`

### load-test-preparation-report.md
**Status:** CLEAN

### end-to-end-validation-report.md
**Status:** CLEAN

### pakistan-wedge-validation-report.md
**Status:** CLEAN

### feature-completeness-check-report.md
**Status:** MISSING-XREF (Finding #69)
- Raw newline text, no H1, no cross-references

### event-architecture-validation-report.md
**Status:** MISSING-XREF (Finding #70)
- Raw newline text, no H1, no cross-references

### service-boundary-validation-report.md
**Status:** MISSING-XREF (Finding #71)
- Raw pipe table, no H1, no cross-references

### code-structure-validation-report.md
**Status:** CLEAN

### event-publishing-validation-report.md
**Status:** BROKEN-REF (Finding #3)
- Line 4: references `/docs/architecture/event-driven-architecture.md` → correct: `docs/architecture/event-driven-architecture.md`

### service-communication-validation-report.md
**Status:** CLEAN

### system-hardening-report.md
**Status:** CLEAN

### full-system-integration-validation-report.md
**Status:** CLEAN

### service-map-verification-report.md
**Status:** CLEAN

### platform-governor-certification-report.md
**Status:** CLEAN

### system-final-validation-report.md
**Status:** CLEAN

### tenant-model-validation-report.md
**Status:** MISSING-XREF (Finding #72)
- Raw newline text, no H1, no cross-references

---

## Folder 08 — docs/specs/ (63 files) — COMPLETE

### adapter-inventory.md
**Status:** STALE (Finding #8)
- Line 129 (MS-ADAPTER-01 table): Storage shown as `(PLANNED)` / `(to be created)`
- Main table (line 19) and dedicated section (line 58) confirm Storage is IMPLEMENTED

### ai-tutor-service-spec.md
**Status:** CLEAN

### recommendation-service-spec.md
**Status:** CLEAN

### skill-inference-service-spec.md
**Status:** CLEAN

### learning-analytics-service-spec.md
**Status:** CLEAN

### learning-knowledge-graph-spec.md
**Status:** CLEAN

### analytics-service-spec.md
**Status:** CLEAN

### assessment-service-spec.md
**Status:** CLEAN

### auth-service-spec-v0.md
**Status:** CLEAN (DEPRECATED banner present, correctly redirects to auth-service-spec.md)

### auth-service-test-plan.md
**Status:** MISSING-XREF (Finding #16)
- 46-line test plan with no reference to auth-service-spec.md

### capability-domain-map.md
**Status:** BROKEN-REF (Finding #35)
- Line 60: references `doc_catalogue.md` — file does not exist anywhere in D:\LMS\Repo

### capability-registry-service-spec.md
**Status:** CLEAN

### compliance-reporting-spec.md
**Status:** MISSING-XREF (Finding #23)
- 16-line raw table stub with no cross-references

### content-service-spec.md
**Status:** MISSING-XREF (Finding #13)
- 5-line raw pipe table stub, no title, no purpose, no cross-references

### content-versioning-spec.md
**Status:** MISSING-XREF (Finding #24)
- 16-line raw table stub with no cross-references

### capability-inventory.md
**Status:** CLEAN

### billing-and-usage-model.md
**Status:** CLEAN

### economic-capabilities-user-spec.md
**Status:** CLEAN

### enterprise-control-spec.md
**Status:** CLEAN

### event-ingestion-spec.md
**Status:** CLEAN

### exam-engine-spec.md
**Status:** CLEAN

### feature-flags-spec.md
**Status:** MISSING-XREF (Finding #25)
- 11-line raw table stub with no cross-references

### financial-ledger-spec.md
**Status:** CLEAN

### free-tier-operational-definition.md
**Status:** BROKEN-REF (Finding #33)
- Lines 5 and 124: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo

### integration-service-spec.md
**Status:** CLEAN

### interaction-layer-spec.md
**Status:** CLEAN

### learning-analytics-spec.md
**Status:** MISSING-XREF (Finding #26)
- 6-line raw table stub with no cross-references

### learning-path-spec.md
**Status:** MISSING-XREF (Finding #14)
- 22-line raw table stub with no cross-references

### lesson-service-spec.md
**Status:** CLEAN

### localization-spec.md
**Status:** MISSING-XREF (Finding #27)
- 8-line titled stub with no cross-references

### manager-dashboard-spec.md
**Status:** MISSING-XREF (Finding #28)
- 6-line raw table stub with no cross-references

### media-pipeline-spec.md
**Status:** MISSING-XREF (Finding #15)
- 16-line pipeline_stage raw stub with no cross-references

### media-security-spec.md
**Status:** CLEAN

### monolith-to-services-migration.md
**Status:** CLEAN

### notification-service-spec.md
**Status:** CLEAN

### offline-sync-spec.md
**Status:** CLEAN

### onboarding-spec.md
**Status:** CLEAN

### operations-os-spec.md
**Status:** BROKEN-REF (Finding #19)
- Line 69: `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md` not found in D:\LMS\Repo

### org-hierarchy-spec.md
**Status:** MISSING-XREF (Finding #29)
- 29-line entity/attributes stub, no document title, no cross-references

### performance-capabilities-spec.md
**Status:** BROKEN-REF (Finding #30)
- Line 139: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo

### platform-behavioral-contract.md
**Status:** CLEAN

### prerequisite-engine-spec.md
**Status:** MISSING-XREF (Finding #31)
- 29-line YAML-style stub, no title, no cross-references

### progress-tracking-spec.md
**Status:** MISSING-XREF (Finding #17)
- 16-line raw table stub with no cross-references

### rbac-service-spec-v0.md
**Status:** MISSING-XREF (Finding #18)
- No cross-reference to rbac-service-spec.md, no deprecation notice

### reporting-spec.md
**Status:** MISSING-XREF (Finding #20)
- 8-line titled stub with no cross-references

### scorm-runtime-spec.md
**Status:** MISSING-XREF (Finding #21)
- 6-line raw table stub with no cross-references

### session-service-spec.md
**Status:** CLEAN

### skill-analytics-spec.md
**Status:** MISSING-XREF (Finding #32)
- Has title and substantive content, but no cross-references to AI_03, DATA_03, skills-graph-model.md

### auth-service-spec.md
**Status:** CLEAN

### rbac-service-spec.md
**Status:** CLEAN

### tenant-service-spec.md
**Status:** CLEAN (= tenant-service-spec-v0.md)

### institution-service-spec.md
**Status:** CLEAN

### program-service-spec.md
**Status:** CLEAN

### cohort-service-spec.md
**Status:** CLEAN

### course-service-spec.md
**Status:** CLEAN

### enrollment-service-spec.md
**Status:** CLEAN

### progress-service-spec.md
**Status:** CLEAN

### certificate-service-spec.md
**Status:** CLEAN

### sso-spec.md
**Status:** MISSING-XREF (Finding #22)
- 6-line raw table stub with no cross-references

### system-economics-spec.md
**Status:** CLEAN

### tenant-service-spec-v0.md
**Status:** CLEAN (= SPEC_04)

### user-service-spec.md
**Status:** CLEAN

### vocational-training-domain-spec.md
**Status:** BROKEN-REF (Finding #34)
- Lines 4 and 154: `LMS_Pakistan_Market_Research_MASTER.md` not found in D:\LMS\Repo

### workflow-engine-spec.md
**Status:** CLEAN

---

## Confirmed Findings

| # | File | Folder | Code | Issue |
|---|------|--------|------|-------|
| 1 | event-driven-architecture.md | architecture | TRIM | Lines 48–90: envelope definition duplicates docs/anchors/event-envelope.md |
| 2 | learning-event-schema.md | data | TRIM | Lines 9–17: envelope table duplicates docs/anchors/event-envelope.md |
| 3 | event-publishing-validation-report.md | qc | BROKEN-REF | Line 4: wrong path for ARCH_05 (`/docs/architecture/event-driven-architecture.md`) |
| 4 | audit-logging-verification-report.md | qc | BROKEN-REF | Lines 5–6: two non-existent refs (`security_architecture.md`, `audit-policy-layer-design.md`) |
| 5 | cross-service-dependency-check-report.md | qc | BROKEN-REF | Line 10: `core-system-architecture.md` missing ARCH_01_ prefix |
| 6 | global-education-model-framework.md | architecture | BROKEN-REF | Line 92: `cohort-service-spec.md` does not exist; correct is `cohort-service-spec.md` |
| 7 | multi-branch-rbac-model.md | architecture | BROKEN-REF | Line 183: `docs/architecture/org-hierarchy-spec.md` wrong folder; file is in docs/specs/ |
| 8 | adapter-inventory.md | specs | STALE | Line 129: Storage adapter status contradicts lines 19 and 58 (shown PLANNED but is IMPLEMENTED) |
| 9 | event-domain-catalogue.md | architecture | MISSING-XREF | No reference to companion event-bus-design.md |
| 10 | event-bus-design.md | architecture | MISSING-XREF | No reference to companion event-domain-catalogue.md |
| 11 | duplicate-domains-detection-report.md | architecture | MISSING-XREF | No reference to companion service-boundary-analysis-report.md |
| 12 | service-boundary-analysis-report.md | architecture | MISSING-XREF | No reference to companion duplicate-domains-detection-report.md |
| 13 | content-service-spec.md | specs | MISSING-XREF | 5-line raw pipe table stub, no title/purpose/cross-refs |
| 14 | learning-path-spec.md | specs | MISSING-XREF | 22-line raw table stub, no cross-refs |
| 15 | media-pipeline-spec.md | specs | MISSING-XREF | 16-line pipeline_stage raw stub, no cross-refs |
| 16 | auth-service-test-plan.md | specs | MISSING-XREF | No reference to auth-service-spec.md |
| 17 | progress-tracking-spec.md | specs | MISSING-XREF | 16-line raw table stub, no cross-refs |
| 18 | rbac-service-spec-v0.md | specs | MISSING-XREF | No cross-ref to rbac-service-spec.md, no deprecation notice |
| 19 | operations-os-spec.md | specs | BROKEN-REF | Line 69: `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md` not in D:\LMS\Repo |
| 20 | reporting-spec.md | specs | MISSING-XREF | 8-line titled stub, no cross-refs |
| 21 | scorm-runtime-spec.md | specs | MISSING-XREF | 6-line raw table stub, no cross-refs |
| 22 | sso-spec.md | specs | MISSING-XREF | 6-line raw table stub, no cross-refs |
| 23 | compliance-reporting-spec.md | specs | MISSING-XREF | 16-line raw table stub, no cross-refs |
| 24 | content-versioning-spec.md | specs | MISSING-XREF | 16-line raw table stub, no cross-refs |
| 25 | feature-flags-spec.md | specs | MISSING-XREF | 11-line raw table stub, no cross-refs |
| 26 | learning-analytics-spec.md | specs | MISSING-XREF | 6-line raw table stub, no cross-refs |
| 27 | localization-spec.md | specs | MISSING-XREF | 8-line titled stub, no cross-refs |
| 28 | manager-dashboard-spec.md | specs | MISSING-XREF | 6-line raw table stub, no cross-refs |
| 29 | org-hierarchy-spec.md | specs | MISSING-XREF | 29-line entity stub, no title, no cross-refs |
| 30 | performance-capabilities-spec.md | specs | BROKEN-REF | Line 139: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 31 | prerequisite-engine-spec.md | specs | MISSING-XREF | 29-line YAML-style stub, no title, no cross-refs |
| 32 | skill-analytics-spec.md | specs | MISSING-XREF | Has substantive content but no cross-refs to AI_03/DATA_03/skills-graph-model.md |
| 33 | free-tier-operational-definition.md | specs | BROKEN-REF | Lines 5, 124: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 34 | vocational-training-domain-spec.md | specs | BROKEN-REF | Lines 4, 154: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 35 | capability-domain-map.md | specs | BROKEN-REF | Line 60: `doc_catalogue.md` not found in D:\LMS\Repo |
| 36 | analytics-api.md | api | MISSING-XREF | 4-row table stub, no cross-refs to analytics-service-spec.md or AI_04 |
| 37 | api-contract-validation-report.md | api | MISSING-XREF | Raw pipe table, no H1 title, no cross-refs |
| 38 | api-gateway-design.md | api | MISSING-XREF | Raw 5-row table, no H1 title, no cross-refs |
| 39 | api-spec-validation-report.md | api | MISSING-XREF | Raw text, no H1 title, no cross-refs |
| 40 | auth-service-api.md | api | MISSING-XREF | Substantive content but no cross-refs to auth-service-spec.md |
| 41 | content-api.md | api | MISSING-XREF | Raw text stub, no H1 title, no cross-refs |
| 42 | core-rest-api.md | api | MISSING-XREF | CRUD table, no cross-refs to service ownership specs |
| 43 | integration-api.md | api | MISSING-XREF | 4-row raw table stub, no H1 title, no cross-refs |
| 44 | competitive-intelligence.md | market | BROKEN-REF | Lines 5, 109: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 45 | gtm-entry-strategy.md | market | BROKEN-REF | Lines 5, 141: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 46 | pakistan-market-pricing-guide.md | market | BROKEN-REF | Lines 5, 134: `LMS_Pakistan_Market_Research_MASTER.md` not in D:\LMS\Repo |
| 47 | revenue-service-design.md | architecture | BROKEN-REF | Line 275: references `BOS§10.1 / GAP-015` — Behavioral Operating Spec not in D:\LMS\Repo |
| 48 | learner-risk-insights-design.md | architecture | BROKEN-REF | Line 294: references `BOS§9.1 / GAP-011` — Behavioral Operating Spec not in D:\LMS\Repo |
| 49 | communication-adapter-contract.md | architecture | BROKEN-REF | Line 17: references `BOS§6.2 / GAP-008` — Behavioral Operating Spec not in D:\LMS\Repo |
| 50 | capability-gating-model.md | architecture | BROKEN-REF | Line 131: references `BOS§1.1, BOS§12.1 / GAP-018` — Behavioral Operating Spec not in D:\LMS\Repo |
| 51 | multi-branch-rbac-model.md | architecture | BROKEN-REF | Lines 5, 184: `LMS_Pakistan_Market_Research_MASTER.md` used as source authority — not in D:\LMS\Repo |
| 52 | system-of-record-design.md | architecture | BROKEN-REF | Line 55: `docs/architecture/B3P06` is an incomplete path — missing `_revenue_service_design.md` suffix |
| 53 | market-enforcements-capability-map.md | architecture | BROKEN-REF | Line 137: `doc_catalogue.md` not found in D:\LMS\Repo |
| 54 | tenant-extension-model.md | architecture | STALE | Lines 41, 59-67: `display_name` (→`name`) and `enabled_addons` (→`addon_flags`) contradict tenant-contract.md canonical names |
| 55 | agi-ready-architecture.md | architecture | STALE | H1 title "# AGI-Compatible Architecture for LMS LMS" — "LMS LMS" is a duplication artifact |
| 56 | core-lms-schema.md | data | STALE | H1 title "# Core LMS Relational Schema (LMS LMS)" — "LMS LMS" is a duplication artifact |
| 57 | analytics-data-model.md | data | MISSING-XREF | Raw newline text, no H1, 12 event types; no cross-refs |
| 58 | auth-service-storage-contract.md | data | MISSING-XREF | 5 table definitions; no cross-refs to auth-service-spec.md |
| 59 | global-education-schema.md | data | MISSING-XREF | 264-line schema; no cross-refs to DATA_02/DATA_03 |
| 60 | knowledge-graph-schema.md | data | MISSING-XREF | 97-line graph schema; no cross-refs to AI_05/AI_03/DATA_01 |
| 61 | institution-hierarchy-schema.md | data | MISSING-XREF | 281-line hierarchy schema; no cross-refs to DATA_01/DATA_05 |
| 62 | auth-lifecycle-events.md | integrations | MISSING-XREF | Has H1; envelope example present (not TRIM); no cross-ref to event-envelope.md anchor |
| 63 | hris-sync-spec.md | integrations | MISSING-XREF | 3-row raw pipe table, no H1, no cross-refs |
| 64 | lti-consumer-spec.md | integrations | MISSING-XREF | Raw text blocks, no H1, no cross-refs |
| 65 | lti-provider-spec.md | integrations | MISSING-XREF | 11-row pipe table, no H1, no cross-refs |
| 66 | standards-support.md | integrations | MISSING-XREF | Raw newline text (SCORM/xAPI/LTI), no H1, no cross-refs |
| 67 | webhook-system-spec.md | integrations | MISSING-XREF | Raw text blocks with webhook examples, no H1, no cross-refs |
| 68 | auth-service-qc-report.md | qc | MISSING-XREF | Has H1; refs auth-service-storage-contract.md but not auth-service-spec.md |
| 69 | feature-completeness-check-report.md | qc | MISSING-XREF | Raw newline text, no H1, no cross-refs |
| 70 | event-architecture-validation-report.md | qc | MISSING-XREF | Raw newline text, no H1, no cross-refs |
| 71 | service-boundary-validation-report.md | qc | MISSING-XREF | Raw pipe table, no H1, no cross-refs |
| 72 | tenant-model-validation-report.md | qc | MISSING-XREF | Raw newline text, no H1, no cross-refs |
| 73 | cloud-architecture-ems-lms.md | architecture | MISSING-XREF | Raw newline text, no H1, 12 rows; no cross-refs |
| 74 | security-architecture.md | architecture | MISSING-XREF | Raw 5-row pipe table, no H1, no cross-refs |
| 75 | service-map.md | architecture | MISSING-XREF | Has H1; 12 services listed; no cross-refs to ARCH_01 or ARCH_02 |
| 76 | domain-boundaries-backend.md | architecture | MISSING-XREF | Raw domain text blocks, no H1, no cross-refs |
| 77 | platform-evolution-model.md | architecture | MISSING-XREF | 171-line doc with H1; 6 evolution pillars; no cross-refs to ARCH_06 or MIG_01 |
| 78 | scalability-strategy.md | architecture | MISSING-XREF | Raw 4-row pipe table, no H1, no cross-refs |
| 79 | tenant-customization-catalogue.md | architecture | MISSING-XREF | Raw 24-row pipe table, no H1, no cross-refs |
| 80 | tenant-isolation-strategy.md | architecture | MISSING-XREF | Has H1; covers same topic as ARCH_07 without cross-referencing it |
| 81 | data-isolation-analysis-report.md | architecture | MISSING-XREF | Raw 4-row pipe table, no H1, no cross-refs |
| 82 | event-ownership-analysis-report.md | architecture | MISSING-XREF | Raw pipe table (20 HRIS events), no H1, no cross-refs |
| 83 | entitlement-service-design.md | architecture | MISSING-XREF | 226-line doc; differentiates from config and registry but no cross-ref links to them |
| 84 | feature-flag-system-design.md | architecture | MISSING-XREF | 231-line doc; no cross-refs to related docs |
| 85 | usage-metering-service-design.md | architecture | MISSING-XREF | 247-line doc; no cross-refs to related docs |
| 86 | capability-registry-service-design.md | architecture | MISSING-XREF | Has schema and spec refs (valid); missing link to docs/anchors/capability-resolution.md |
| 87 | tenant-extension-model.md | architecture | MISSING-XREF | No cross-ref to docs/anchors/tenant-contract.md or ARCH_07 (also STALE #54) |
| 88 | audit-policy-layer-design.md | architecture | MISSING-XREF | 270-line doc; no cross-refs to event-envelope.md anchor |
| 89 | platform-integration-layer-design.md | architecture | MISSING-XREF | 202-line doc; no cross-refs to related docs |
| 90 | commerce-domain-architecture.md | architecture | MISSING-XREF | 471-line doc; no cross-refs to related docs |
| 91 | catalog-service-design.md | architecture | MISSING-XREF | 274-line doc; no cross-refs to related docs |
| 92 | checkout-service-design.md | architecture | MISSING-XREF | 297-line doc; no cross-refs to related docs |
| 93 | invoice-billing-service-design.md | architecture | MISSING-XREF | 237-line doc; no cross-refs to related docs |
| 94 | subscription-service-design.md | architecture | MISSING-XREF | 310-line doc; no cross-refs to related docs |
| 95 | academy-commerce-extensions.md | architecture | MISSING-XREF | 295-line doc; inline B3P01 mention but no formal cross-ref links |
| 96 | owner-economics-service-design.md | architecture | MISSING-XREF | Has valid refs (B3P06, economic-capabilities-user-spec.md); broader docs not linked |
| 97 | academy-operations-domain.md | architecture | MISSING-XREF | 330-line doc; no cross-refs to event-envelope.md anchor or service specs |
| 98 | school-engagement-domain-design.md | architecture | MISSING-XREF | Has preamble ref to domain-capability-extension-model.md only; no broader cross-refs |
| 99 | workforce-training-domain-design.md | architecture | MISSING-XREF | Has preamble ref to domain-capability-extension-model.md only; no broader cross-refs |
| 100 | university-domain-design.md | architecture | MISSING-XREF | Has preamble ref to domain-capability-extension-model.md only; no broader cross-refs |
| 101 | ai-tutor-assist-design.md | architecture | MISSING-XREF | 177-line doc; MS-AI-01 contract; no cross-ref links to related docs |
| 102 | teacher-ai-assist-design.md | architecture | MISSING-XREF | 128-line doc; no cross-refs to related docs |
| 103 | recommendation-engine-design.md | architecture | MISSING-XREF | 275-line doc; no cross-refs to related docs |
| 104 | analytics-intelligence-layer-design.md | architecture | MISSING-XREF | 218-line doc; no cross-refs to related docs |
| 105 | capability-interface-contract.md | architecture | MISSING-XREF | Has schema ref (valid); missing link to docs/anchors/capability-resolution.md |
| 106 | config-resolution-interface-contract.md | architecture | MISSING-XREF | Has H1; no cross-refs to docs/anchors/capability-resolution.md or B2P01 |
| 107 | content-storage-model.md | architecture | MISSING-XREF | Raw pipe/tab text, no H1, no cross-refs |
| 108 | entitlement-interface-contract.md | architecture | MISSING-XREF | Has config-resolution-interface-contract.md ref (valid); missing capability-resolution.md anchor link |
| 109 | file-storage-design.md | architecture | MISSING-XREF | Raw 4-row pipe table, no H1, no cross-refs |
| 110 | media-security-interface-contract.md | architecture | MISSING-XREF | Has H1; TypeScript interfaces; no cross-refs |
| 111 | offline-sync-interface-contract.md | architecture | MISSING-XREF | Has H1; 6 TypeScript interfaces; no cross-refs |
| 112 | payment-provider-adapter-contract.md | architecture | MISSING-XREF | Has adapter-inventory.md ref (valid); no broader cross-refs to anchors |
| 113 | usage-metering-interface-contract.md | architecture | MISSING-XREF | Has H1; TypeScript interfaces; no cross-refs |
| 114 | adaptive-learning-engine.md | architecture | MISSING-XREF | Has H1; 8 components; no cross-refs |
| 115 | agi-ready-architecture.md | architecture | MISSING-XREF | Raw pipe tables; no cross-refs (also STALE #55) |
| 116 | ai-course-generation-pipeline.md | architecture | MISSING-XREF | Raw pipe table, no H1, no cross-refs |
| 117 | ai-learning-copilot.md | architecture | MISSING-XREF | Has H1; raw pipe table; no cross-refs |
| 118 | product-capabilities-matrix.md | architecture | MISSING-XREF | Has H1; 16-row capability matrix; no cross-refs to related docs |
| 119 | academy-operational-model.md | architecture | MISSING-XREF | Has H1; 6 lifecycle sections; no cross-refs |
| 120 | tutor-operational-model.md | architecture | MISSING-XREF | Has H1; 7 sections; no cross-refs |
| 121 | ai-capability-definition.md | architecture | MISSING-XREF | 188-line doc with H1; no cross-refs |
| 122 | enterprise-admin-model.md | architecture | MISSING-XREF | Raw pipe table, no H1, no cross-refs |
| 123 | data-ownership-rules.md | architecture | MISSING-XREF | Raw newline text, no H1, no cross-refs |
| 124 | skills-graph-model.md | architecture | MISSING-XREF | Has H1; 3 pipe tables; no cross-refs to DATA_03 or AI_05 |

**Total confirmed findings: 124**

---

## Summary by Code

| Code | Count | Priority |
|------|-------|----------|
| BROKEN-REF | 22 | High — dead links, wrong paths, missing files |
| STALE | 4 | Medium — content contradicts current known state |
| TRIM | 2 | Medium — redundant sections that duplicate canonical anchors |
| MISSING-XREF | 96 | Low-Medium — cross-reference gaps, largely stub files |

## Summary by Folder

| Folder | BROKEN-REF | STALE | TRIM | MISSING-XREF | CLEAN |
|--------|-----------|-------|------|-------------|-------|
| anchors | 0 | 0 | 0 | 0 | 5 |
| api | 0 | 0 | 0 | 8 | 0 |
| architecture | 9 | 3 | 1 | 52 | 13 |
| data | 0 | 1 | 1 | 5 | 6 |
| integrations | 0 | 0 | 0 | 6 | 0 |
| market | 3 | 0 | 0 | 0 | 0 |
| qc | 3 | 0 | 0 | 5 | 19 |
| specs | 7 | 1 | 0 | 20 | 35 |
| **TOTAL** | **22** | **5** | **2** | **96** | **78** |

*Note: STALE count = 5 (findings #8, #54, #55, #56 = 4 issues; adapter-inventory.md is counted once in specs STALE column). BROKEN-REF architecture = 9 (findings #6, #7, #47-#53). Files with multiple codes counted once per code per folder row.*

---

**AWAITING USER REVIEW AND APPROVAL BEFORE ANY FIXES ARE APPLIED**
