# Noise Kill Tracker — docs/ Subfolders
**Phase:** Noise Kill only — repetition, duplication, overlap
**Out of scope:** broken references, ambiguity, missing content, contradictions (→ normalisation phase)
**Rule:** Every file read before any finding logged. No assumptions.
**Last updated:** 2026-05-18 — ALL 203 .md FILES READ 100% (9 previously unscanned files confirmed CLEAN 2026-05-18: 6 from docs/data/, 3 from docs/market/)

---

## Folder Progress

| Folder | Files | Status |
|---|---|---|
| docs/anchors/ | 5 | COMPLETE — 0 noise items |
| docs/api/ | 8 | COMPLETE — 0 noise items |
| docs/data/ | 13 | COMPLETE — 1 trim (DATA_02) |
| docs/architecture/ | 78 md | COMPLETE — 2 archive, 1 trim |
| docs/specs/ | 63 md | COMPLETE — 0 archive, 1 trim (AI_01) |
| docs/integrations/ | 6 | COMPLETE — 0 noise items |
| docs/qc/ | 27 md + 11 py | COMPLETE — 1 archive (B3P05), 0 trims |
| docs/market/ | 3 | COMPLETE — 0 noise items |

**Canonical .md scope: 203 active files (excludes 3 archived: architecture/_archive x2, qc/_archive x1)**

---

## Noise Findings Log

| # | File | Folder | Finding | Type | Duplicate/Overlap of | Status |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

---

## Folder Detail

### 01 · docs/anchors/ — 5 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| capability-resolution.md | DONE | CLEAN — unique canonical resolution chain (capability→config→entitlement→final_state) |
| country-layer-architecture.md | DONE | CLEAN — unique adapter-binding pattern, ties 4 interface contracts to QC evidence |
| doc-precedence.md | DONE | CLEAN — unique priority model BATCH>SPEC>ARCH>Legacy |
| event-envelope.md | DONE | CLEAN — canonical envelope anchor, unique content |
| tenant-contract.md | DONE | CLEAN — unique canonical tenant payload shape |

**Folder result: 0 noise items. All 5 files are unique canonical anchors.**

---

### 02 · docs/api/ — 8 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| analytics-api.md | DONE | CLEAN — 4 unique analytics endpoints |
| api-contract-validation-report.md | DONE | CLEAN — unique Gate 2 API contract findings |
| api-gateway-design.md | DONE | CLEAN — unique 5-component gateway design |
| api-spec-validation-report.md | DONE | CLEAN — unique Gate 1 API spec findings |
| auth-service-api.md | DONE | CLEAN — unique auth API contract (10 routes, schemas, error matrix) |
| content-api.md | DONE | CLEAN — unique content endpoints (upload, publish not in core_rest_api) |
| core-rest-api.md | DONE | CLEAN — primary REST catalog (users/courses/lessons/enrollments/assessments/certificates) |
| integration-api.md | DONE | CLEAN — unique integration endpoints (HRIS, CRM, LTI, webhooks) |

**Folder result: 0 noise items. All 8 files unique.**

---

### 03 · docs/data/ — 13 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| analytics-data-model.md | DONE | CLEAN — unique (12 event types, aggregation strategies) |
| auth-service-storage-contract.md | DONE | CLEAN — unique auth DB schema (5 tables, access constraints) |
| core-lms-schema.md | DONE | CLEAN — unique core schema (8 tables, PKs, relationships) |
| global-education-schema.md | DONE | CLEAN — unique global education extension schema |
| learning-event-schema.md | DONE | TRIM — re-defines 7 envelope fields already owned by event-envelope.md anchor (lines 9–17) |
| knowledge-graph-schema.md | DONE | CLEAN — unique knowledge graph schema (7 nodes, 6 edges) |
| institution-hierarchy-schema.md | DONE | CLEAN — unique hierarchy schema (adds Sub-Institution level not in DATA_01) |
| cohort-batch-schema.md | DONE | CLEAN — unique delivery schema (Program/Cohort/Batch/Session Group/Enrollment Link, 3 delivery models) |
| assessment-data-schema.md | DONE | CLEAN — unique assessment schema (6 entities: Assessment/Attempt/Question Set/Submission/Grading Record/Result) |
| ai-interaction-schema.md | DONE | CLEAN — unique AI interaction schema (7 entities, tenant-safe, audit-by-default) |
| data-model-validation-report.md | DONE | CLEAN — unique QC findings (missing entities, naming mismatches, analytics coverage gaps) |
| learning-data-model-overview.md | DONE | CLEAN — unique high-level learning data model overview (10 entities, compatibility mapping) |
| database-schema-validation-report.md | DONE | CLEAN — unique DB schema QC findings (ownership, terminology inconsistencies) |

