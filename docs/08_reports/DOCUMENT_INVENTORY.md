# DOCUMENT_INVENTORY

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-22
Owner: AI

Total documents inventoried: 355 (251 in docs/, 104 in workspace/)
Scope: All .md files in D:\SaaS\LMS\Repo\docs\ and D:\SaaS\LMS\workspace\

---

## INVENTORY KEY

| Classification | Code | Description |
|---|---|---|
| Authority Document | AUTH | Single authoritative source for an information domain |
| Supporting Reference | SUPP | Provides detail that supports an authority document |
| Operational Artifact | OPS | Tracks active operational state (progress, pending, snapshot) |
| Historical Record | HIST | Session outputs and prior-phase audit work; retained for traceability |
| Generated Report | RPT | Point-in-time validation, QC, or analysis output |
| Working Draft | DRAFT | In-progress documentation; not yet authoritative |
| Retired Document | RETD | Superseded; no longer valid for decisions |
| Duplicate Document | DUPL | Duplicate of another document; candidate for removal |
| Obsolete Document | OBSOL | Naming or structure artifact from prior phase; content stale |

---

## SECTION 1 — GOVERNANCE AUTHORITY TIER

Path prefix: docs/00_authority/, docs/06_decisions/, docs/07_governance/

| File | Classification | Description |
|---|---|---|
| docs/00_authority/PROJECT_CHARTER.md | AUTH | Primary authority: project identity, phase status, principles, tech stack, platform purpose |
| docs/00_authority/DOMAIN_MODEL.md | AUTH | Primary authority: bounded contexts, aggregate roots, service-domain assignments, config hierarchy |
| docs/00_authority/FEATURE_SCOPE.md | AUTH | Primary authority: feature inventory by domain, service-to-feature mapping |
| docs/00_authority/PRODUCT_WORKFLOWS.md | AUTH | Primary authority: core platform workflows WF-001 through WF-010 |
| docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md | DRAFT | Draft authority: cross-layer traceability; backend column populated, frontend TBD |
| docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md | AUTH | Authority for all architectural decisions in Phase 1; 8-principle list; config model |
| docs/07_governance/AI_OPERATING_CONTEXT.md | AUTH | AI session rules, frozen decisions, active blockers GEB-001 through GEB-008 |
| docs/07_governance/DECISION_ESCALATION_MATRIX.md | AUTH | Decision routing rules, escalation thresholds |

---

## SECTION 2 — GOVERNANCE REPORTS TIER

Path prefix: docs/08_reports/

| File | Classification | Description |
|---|---|---|
| docs/08_reports/GOVERNANCE_IMPLEMENTATION_REPORT.md | RPT | Phase 1 governance implementation summary |
| docs/08_reports/GOVERNANCE_CONSISTENCY_AUDIT.md | RPT | 33-finding audit of governance docs (3 Critical, 7 High, 9 Medium, 14 Low) |
| docs/08_reports/REMEDIATION_REPORT.md | RPT | Remediation status: 31 resolved, 2 deferred |
| docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md | RPT | Service-to-spec coverage: 45 specced, 24 unspecced of 69 HTTP services |
| docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md | RPT | Living register of architectural gaps (GEB-001–008) |
| docs/08_reports/RECOMMENDED_ADR_ROADMAP.md | RPT | Roadmap for future ADRs (R-001 through R-010+) |

---

## SECTION 3 — CANONICAL ANCHORS TIER

Path prefix: docs/anchors/

| File | Classification | Description |
|---|---|---|
| docs/anchors/event-envelope.md | AUTH | Canonical 7-field event envelope schema |
| docs/anchors/tenant-contract.md | AUTH | Canonical 6-field tenant payload |
| docs/anchors/capability-resolution.md | AUTH | Capability resolution flow — NEEDS UPDATE: still documents 6-level config hierarchy including plan + runtime_override |
| docs/anchors/country-layer-architecture.md | AUTH | Canonical adapter-binding pattern for country layer |
| docs/anchors/doc-precedence.md | OBSOL | Pre-governance priority model (BATCH > SPEC > ARCH > Legacy) — does not reflect docs/00_authority/ tier |

---

## SECTION 4 — SERVICE SPECIFICATION TIER

Path prefix: docs/specs/

| File | Classification | Description |
|---|---|---|
| docs/specs/adapter-inventory.md | SUPP | Inventory of all adapter types across services |
| docs/specs/ai-tutor-service-spec.md | AUTH | Service contract: AI tutor service |
| docs/specs/analytics-service-spec.md | AUTH | Service contract: analytics service |
| docs/specs/api-key-service-spec.md | AUTH | Service contract: API key management |
| docs/specs/assessment-service-spec.md | AUTH | Service contract: assessment service |
| docs/specs/attempt-service-spec.md | AUTH | Service contract: attempt service |
| docs/specs/auth-service-spec.md | AUTH | Service contract: auth service (v2 canonical — base path /api/v2/auth) |
| docs/specs/auth-service-spec-v0.md | RETD | Retired v0 auth-service-spec; superseded by auth-service-spec.md |
| docs/specs/auth-service-test-plan.md | SUPP | Test plan specific to auth service |
| docs/specs/badge-service-spec.md | AUTH | Service contract: badge service |
| docs/specs/billing-and-usage-model.md | AUTH | Service contract: billing and usage model |
| docs/specs/capability-domain-map.md | SUPP | Maps capabilities to domains (supporting DOMAIN_MODEL.md) |
| docs/specs/capability-inventory.md | SUPP | Full capability inventory (supporting FEATURE_SCOPE.md) |
| docs/specs/capability-registry-service-spec.md | AUTH | Service contract: capability registry service |
| docs/specs/catalog-service-spec.md | AUTH | Service contract: catalog service |
| docs/specs/certificate-service-spec.md | AUTH | Service contract: certificate service (canonical) |
| docs/specs/cohort-service-spec.md | AUTH | Service contract: cohort service |
| docs/specs/course-service-spec.md | AUTH | Service contract: course service |
| docs/specs/department-service-spec.md | AUTH | Service contract: department service |
| docs/specs/economic-capabilities-user-spec.md | AUTH | User-facing spec: economic capabilities for academy owners |
| docs/specs/email-service-spec.md | AUTH | Service contract: email service |
| docs/specs/enrollment-service-spec.md | AUTH | Service contract: enrollment service |
| docs/specs/enterprise-control-spec.md | AUTH | Service contract: enterprise control |
| docs/specs/event-ingestion-spec.md | AUTH | Service contract: event ingestion |
| docs/specs/exam-engine-spec.md | AUTH | Service contract: exam engine |
| docs/specs/financial-ledger-spec.md | AUTH | Service contract: financial ledger |
| docs/specs/free-tier-operational-definition.md | AUTH | Operational definition of free tier behavior |
| docs/specs/GEN_14_certificate_service.md | DUPL | Duplicate of certificate-service-spec.md with legacy naming prefix |
| docs/specs/group-service-spec.md | AUTH | Service contract: group service |
| docs/specs/hr-helpdesk-service-spec.md | AUTH | Service contract: HR helpdesk service |
| docs/specs/institution-service-spec.md | AUTH | Service contract: institution service |
| docs/specs/integration-service-spec.md | AUTH | Service contract: integration service |
| docs/specs/interaction-layer-spec.md | AUTH | Service contract: interaction layer service |
| docs/specs/learning-analytics-service-spec.md | AUTH | Service contract: learning analytics service |
| docs/specs/learning-knowledge-graph-spec.md | AUTH | Service contract: learning knowledge graph |
| docs/specs/media-pipeline-spec.md | AUTH | Service contract: media-service (spec retains pipeline name; service canonical name is media-service) |
| docs/specs/media-security-spec.md | AUTH | Service contract: media security |
| docs/specs/monolith-to-services-migration.md | HIST | Migration strategy from Rails monolith to microservices — historical plan |
| docs/specs/notification-service-spec.md | AUTH | Service contract: notification service |
| docs/specs/offline-sync-spec.md | AUTH | Service contract: offline sync service |
| docs/specs/onboarding-spec.md | AUTH | Service contract: onboarding service (7-step automated onboarding) |
| docs/specs/operations-os-spec.md | AUTH | Service contract: operations OS |
| docs/specs/platform-behavioral-contract.md | SUPP | Repo-facing translation of behavioral authority into named contracts |
| docs/specs/program-service-spec.md | AUTH | Service contract: program service |
| docs/specs/progress-service-spec.md | AUTH | Service contract: progress service |
| docs/specs/push-service-spec.md | AUTH | Service contract: push notification service |
| docs/specs/quiz-engine-spec.md | AUTH | Service contract: quiz engine |
| docs/specs/rbac-service-spec.md | AUTH | Service contract: RBAC service (canonical) |
| docs/specs/recommendation-service-spec.md | AUTH | Service contract: recommendation service |
| docs/specs/session-service-spec.md | AUTH | Service contract: session service |
| docs/specs/skill-inference-service-spec.md | AUTH | Service contract: skill inference service |
| docs/specs/sso-spec.md | AUTH | Service contract: SSO |
| docs/specs/system-economics-spec.md | AUTH | Service contract: system economics service |
| docs/specs/tenant-service-spec.md | AUTH | Service contract: tenant service (canonical) |
| docs/specs/tenant-service-spec-v0.md | RETD | Retired v0 tenant-service-spec; superseded by tenant-service-spec.md |
| docs/specs/user-service-spec.md | AUTH | Service contract: user service |
| docs/specs/vocational-training-domain-spec.md | AUTH | Domain spec: vocational training vertical |
| docs/specs/workflow-engine-spec.md | AUTH | Service contract: workflow engine |