**Note (normalisation, not noise kill):** DATA_01 and DATA_04 both define Institution/Program/Cohort/Session with different field schemas — schema conflict, not duplication.
**Folder result: 0 archive candidates. 1 trim (DATA_02). All 13 files read.**

---

### 04 · docs/architecture/ — 75 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| core-system-architecture.md | DONE | CLEAN — unique core system architecture with 9 domain responsibilities |
| microservice-boundary-map.md | DONE | CLEAN — unique bounded context map (all services, APIs, events) |
| domain-driven-design-map.md | DONE | CLEAN — unique DDD map (9 bounded contexts, aggregates, value objects) |
| service-data-ownership-rules.md | DONE | CLEAN — unique service→entity ownership matrix |
| event-driven-architecture.md | DONE | TRIM — independently defines same envelope schema, no anchor reference |
| api-versioning-strategy.md | DONE | CLEAN — unique versioning strategy (major version, deprecation lifecycle) |
| multi-tenant-isolation-model.md | DONE | CLEAN — unique 3-pass QC isolation model (context propagation, partitioning, RBAC) |
| observability-architecture.md | DONE | CLEAN — comprehensive, unique content, keep |
| architecture-full-audit-report.md | DONE | CLEAN — unique audit findings (event ownership fix, cycle detection) |
| circular-dependencies-audit-report.md | DONE | CLEAN — unique cycle detection report (40 services, Tarjan SCC) |
| config-service-design.md | DONE | CLEAN — unique config service design |
| entitlement-service-design.md | DONE | CLEAN — unique entitlement service design |
| feature-flag-system-design.md | DONE | CLEAN — unique feature flag system design |
| usage-metering-service-design.md | DONE | CLEAN — unique usage metering design |
| capability-registry-service-design.md | DONE | CLEAN — unique capability registry design |
| tenant-extension-model.md | DONE | CLEAN — unique tenant extension model |
| audit-policy-layer-design.md | DONE | CLEAN — unique audit policy layer design |
| platform-integration-layer-design.md | DONE | CLEAN — unique platform integration layer design |
| commerce-domain-architecture.md | DONE | CLEAN — unique commerce domain architecture |
| catalog-service-design.md | DONE | CLEAN — unique catalog service design |
| checkout-service-design.md | DONE | CLEAN — unique checkout service design |
| invoice-billing-service-design.md | DONE | CLEAN — unique invoice/billing service design |
| subscription-service-design.md | DONE | CLEAN — unique subscription service design |
| revenue-service-design.md | DONE | CLEAN — unique revenue service design |
| academy-commerce-extensions.md | DONE | CLEAN — unique academy commerce extensions |
| owner-economics-service-design.md | DONE | CLEAN — unique owner economics design |
| academy-operations-domain.md | DONE | CLEAN — unique academy operations domain |
| school-engagement-domain-design.md | DONE | CLEAN — unique school engagement domain |
| workforce-training-domain-design.md | DONE | CLEAN — unique workforce training domain |
| university-domain-design.md | DONE | CLEAN — unique university domain design |
| ai-tutor-assist-design.md | DONE | CLEAN — unique capability design with MS-AI-01 contract |
| teacher-ai-assist-design.md | DONE | CLEAN — unique teacher AI assist design |
| recommendation-engine-design.md | DONE | CLEAN — unique recommendation engine design |
| learner-risk-insights-design.md | DONE | CLEAN — unique learner risk insights design |
| analytics-intelligence-layer-design.md | DONE | CLEAN — unique analytics intelligence layer design |
| system-of-record-design.md | DONE | CLEAN — unique SoR design (3 pillars: lifecycle, ledger, profile) |
| adaptive-learning-engine.md | DONE | CLEAN — unique adaptive learning component spec (8 components) |
| agi-ready-architecture.md | DONE | CLEAN — unique AGI-compatible layered architecture |
| ai-course-generation-pipeline.md | DONE | CLEAN — unique AI course generation pipeline (4 stages) |
| ai-learning-copilot.md | DONE | CLEAN — unique AI learning assistant capability table |
| capability-gating-model.md | DONE | CLEAN — unique capability gating model (4 components, 3-pass QC) |
| capability-interface-contract.md | DONE | CLEAN — unique capability interface contract |
| cloud-architecture-ems-lms.md | DONE | CLEAN — keep (canonical version) |
| cloud_architecture_lms.md | DONE | ARCHIVE — near-exact duplicate of cloud-architecture-ems-lms.md |
| communication-adapter-contract.md | DONE | CLEAN — unique communication adapter interface contract |
| config-resolution-interface-contract.md | DONE | CLEAN — unique config resolution interface contract |
| content-storage-model.md | DONE | CLEAN — unique content storage model (4 types, bucket/CDN/metadata) |
| event-domain-catalogue.md | DONE | PENDING DECISION — HRIS event taxonomy, different service names from V2 LMS |
| security-architecture.md | DONE | CLEAN — unique security component table (SSO, OAuth, SAML, encryption, audit) |
| service-map.md | DONE | CLEAN — unique service map (12 services, primary entities) |
| duplicate-domains-detection-report.md | DONE | PENDING DECISION — thematic overlap with service-boundary-analysis-report.md and qc_gate_2, not pure subset |
| product-capabilities-matrix.md | DONE | CLEAN — unique capability matrix (15 capabilities, tier coverage map) |
| global-education-model-framework.md | DONE | CLEAN — unique global education hierarchy model (9 levels, 5 institution types) |
| academy-operational-model.md | DONE | CLEAN — unique academy operational model (5-layer workflow chain) |
| tutor-operational-model.md | DONE | CLEAN — unique tutor operational model (5 workflow stages) |
| ai-capability-definition.md | DONE | CLEAN — unique AI capability definition (4 services, integration model, 2-pass QC) |
| terminology-bridge.md | DONE | CLEAN — unique terminology bridge (feature→capability canonical map) |
| market-enforcements-capability-map.md | DONE | CLEAN — unique market enforcements→capability map (7 MS§7 requirements) |
| domain-boundaries-backend.md | DONE | CLEAN — unique domain boundary table (9 domains, service lists) |
| domain-capability-extension-model.md | DONE | CLEAN — unique extension model (B5P* pattern, 4 extensions) |
| enterprise-admin-model.md | DONE | CLEAN — unique enterprise admin model (6 components, actor roles) |
| entitlement-interface-contract.md | DONE | CLEAN — unique entitlement interface contract |
| event-bus-design.md | DONE | PENDING DECISION — HRIS event subset + infrastructure events, partial overlap with event-domain-catalogue.md |
| file-storage-design.md | DONE | CLEAN — unique file storage design (4 bucket types, CDN/signed URL access) |
| data-ownership-rules.md | DONE | CLEAN — stray/irrelevant content (K-12 taxonomy) but not a duplicate of any other file; does not qualify for noise kill |
| media-security-interface-contract.md | DONE | CLEAN — unique media security interface contract |
| multi-branch-rbac-model.md | DONE | CLEAN — unique multi-branch RBAC model (5 role types, BC-BRANCH-01) |
| observability_design.md | DONE | ARCHIVE — fully subsumed by ARCH_08 (4-line table vs 214-line comprehensive doc) |
| offline-sync-interface-contract.md | DONE | CLEAN — unique offline sync interface contract |
| payment-provider-adapter-contract.md | DONE | CLEAN — unique payment provider adapter interface contract |
| platform-evolution-model.md | DONE | CLEAN — unique 20-30 year evolution model (6 pillars, 3-iteration QC) |
| scalability-strategy.md | DONE | CLEAN — unique scalability strategy table (4 components) |
| skills-graph-model.md | DONE | CLEAN — unique skills graph model (15 node types, relationship rules) |
| storage-adapter-interface-contract.md | DONE | CLEAN — unique storage adapter interface contract |
| tenant-customization-catalogue.md | DONE | CLEAN — unique tenant customization config table (5 areas, 22 config keys) |
| tenant-isolation-strategy.md | DONE | CLEAN — unique 3-strategy comparison (shared/schema-per-tenant/database-per-tenant) |
| usage-metering-interface-contract.md | DONE | CLEAN — unique usage metering interface contract |
| data-isolation-analysis-report.md | DONE | CLEAN — unique data isolation audit findings (cross-service link, API contract gap) |
| event-ownership-analysis-report.md | DONE | CLEAN — unique event ownership audit (23 events, naming drift findings) |
| service-boundary-analysis-report.md | DONE | PENDING DECISION — thematic overlap with duplicate-domains-detection-report.md and qc_gate_2, not pure subset |