### Section 4a — Feature Specs (docs/specs/features/)

| File | Classification | Description |
|---|---|---|
| docs/specs/features/compliance-reporting-spec.md | AUTH | Feature spec: compliance reporting |
| docs/specs/features/content-service-spec.md | AUTH | Feature spec: content service |
| docs/specs/features/content-versioning-spec.md | AUTH | Feature spec: content versioning |
| docs/specs/features/feature-flags-spec.md | AUTH | Feature spec: feature flags |
| docs/specs/features/hris-sync-service-spec.md | AUTH | Feature spec: HRIS sync service |
| docs/specs/features/learning-analytics-spec.md | AUTH | Feature spec: learning analytics |
| docs/specs/features/learning-path-spec.md | AUTH | Feature spec: learning paths |
| docs/specs/features/lesson-service-spec.md | AUTH | Feature spec: lesson service |
| docs/specs/features/localization-spec.md | AUTH | Feature spec: localization |
| docs/specs/features/manager-dashboard-spec.md | AUTH | Feature spec: manager dashboard |
| docs/specs/features/org-hierarchy-spec.md | AUTH | Feature spec: org hierarchy |
| docs/specs/features/performance-capabilities-spec.md | AUTH | Feature spec: performance capabilities |
| docs/specs/features/prerequisite-engine-spec.md | AUTH | Feature spec: prerequisite engine |
| docs/specs/features/progress-tracking-spec.md | AUTH | Feature spec: progress tracking |
| docs/specs/features/rbac-service-spec-v0.md | RETD | Retired v0 RBAC spec; superseded by docs/specs/rbac-service-spec.md |
| docs/specs/features/reporting-spec.md | AUTH | Feature spec: reporting |
| docs/specs/features/review-service-spec.md | AUTH | Feature spec: review service |
| docs/specs/features/scorm-runtime-spec.md | AUTH | Feature spec: SCORM runtime |
| docs/specs/features/skill-analytics-spec.md | AUTH | Feature spec: skill analytics |

---

## SECTION 5 — INTERFACE CONTRACTS TIER

Path prefix: docs/contracts/

| File | Classification | Description |
|---|---|---|
| docs/contracts/capability-gating-model.md | AUTH | Contract: capability gating logic and enforcement |
| docs/contracts/capability-interface-contract.md | AUTH | Contract: capability interface |
| docs/contracts/communication-adapter-contract.md | AUTH | Contract: communication adapter |
| docs/contracts/config-resolution-interface-contract.md | AUTH | Contract: config resolution interface |
| docs/contracts/content-storage-model.md | AUTH | Contract: content storage model |
| docs/contracts/entitlement-interface-contract.md | AUTH | Contract: entitlement interface |
| docs/contracts/media-security-interface-contract.md | AUTH | Contract: media security interface |
| docs/contracts/offline-sync-interface-contract.md | AUTH | Contract: offline sync interface |
| docs/contracts/payment-provider-adapter-contract.md | AUTH | Contract: payment provider adapter |
| docs/contracts/storage-adapter-interface-contract.md | AUTH | Contract: storage adapter interface |
| docs/contracts/usage-metering-interface-contract.md | AUTH | Contract: usage metering interface |

---

## SECTION 6 — ARCHITECTURE SUPPORTING DOCS

Path prefix: docs/architecture/

### 6a — Design Architecture