**Folder result: 2 archive candidates, 1 trim. All 75 files read.**

---

### 05 · docs/specs/ — 63 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| ai-tutor-service-spec.md | DONE | TRIM — guardrail/integration sections duplicate B6P01 content |
| recommendation-service-spec.md | DONE | CLEAN — unique recommendation service spec |
| skill-inference-service-spec.md | DONE | CLEAN — unique skill inference service spec |
| learning-analytics-service-spec.md | DONE | CLEAN — unique learning analytics spec |
| learning-knowledge-graph-spec.md | DONE | CLEAN — unique knowledge graph spec |
| adapter-inventory.md | DONE | CLEAN — unique adapter inventory (4 types, MS-ADAPTER-01 contract) |
| analytics-service-spec.md | DONE | CLEAN — unique analytics service spec |
| assessment-service-spec.md | DONE | CLEAN — unique assessment service spec (SPEC_13) |
| auth-service-spec-v0.md | DONE | CLEAN — self-declared deprecated but has unique content absent from SPEC_01: Ruby module file tree, specific metric label names, 6-step migration plan, rollback strategy, test deliverables |
| auth-service-test-plan.md | DONE | CLEAN — unique auth service test plan |
| capability-domain-map.md | DONE | CLEAN — unique full capability domain map |
| capability-registry-service-spec.md | DONE | CLEAN — unique capability registry service spec |
| compliance-reporting-spec.md | DONE | CLEAN — unique compliance reporting spec |
| content-service-spec.md | DONE | CLEAN — unique content service spec |
| content-versioning-spec.md | DONE | CLEAN — unique content versioning spec |
| capability-inventory.md | DONE | CLEAN — unique feature inventory (8 domains, extension map) |
| billing-and-usage-model.md | DONE | CLEAN — unique billing and usage model |
| economic-capabilities-user-spec.md | DONE | CLEAN — unique economic capabilities spec |
| enterprise-control-spec.md | DONE | CLEAN — unique enterprise control spec (CAP-RBAC, CAP-AUDIT-LOGS, CAP-COMPLIANCE) |
| event-ingestion-spec.md | DONE | CLEAN — unique event ingestion spec (SPEC_15) |
| exam-engine-spec.md | DONE | CLEAN — unique exam engine spec |
| feature-flags-spec.md | DONE | CLEAN — unique feature flags spec |
| financial-ledger-spec.md | DONE | CLEAN — unique financial ledger spec (student vs platform billing split) |
| free-tier-operational-definition.md | DONE | CLEAN — unique free tier definition (BC-FREE-01, quota rules) |
| integration-service-spec.md | DONE | CLEAN — unique integration service spec |
| interaction-layer-spec.md | DONE | CLEAN — unique interaction layer spec |
| learning-analytics-spec.md | DONE | CLEAN — unique learning analytics metric spec (3 metric definitions) |
| learning-path-spec.md | DONE | CLEAN — unique learning path spec |
| lesson-service-spec.md | DONE | CLEAN — unique lesson service spec (SPEC_10) |
| localization-spec.md | DONE | CLEAN — unique localization spec |
| manager-dashboard-spec.md | DONE | CLEAN — unique manager dashboard spec |
| media-pipeline-spec.md | DONE | CLEAN — unique media pipeline spec |
| media-security-spec.md | DONE | CLEAN — unique media security spec |
| monolith-to-services-migration.md | DONE | CLEAN — unique migration plan (6 phases, 13 steps, 2-pass QC) |
| notification-service-spec.md | DONE | CLEAN — unique notification service spec |
| offline-sync-spec.md | DONE | CLEAN — unique offline sync spec |
| onboarding-spec.md | DONE | CLEAN — unique onboarding spec |
| operations-os-spec.md | DONE | CLEAN — unique operations OS spec |
| org-hierarchy-spec.md | DONE | CLEAN — unique org hierarchy spec |
| performance-capabilities-spec.md | DONE | CLEAN — unique performance capabilities spec |
| platform-behavioral-contract.md | DONE | CLEAN — unique platform behavioral contract |
| prerequisite-engine-spec.md | DONE | CLEAN — unique prerequisite engine spec |
| rbac-service-spec-v0.md | DONE | CLEAN — unique RBAC spec |
| reporting-spec.md | DONE | CLEAN — unique reporting spec |
| scorm-runtime-spec.md | DONE | CLEAN — unique SCORM runtime spec |
| session-service-spec.md | DONE | CLEAN — unique session service spec (SPEC_08) |
| skill-analytics-spec.md | DONE | CLEAN — unique skill analytics spec |
| sso-spec.md | DONE | CLEAN — unique SSO spec |
| system-economics-spec.md | DONE | CLEAN — unique system economics spec (CAP-COST-TRACKING, BC-ECON-01) |
| vocational-training-domain-spec.md | DONE | CLEAN — unique vocational training domain spec (6 capabilities) |
| workflow-engine-spec.md | DONE | CLEAN — unique workflow engine spec |
| rbac-service-spec.md | DONE | CLEAN — unique (full API contracts, 6 entities, events); rbac-service-spec-v0.md has role catalog table — neither subsumes the other |
| institution-service-spec.md | DONE | CLEAN — unique institution service spec (lifecycle, hierarchy, tenant linkage, events) |
| program-service-spec.md | DONE | CLEAN — unique program service spec (4 entities, course mapping, institution linkage) |
| cohort-service-spec.md | DONE | CLEAN — unique cohort service spec (3 delivery models, membership, schedule context) |
| course-service-spec.md | DONE | CLEAN — unique course service spec (Rails alignment, publish pipeline, program/session links) |
| enrollment-service-spec.md | DONE | CLEAN — unique enrollment service spec (state machine with guards, bulk assign, 6 event consumers) |
| progress-service-spec.md | DONE | CLEAN — unique progress service spec (4 owned tables, 5 events produced, learning path tracking) |
| certificate-service-spec.md | DONE | CLEAN — unique certificate service spec (template model, verification metadata, badge extension) |
| progress-tracking-spec.md | DONE | CLEAN — 3-event table with consumer_services per event; SPEC_12 has the same events but not the consumer_services column |
| tenant-service-spec-v0.md | DONE | CLEAN — unique tenant service spec (SPEC_04): lifecycle, config, plan linkage, isolation policy |
| user-service-spec.md | DONE | CLEAN — unique user service spec (SPEC_02): identity lifecycle, preferences, identity links |

**Folder result: 0 archive, 1 trim (AI_01). All 63 files read individually.**

---

### 06 · docs/integrations/ — 6 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| hris-sync-spec.md | DONE | CLEAN — unique HRIS sync spec |
| lti-consumer-spec.md | DONE | CLEAN — unique LTI consumer spec |
| lti-provider-spec.md | DONE | CLEAN — unique LTI provider spec |
| standards-support.md | DONE | CLEAN — unique standards support doc (xAPI, SCORM, AICC) |
| webhook-system-spec.md | DONE | CLEAN — unique webhook system spec |
| auth-lifecycle-events.md | DONE | CLEAN — unique auth event envelope schema + 7 events with specific payload fields (auth_method, risk_signal, etc.) not covered by SPEC_01 |

**Folder result: 0 noise items.**

---

### 07 · docs/qc/ — 28 md + 11 py ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| architecture-consistency-check-report.md | DONE | CLEAN — unique Gate 1 findings |
| audit-logging-verification-report.md | DONE | CLEAN — unique content (6 event categories, 4 audit fields, Loki pipeline) |
| auth-service-qc-report.md | DONE | CLEAN — unique two-pass evaluation with specific defect findings |
| B3P05_payment_integration_qc_report.md | DONE | ARCHIVE — fully subsumed by B7P05 |
| capability-registry-validation-report.md | DONE | CLEAN — unique (19 capabilities, 10 domains, dependency resolution) |
| entitlement-resolution-validation-report.md | DONE | CLEAN — unique (segment/plan/country entitlement scenarios) |
| config-resolution-validation-report.md | DONE | CLEAN — unique (3 scenarios, 3 segments, 3 countries) |
| commerce-flow-validation-report.md | DONE | CLEAN — unique (purchase flow, subscription lifecycle, invoice validation) |
| payment-adapter-validation-report.md | DONE | CLEAN — keep (supersedes B3P05) |
| communication-workflow-validation-report.md | DONE | CLEAN — unique (WhatsApp/SMS fallback, adapter-only delivery) |
| delivery-system-validation-report.md | DONE | CLEAN — unique (secure media, offline sync, concurrency) |
| end-to-end-system-validation-report.md | DONE | CLEAN — unique functional roll-up |
| cross-service-dependency-check-report.md | DONE | CLEAN — unique (38 service dependency map) |
| load-test-preparation-report.md | DONE | CLEAN — unique (6 tuning actions, Round 1/2 narrative, NOT subsumed by QC_HARD_01) |
| end-to-end-validation-report.md | DONE | CLEAN — unique (42-service platform coverage, tenant→communication flow) |
| pakistan-wedge-validation-report.md | DONE | CLEAN — unique (10-gate Pakistan wedge validation) |
| system-hardening-report.md | DONE | CLEAN — comprehensive hardening, unique |
| full-system-integration-validation-report.md | DONE | CLEAN — unique integration map |
| feature-completeness-check-report.md | DONE | CLEAN — unique (3 findings: missing gamification, notification overlap, SCORM grouping) |
| event-architecture-validation-report.md | DONE | CLEAN — unique (20 HRIS events, ownership validation) |
| service-boundary-validation-report.md | DONE | CLEAN — unique V2 boundary findings |
| code-structure-validation-report.md | DONE | CLEAN — unique code structure check |
| event-publishing-validation-report.md | DONE | CLEAN — unique SCORM event publishing |
| service-communication-validation-report.md | DONE | CLEAN — unique (6 services checked, 3 violations fixed) |
| service-map-verification-report.md | DONE | CLEAN — unique (unexpected services finding) |
| platform-governor-certification-report.md | DONE | CLEAN — canonical domain ownership matrix |
| system-final-validation-report.md | DONE | CLEAN — unique multi-gate consolidation |
| tenant-model-validation-report.md | DONE | CLEAN — unique tenant findings |
| b7p01_capability_registry_validation.py | DONE | CLEAN — unique validation logic (cycle detection, segment/country alignment) |
| b7p02_entitlement_resolution_validation.py | DONE | CLEAN — unique entitlement resolution logic |
| b7p03_config_resolution_validation.py | DONE | CLEAN — unique config resolution logic (6-layer hierarchy) |
| b7p04_commerce_flow_validation.py | DONE | CLEAN — unique commerce flow logic |
| b7p05_payment_adapter_validation.py | DONE | CLEAN — unique payment validation logic |
| b7p06_communication_workflow_validation.py | DONE | CLEAN — unique (note: _hash_trace() fn duplicated with b7p05, code quality not doc noise) |
| b7p07_delivery_system_validation.py | DONE | CLEAN — unique delivery validation |
| b7p08_end_to_end_system_validation.py | DONE | CLEAN — unique end-to-end validation (4 contexts, 12 checks) |
| load_test_readiness_check.py | DONE | CLEAN — unique (6 infra checks, autoscaling rules) |
| p18_end_to_end_validation.py | DONE | CLEAN — unique (42-service manifest validation, 6 flow scenarios) |
| performance_smoke_tests.py | DONE | CLEAN — unique (6 benchmarks: gateway, auth, courses, enrollment, analytics, event bus) |