| File | Classification | Description |
|---|---|---|
| docs/architecture/core-system-architecture.md | SUPP | Core system architecture — superseded by PROJECT_CHARTER for identity; retained for Rails heritage detail |
| docs/architecture/microservice-boundary-map.md | SUPP | Microservice boundary map — supporting detail for DOMAIN_MODEL.md |
| docs/architecture/domain-driven-design-map.md | SUPP | DDD map — supporting detail for DOMAIN_MODEL.md (may have older bounded context definitions) |
| docs/architecture/service-data-ownership-rules.md | SUPP | Data ownership rules — supporting for DOMAIN_MODEL.md §4 |
| docs/architecture/event-driven-architecture.md | SUPP | Event architecture detail — supporting for event-envelope.md anchor |
| docs/architecture/api-versioning-strategy.md | AUTH | API versioning strategy — sole authority on this topic |
| docs/architecture/multi-tenant-isolation-model.md | SUPP | Multi-tenant isolation — supporting for tenant-contract.md anchor |
| docs/architecture/observability-architecture.md | SUPP | Observability stack design |
| docs/architecture/cloud-architecture-ems-lms.md | SUPP | Cloud architecture for EMS/LMS overlay |
| docs/architecture/domain-boundaries-backend.md | SUPP | Backend domain boundary analysis |
| docs/architecture/event-bus-design.md | SUPP | Event bus implementation design |
| docs/architecture/event-consumer-infrastructure.md | SUPP | Event consumer infrastructure patterns |
| docs/architecture/event-domain-catalogue.md | SUPP | Catalogue of event domains |
| docs/architecture/platform-evolution-model.md | SUPP | Platform evolution roadmap model |
| docs/architecture/scalability-strategy.md | SUPP | Scalability strategy |
| docs/architecture/security-architecture.md | SUPP | Security architecture design |
| docs/architecture/service-map.md | SUPP | Service map (older service names; DOCUMENTATION_COVERAGE_MATRIX.md is now canonical) |
| docs/architecture/tenant-customization-catalogue.md | SUPP | Tenant customization options catalogue |
| docs/architecture/tenant-isolation-strategy.md | SUPP | Tenant isolation strategy |

### 6b — Architecture Audit Reports

| File | Classification | Description |
|---|---|---|
| docs/architecture/architecture-full-audit-report.md | RPT | Full architecture audit — Historical |
| docs/architecture/circular-dependencies-audit-report.md | RPT | Circular dependency detection — Historical |
| docs/architecture/duplicate-domains-detection-report.md | RPT | Domain overlap detection — Historical |
| docs/architecture/data-isolation-analysis-report.md | RPT | Data isolation validation — Historical |
| docs/architecture/event-ownership-analysis-report.md | RPT | Event ownership audit — Historical |
| docs/architecture/service-boundary-analysis-report.md | RPT | Service boundary validation — Historical |

---

## SECTION 7 — API DOCS

Path prefix: docs/api/

| File | Classification | Description |
|---|---|---|
| docs/api/analytics-api.md | SUPP | Analytics API surface (supplemental to analytics-service-spec.md) |
| docs/api/api-contract-validation-report.md | RPT | API contract validation — Historical |
| docs/api/api-gateway-design.md | SUPP | API gateway design patterns |
| docs/api/api-spec-validation-report.md | RPT | API spec validation — Historical |
| docs/api/auth-service-api.md | SUPP | Auth service API detail (supplemental to auth-service-spec.md) |
| docs/api/content-api.md | SUPP | Content API surface |
| docs/api/core-rest-api.md | SUPP | Core REST API patterns |
| docs/api/integration-api.md | SUPP | Integration API surface |

---

## SECTION 8 — DESIGN DOCS

Path prefix: docs/designs/ — All 45 documents are Supporting References.

| File | Classification | Notes |
|---|---|---|
| docs/designs/academy-commerce-extensions.md | SUPP | Commerce extensions design |
| docs/designs/academy-operational-model.md | SUPP | Academy ops operational model |
| docs/designs/academy-operations-domain.md | SUPP | Academy operations domain design |
| docs/designs/adaptive-learning-engine.md | SUPP | Adaptive learning engine design |
| docs/designs/agi-ready-architecture.md | SUPP | AGI-ready architecture design |
| docs/designs/ai-capability-definition.md | SUPP | AI capability definition |
| docs/designs/ai-course-generation-pipeline.md | SUPP | AI course generation pipeline (referenced by course-generation-service README) |
| docs/designs/ai-learning-copilot.md | SUPP | AI learning copilot design |
| docs/designs/ai-tutor-assist-design.md | SUPP | AI tutor assist design |
| docs/designs/analytics-intelligence-layer-design.md | SUPP | Analytics intelligence layer |
| docs/designs/audit-policy-layer-design.md | SUPP | Audit policy layer design |
| docs/designs/auth-rsa-key-design.md | SUPP | RSA key management design |
| docs/designs/capability-registry-service-design.md | SUPP | Capability registry service design |
| docs/designs/catalog-service-design.md | SUPP | Catalog service design |
| docs/designs/checkout-service-design.md | SUPP | Checkout service design |
| docs/designs/commerce-domain-architecture.md | SUPP | Commerce domain architecture |
| docs/designs/config-service-design.md | SUPP | Config service design |
| docs/designs/data-ownership-rules.md | SUPP | Data ownership rules (potential duplicate of architecture/service-data-ownership-rules.md) |
| docs/designs/domain-capability-extension-model.md | SUPP | Domain capability extension model |
| docs/designs/enterprise-admin-model.md | SUPP | Enterprise admin model |
| docs/designs/entitlement-service-design.md | SUPP | Entitlement service design |
| docs/designs/feature-flag-system-design.md | SUPP | Feature flag system design |
| docs/designs/file-storage-design.md | SUPP | File storage design |
| docs/designs/global-education-model-framework.md | SUPP | Global education model framework |
| docs/designs/invoice-billing-service-design.md | SUPP | Invoice/billing service design |
| docs/designs/learner-risk-insights-design.md | SUPP | Learner risk insights design |
| docs/designs/market-enforcements-capability-map.md | SUPP | Market enforcement capability map |
| docs/designs/multi-branch-rbac-model.md | SUPP | Multi-branch RBAC model |
| docs/designs/owner-economics-service-design.md | SUPP | Owner economics service design |
| docs/designs/payment-service-design.md | SUPP | Payment service design |
| docs/designs/platform-integration-layer-design.md | SUPP | Platform integration layer design |
| docs/designs/product-capabilities-matrix.md | SUPP | Product capabilities matrix |
| docs/designs/recommendation-engine-design.md | SUPP | Recommendation engine design |
| docs/designs/revenue-service-design.md | SUPP | Revenue service design |
| docs/designs/school-engagement-domain-design.md | SUPP | School engagement domain design |
| docs/designs/skills-graph-model.md | SUPP | Skills graph model design |
| docs/designs/subscription-service-design.md | SUPP | Subscription service design |
| docs/designs/system-of-record-design.md | SUPP | System of record design |
| docs/designs/teacher-ai-assist-design.md | SUPP | Teacher AI assist design |
| docs/designs/tenant-extension-model.md | SUPP | Tenant extension model (supplies discriminator fields referenced by capability-resolution.md) |
| docs/designs/terminology-bridge.md | SUPP | Terminology bridge across doc generations |
| docs/designs/tutor-operational-model.md | SUPP | Tutor operational model |
| docs/designs/university-domain-design.md | SUPP | University domain design |
| docs/designs/usage-metering-service-design.md | SUPP | Usage metering service design |
| docs/designs/workforce-training-domain-design.md | SUPP | Workforce training domain design |

---

## SECTION 9 — DATA SCHEMAS

Path prefix: docs/data/

| File | Classification | Description |
|---|---|---|
| docs/data/ai-interaction-schema.md | SUPP | Schema: AI interaction data |
| docs/data/analytics-data-model.md | SUPP | Data model: analytics |
| docs/data/assessment-data-schema.md | SUPP | Schema: assessment data |
| docs/data/auth-service-storage-contract.md | AUTH | Storage contract: auth service (authoritative for auth data model) |
| docs/data/cohort-batch-schema.md | SUPP | Schema: cohort batch |
| docs/data/core-lms-schema.md | SUPP | Core LMS entity schema (Rails heritage entities) |
| docs/data/database-schema-validation-report.md | RPT | Database schema validation — Historical |
| docs/data/data-model-validation-report.md | RPT | Data model validation — Historical |
| docs/data/global-education-schema.md | SUPP | Schema: global education model |
| docs/data/institution-hierarchy-schema.md | SUPP | Schema: institution hierarchy |
| docs/data/knowledge-graph-schema.md | SUPP | Schema: knowledge graph |
| docs/data/learning-data-model-overview.md | SUPP | Learning data model overview |
| docs/data/learning-event-schema.md | SUPP | Schema: learning events |

---

## SECTION 10 — INTEGRATIONS

Path prefix: docs/integrations/

| File | Classification | Description |
|---|---|---|
| docs/integrations/auth-lifecycle-events.md | AUTH | Auth lifecycle event contracts |
| docs/integrations/hris-sync-spec.md | AUTH | HRIS sync integration spec |
| docs/integrations/lti-consumer-spec.md | AUTH | LTI consumer integration spec |
| docs/integrations/lti-provider-spec.md | AUTH | LTI provider integration spec |
| docs/integrations/standards-support.md | SUPP | Supported integration standards overview |
| docs/integrations/webhook-system-spec.md | AUTH | Webhook system spec |

---

## SECTION 11 — MARKET DOCS

Path prefix: docs/market/