**Folder result: 1 archive (B3P05), 0 trims. All 39 files read.**

---

### 08 · docs/market/ — 3 files ✓ COMPLETE

| File | Read | Finding |
|---|---|---|
| pakistan-market-pricing-guide.md | DONE | CLEAN — unique Pakistan pricing intelligence (6 segments, payment method requirements, monetization model comparison) |
| gtm-entry-strategy.md | DONE | CLEAN — unique GTM entry strategy (5-phase expansion, academy wedge, anti-patterns) |
| competitive-intelligence.md | DONE | CLEAN — unique competitor analysis (local + global, gap map, Moodle replacement opportunity) |

**Folder result: 0 noise items. All 3 files read.**

---

## Confirmed Noise Findings (All 9 Folders Read — Final, Verified 2026-05-18)

| # | File | Action | Archived To | Completed |
|---|---|---|---|---|
| 1 | architecture/cloud_architecture_lms.md | ARCHIVED | architecture/_archive/cloud_architecture_lms.md | 2026-05-18 |
| 2 | architecture/observability_design.md | ARCHIVED | architecture/_archive/observability_design.md | 2026-05-18 |
| 3 | qc/B3P05_payment_integration_qc_report.md | ARCHIVED | qc/_archive/B3P05_payment_integration_qc_report.md | 2026-05-18 |

**Note:** data-ownership-rules.md and auth-service-spec-v0.md were removed — stray/deprecated ≠ noise kill without duplication evidence. DATA_02, ARCH_05, AI_01 are TRIMS (normalisation phase, out of scope for noise kill).
**Scope corrected 2026-05-18:** 203 active .md files audited (9 previously unscanned files confirmed CLEAN — 6 in docs/data/, 3 in docs/market/). Prior claim of 219 was a miscounted mixed-type total; canonical count is 203 .md files.

---

## Pending Decisions (Not noise kill — deferred)

| File | Issue |
|---|---|
| architecture/event-domain-catalogue.md | HRIS taxonomy mismatch — normalisation phase |
| architecture/event-bus-design.md | Partial HRIS overlap — normalisation phase |
| architecture/duplicate-domains-detection-report.md | Thematic overlap with validate_service_boundaries + qc_gate_2, not pure subset |
| architecture/service-boundary-analysis-report.md | Thematic overlap with detect_duplicate_domains + qc_gate_2, not pure subset |