| File | Classification | Description |
|---|---|---|
| docs/market/competitive-intelligence.md | AUTH | Competitive intelligence (no other market authority) |
| docs/market/gtm-entry-strategy.md | AUTH | Go-to-market strategy |
| docs/market/pakistan-market-pricing-guide.md | AUTH | Pakistan market pricing guide |

---

## SECTION 12 — QC REPORTS

Path prefix: docs/qc/ — All are Generated Reports (point-in-time).

| File | Classification |
|---|---|
| docs/qc/_archive/B3P05_payment_integration_qc_report.md | HIST |
| docs/qc/architecture-consistency-check-report.md | RPT |
| docs/qc/audit-logging-verification-report.md | RPT |
| docs/qc/auth-service-qc-report.md | RPT |
| docs/qc/capability-registry-validation-report.md | RPT |
| docs/qc/code-structure-validation-report.md | RPT |
| docs/qc/commerce-flow-validation-report.md | RPT |
| docs/qc/communication-workflow-validation-report.md | RPT |
| docs/qc/config-resolution-validation-report.md | RPT |
| docs/qc/cross-service-dependency-check-report.md | RPT |
| docs/qc/delivery-system-validation-report.md | RPT |
| docs/qc/end-to-end-system-validation-report.md | RPT |
| docs/qc/end-to-end-validation-report.md | RPT |
| docs/qc/entitlement-resolution-validation-report.md | RPT |
| docs/qc/event-architecture-validation-report.md | RPT |
| docs/qc/event-publishing-validation-report.md | RPT |
| docs/qc/feature-completeness-check-report.md | RPT |
| docs/qc/full-system-integration-validation-report.md | RPT |
| docs/qc/load-test-preparation-report.md | RPT |
| docs/qc/pakistan-wedge-validation-report.md | RPT |
| docs/qc/payment-adapter-validation-report.md | RPT |
| docs/qc/platform-governor-certification-report.md | RPT |
| docs/qc/service-boundary-validation-report.md | RPT |
| docs/qc/service-communication-validation-report.md | RPT |
| docs/qc/service-map-verification-report.md | RPT |
| docs/qc/system-final-validation-report.md | RPT |
| docs/qc/system-hardening-report.md | RPT |
| docs/qc/tenant-model-validation-report.md | RPT |

---

## SECTION 13 — RETIRED AND ARCHIVED DOCS

Path prefix: docs/_archive/, docs/governance/

| File | Classification | Description |
|---|---|---|
| docs/_archive/audit_logging.md | RETD | Superseded by qc/ reports and architecture docs |
| docs/_archive/cloud_architecture_lms.md | RETD | Superseded by architecture/cloud-architecture-ems-lms.md |
| docs/_archive/cohort_spec.md | RETD | Superseded by specs/cohort-service-spec.md |
| docs/_archive/config_service.md | RETD | Superseded by designs/config-service-design.md and specs |
| docs/_archive/core_system_architecture.md | RETD | Superseded by architecture/core-system-architecture.md |
| docs/_archive/course_service_spec.md | RETD | Superseded by specs/course-service-spec.md |
| docs/_archive/event_driven_architecture.md | RETD | Superseded by architecture/event-driven-architecture.md |
| docs/_archive/feature_inventory.md | RETD | Superseded by FEATURE_SCOPE.md |
| docs/_archive/microservice_boundaries.md | RETD | Superseded by architecture/microservice-boundary-map.md |
| docs/_archive/observability_design.md | RETD | Superseded by architecture/observability-architecture.md |
| docs/governance/doc-catalogue.md | OBSOL | v7.3 master catalogue; superseded by DOCUMENTATION_COVERAGE_MATRIX.md + this normalization |
| docs/governance/_archive/backend-restructuring.md | HIST | Backend restructuring record May 2026 |
| docs/governance/_archive/docs-rename-map.md | HIST | 204-file rename map — traceability record |
| docs/governance/_archive/noise-kill-tracker.md | HIST | 219-doc noise-kill record |
| docs/governance/_archive/normalisation-tracker.md | HIST | 124-finding Phase 2 normalisation tracker |
| docs/governance/_archive/tracker.md | HIST | Repo restructuring tracker |

---

## SECTION 14 — WORKSPACE: FOUNDATION AND OPS

| File | Classification | Description |
|---|---|---|
| workspace/foundation/product-build-spec.md | HIST | Former Master Spec authority — superseded by docs/00_authority/PROJECT_CHARTER.md |
| workspace/foundation/behavioral-spec.md | HIST | Former behavioral authority — superseded by docs/00_authority/PRODUCT_WORKFLOWS.md and FEATURE_SCOPE.md |
| workspace/foundation/market-research.md | HIST | Market research underlying GTM strategy |
| workspace/ops/snapshot.md | OPS | Session snapshot — current project state |
| workspace/ops/progress.md | OPS | Normalisation phase tracker |
| workspace/ops/pending.md | OPS | Pending work register (BOS gaps MO-001–MO-044) |
| workspace/ops/gap-register.md | OPS | BOS overlay gap register (18 gaps) |

---

## SECTION 15 — WORKSPACE: DESIGN SYSTEM AND PAGE DEFINITIONS

| File | Classification | Description |
|---|---|---|
| workspace/design-system/design-system.md | DRAFT | Design system — pre-Frontend Authority phase |
| workspace/design-system/behavior-to-ui.md | DRAFT | Behavior-to-UI mapping — pre-Frontend Authority phase |
| workspace/design-system/framework-gap-register.md | DRAFT | Frontend framework gap register |
| workspace/page-definitions/entity-contracts.md | DRAFT | Entity contracts for UI — pre-Frontend Authority phase |
| workspace/page-definitions/page-inventory.md | DRAFT | Page inventory — pre-Frontend Authority phase |
| workspace/page-definitions/ui-framework.md | DRAFT | UI framework definition |

---

## SECTION 16 — WORKSPACE: AUDIT FILES

| File | Classification | Description |
|---|---|---|
| workspace/audit/audit-master-register.md | HIST | Master register of all audit findings across phases |
| workspace/audit/backend-audit-plan.md | HIST | Backend audit plan |
| workspace/audit/catalogue-anchored-audit-2026-05-31.md | HIST | Catalogue-anchored audit 2026-05-31 |
| workspace/audit/doc-code-audit-2026-05-31.md | HIST | Doc-to-code audit 2026-05-31 |
| workspace/audit/full-alignment-register.md | HIST | Full alignment register from prior phases |
| workspace/audit/html-audit-approach.md | HIST | HTML audit methodology |
| workspace/audit/inconsistency-register.md | HIST | Inconsistency register from prior phases |

---

## SECTION 17 — WORKSPACE: ARCHIVED FILES

| File | Classification | Description |
|---|---|---|
| workspace/archive/ARCHIVE-README.md | RETD | Archive README |
| workspace/archive/code-gap-register.md | HIST | Code gap register 111 gaps CGAP-001 through MO-044 |
| workspace/archive/doc-catalogue-v4.0.md | RETD | Prior catalogue v4.0 — superseded by doc-catalogue.md v7.3 and now DOCUMENTATION_COVERAGE_MATRIX.md |
| workspace/archive/icon-system-v1.md | HIST | Icon system v1 design — pre-Frontend Authority phase |
| workspace/archive/ms-overlay-register.md | HIST | Master Spec overlay gap register CLOSED 2026-04-11 |
| workspace/archive/normalisation-findings.md | HIST | 166 Phase 2 normalisation findings |
| workspace/archive/pattern-checklist.md | HIST | Pattern checklist |
| workspace/archive/stage3-read-tracker.md | HIST | Stage 3 read tracker — 313/313 files |

---

## SECTION 18 — WORKSPACE: SESSION OUTPUTS

All session output files are HIST (Historical Record). They are the audit trail of discovery and decision-making across sessions U0–U11.

| Session | Files | Key Outputs |
|---|---|---|
| workspace/sessions/U0/ | 5 | REPOSITORY_REALITY_REPORT, REPOSITORY_TREE_INVENTORY, WORKSPACE_BASELINE_AUDIT, CURRENT_PROJECT_STATUS |
| workspace/sessions/U0-U9/ | 7 | Forensic audit, contradiction register, completeness scorecard, findings register |
| workspace/sessions/U1/ | 8 | API_INVENTORY, ENTITY_INVENTORY, FEATURE_INVENTORY, MODULE_INVENTORY, ROLE_PERMISSION_INVENTORY, WORKFLOW_INVENTORY, AUTHORITY_RECONSTRUCTION_REPORT |
| workspace/sessions/U2/ | 4 | DOC_CATALOGUE, DOCUMENT_CLASSIFICATION_MATRIX v1, DOCUMENT_OWNERSHIP_MATRIX |
| workspace/sessions/U3/ | 5 | DOC_CONFLICT_REGISTER, DOC_DUPLICATION_REGISTER, DOC_NORMALIZATION_REPORT v1, DOC_STALE_REFERENCE_REPORT |
| workspace/sessions/U4/ | 5 | WORKSPACE_RESTRUCTURING_PLAN, FILE_RELOCATION_MATRIX, FOLDER_PURPOSE_MATRIX, BREAKAGE_RISK_REPORT |
| workspace/sessions/U5/ | 5 | RESTRUCTURING_EXECUTION_REPORT, POST_RESTRUCTURE_VALIDATION, STALE_LINK_FIX_REPORT |
| workspace/sessions/U6/ | 5 | DOC_CODE_DELTA_REPORT, DELTA_SUMMARY_REPORT, STALE_DOC_CLAIMS_REGISTER, UNDOCUMENTED_CODE_REGISTER |
| workspace/sessions/U7/ | 3 | BACKEND_DOC_ALIGNMENT_STATUS, DOC_CODE_REMEDIATION_REPORT |
| workspace/sessions/U8/ | 4 | C_DRIVE_LEAKAGE_AUDIT, SEALED_WORKSPACE_VALIDATION, WORKSPACE_SEALING_REPORT |
| workspace/sessions/U9/ | 6 | TEST_SUITE_PLAN, SECURITY_TEST_PLAN, LOAD_TEST_PLAN, HARDENING_PLAN, VALIDATION_COMMANDS |
| workspace/sessions/U10/ | 10 | SERVICE_CLASSIFICATION_MATRIX, TWO_LAYER_ARCHITECTURE_REPORT, COMMERCE_FORENSIC_REPORT, SERVICE_INVENTORY, ARCHITECTURE_DECISION_REPORT |
| workspace/sessions/U11/ | 6 | GOVERNANCE_ENTRY_BLOCKERS (GEB-001–008), REMEDIATION_PLAN, FINAL_RECOMMENDATION, TEST_REQUIREMENTS |
| workspace/sessions/GOVERNANCE-P1/ | 1 | GOVERNANCE IMPLEMENTATION PHASE 1 prompt |
| workspace/sessions/GOVERNANCE-VALIDATION-P1/ | 1 | PHASE 1 GOVERNANCE VALIDATION prompt |
| workspace/sessions/AUDIT-REMEDIATION/ | 1 | AUDIT REMEDIATION prompt |

---

## SECTION 19 — EMPTY PLACEHOLDER DIRECTORIES

Created by workspace restructuring (U4/U5); no content yet.

| Directory | Purpose (Planned) | Status |
|---|---|---|
| docs/01_backend/ | Backend authority docs | Empty — awaiting Backend Authority Capture |
| docs/02_frontend/ | Frontend authority docs | Empty — awaiting Frontend Authority Capture |
| docs/03_fullstack_contracts/ | Full-stack contracts | Empty — awaiting Phase 2/3 |
| docs/04_testing/ | Testing authority docs | Empty — awaiting Testing Authority Capture |
| docs/05_deployment/ | Deployment authority docs | Empty — awaiting Deployment Authority Capture |

---

## DOCUMENT COUNT SUMMARY

| Category | Count | Classification Breakdown |
|---|---|---|
| Governance Authority (00_authority, 06_decisions, 07_governance) | 8 | 7 AUTH + 1 DRAFT |
| Governance Reports (08_reports) | 6 | 6 RPT |
| Canonical Anchors (anchors/) | 5 | 4 AUTH + 1 OBSOL |
| Service Specs (specs/) | 58 | 53 AUTH + 2 RETD + 1 DUPL + 2 SUPP/HIST |
| Feature Specs (specs/features/) | 19 | 18 AUTH + 1 RETD |
| Interface Contracts (contracts/) | 11 | 11 AUTH |
| Architecture Design (architecture/) | 19 | 1 AUTH + 12 SUPP + 6 RPT |
| API Docs (api/) | 8 | 2 RPT + 6 SUPP |
| Design Docs (designs/) | 45 | 45 SUPP |
| Data Schemas (data/) | 13 | 1 AUTH + 10 SUPP + 2 RPT |
| Integrations (integrations/) | 6 | 5 AUTH + 1 SUPP |
| Market Docs (market/) | 3 | 3 AUTH |
| QC Reports (qc/) | 28 | 27 RPT + 1 HIST |
| Retired/Archive docs (docs/) | 16 | 10 RETD + 6 HIST |
| Workspace Foundation | 3 | 3 HIST |
| Workspace Ops | 4 | 4 OPS |
| Workspace Design System + Pages | 6 | 6 DRAFT |
| Workspace Audit | 7 | 7 HIST |
| Workspace Archive | 8 | 6 HIST + 2 RETD |
| Workspace Sessions | 81 | 81 HIST |
| **TOTAL** | **355** | **127 AUTH + 1 DRAFT + 85 SUPP + 4 OPS + 6 DRAFT + 59 RPT + 12 RETD + 1 DUPL + 1 OBSOL + 84 HIST** |
