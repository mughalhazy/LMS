# Docs Rename Map

**Standard:** Lowercase kebab-case · Descriptive noun-phrase names · No batch codes, numeric series, or opaque prefixes
**Scope:** 201+ active .md files across docs/ (excludes _archive folders)
**Status:** COMPLETE — all 204 files renamed 2026-05-26.

## Naming convention applied

| Type suffix | Used for |
|---|---|
| `-design.md` | Service and system design documents |
| `-spec.md` | Specification documents |
| `-contract.md` | Interface and integration contracts |
| `-schema.md` | Data schema definitions |
| `-report.md` | Validation, audit, and QC reports |
| `-model.md` | Domain and data models |
| `-architecture.md` | High-level architecture descriptions |
| `-strategy.md` | Strategy and approach documents |
| `-catalogue.md` | Reference tables and inventories |
| `-map.md` | Relationship and boundary maps |
| No suffix | Anchors, guides, and topic documents where type is implicit |

## Change reason codes

| Code | Meaning |
|---|---|
| `kebab` | Convert underscores/caps to lowercase kebab — content unchanged |
| `batch-code` | Remove opaque batch prefix (B2P01, B3P06, B7P04 etc.) |
| `ARCH-prefix` | Remove ARCH_ numeric prefix |
| `SPEC-series` | Remove SPEC_ numeric prefix |
| `AI-series` | Remove AI_ numeric prefix |
| `DATA-series` | Remove DATA_ numeric prefix |
| `DOC-series` | Remove DOC_ numeric prefix |
| `QC-code` | Remove QC code prefix (B7P, QC_, SUP_, P18, PW3) |
| `verb-to-noun` | Convert verb-phrase name to noun-phrase |
| `legacy` | Disambiguate deprecated version from canonical |
| `de-dup` | Rename to prevent cross-folder name collision |

---

## docs/anchors/ — 5 files

| Old Name | New Name | Change |
|---|---|---|
| `event-envelope.md` | `event-envelope.md` | kebab |
| `doc-precedence.md` | `doc-precedence.md` | kebab |
| `capability-resolution.md` | `capability-resolution.md` | kebab |
| `country-layer-architecture.md` | `country-layer-architecture.md` | kebab |
| `tenant-contract.md` | `tenant-contract.md` | kebab |

---

## docs/api/ — 8 files

| Old Name | New Name | Change |
|---|---|---|
| `analytics-api.md` | `analytics-api.md` | kebab |
| `api-contract-validation-report.md` | `api-contract-validation-report.md` | verb-to-noun |
| `api-gateway-design.md` | `api-gateway-design.md` | kebab |
| `api-spec-validation-report.md` | `api-spec-validation-report.md` | verb-to-noun |
| `auth-service-api.md` | `auth-service-api.md` | kebab |
| `content-api.md` | `content-api.md` | kebab |
| `core-rest-api.md` | `core-rest-api.md` | kebab |
| `integration-api.md` | `integration-api.md` | kebab |

---

## docs/architecture/ — 78 files

| Old Name | New Name | Change |
|---|---|---|
| `core-system-architecture.md` | `core-system-architecture.md` | ARCH-prefix |
| `microservice-boundary-map.md` | `microservice-boundary-map.md` | ARCH-prefix |
| `domain-driven-design-map.md` | `domain-driven-design-map.md` | ARCH-prefix |
| `service-data-ownership-rules.md` | `service-data-ownership-rules.md` | ARCH-prefix |
| `event-driven-architecture.md` | `event-driven-architecture.md` | ARCH-prefix |
| `api-versioning-strategy.md` | `api-versioning-strategy.md` | ARCH-prefix |
| `multi-tenant-isolation-model.md` | `multi-tenant-isolation-model.md` | ARCH-prefix |
| `observability-architecture.md` | `observability-architecture.md` | ARCH-prefix |
| `architecture-full-audit-report.md` | `architecture-full-audit-report.md` | ARCH-prefix + QC-code |
| `circular-dependencies-audit-report.md` | `circular-dependencies-audit-report.md` | QC-code |
| `config-service-design.md` | `config-service-design.md` | batch-code |
| `entitlement-service-design.md` | `entitlement-service-design.md` | batch-code |
| `feature-flag-system-design.md` | `feature-flag-system-design.md` | batch-code |
| `usage-metering-service-design.md` | `usage-metering-service-design.md` | batch-code |
| `capability-registry-service-design.md` | `capability-registry-service-design.md` | batch-code |
| `tenant-extension-model.md` | `tenant-extension-model.md` | batch-code |
| `audit-policy-layer-design.md` | `audit-policy-layer-design.md` | batch-code |
| `platform-integration-layer-design.md` | `platform-integration-layer-design.md` | batch-code |
| `commerce-domain-architecture.md` | `commerce-domain-architecture.md` | batch-code |
| `catalog-service-design.md` | `catalog-service-design.md` | batch-code |
| `checkout-service-design.md` | `checkout-service-design.md` | batch-code |
| `invoice-billing-service-design.md` | `invoice-billing-service-design.md` | batch-code |
| `subscription-service-design.md` | `subscription-service-design.md` | batch-code |
| `revenue-service-design.md` | `revenue-service-design.md` | batch-code |
| `academy-commerce-extensions.md` | `academy-commerce-extensions.md` | batch-code |
| `owner-economics-service-design.md` | `owner-economics-service-design.md` | batch-code |
| `academy-operations-domain.md` | `academy-operations-domain.md` | batch-code |
| `school-engagement-domain-design.md` | `school-engagement-domain-design.md` | batch-code |
| `workforce-training-domain-design.md` | `workforce-training-domain-design.md` | batch-code |
| `university-domain-design.md` | `university-domain-design.md` | batch-code |
| `ai-tutor-assist-design.md` | `ai-tutor-assist-design.md` | batch-code |
| `teacher-ai-assist-design.md` | `teacher-ai-assist-design.md` | batch-code |
| `recommendation-engine-design.md` | `recommendation-engine-design.md` | batch-code |
| `learner-risk-insights-design.md` | `learner-risk-insights-design.md` | batch-code |
| `analytics-intelligence-layer-design.md` | `analytics-intelligence-layer-design.md` | batch-code |
| `adaptive-learning-engine.md` | `adaptive-learning-engine.md` | kebab |
| `agi-ready-architecture.md` | `agi-ready-architecture.md` | kebab |
| `ai-course-generation-pipeline.md` | `ai-course-generation-pipeline.md` | kebab |
| `ai-learning-copilot.md` | `ai-learning-copilot.md` | kebab |
| `capability-gating-model.md` | `capability-gating-model.md` | kebab |
| `capability-interface-contract.md` | `capability-interface-contract.md` | kebab |
| `cloud-architecture-ems-lms.md` | `cloud-architecture-ems-lms.md` | kebab |
| `communication-adapter-contract.md` | `communication-adapter-contract.md` | kebab |
| `config-resolution-interface-contract.md` | `config-resolution-interface-contract.md` | kebab |
| `content-storage-model.md` | `content-storage-model.md` | kebab |
| `event-domain-catalogue.md` | `event-domain-catalogue.md` | verb-to-noun |
| `security-architecture.md` | `security-architecture.md` | verb-to-noun |
| `service-map.md` | `service-map.md` | verb-to-noun |
| `duplicate-domains-detection-report.md` | `duplicate-domains-detection-report.md` | verb-to-noun |
| `product-capabilities-matrix.md` | `product-capabilities-matrix.md` | DOC-series |
| `global-education-model-framework.md` | `global-education-model-framework.md` | DOC-series |
| `academy-operational-model.md` | `academy-operational-model.md` | DOC-series |
| `tutor-operational-model.md` | `tutor-operational-model.md` | DOC-series |
| `ai-capability-definition.md` | `ai-capability-definition.md` | DOC-series |
| `terminology-bridge.md` | `terminology-bridge.md` | DOC-series |
| `market-enforcements-capability-map.md` | `market-enforcements-capability-map.md` | DOC-series |
| `domain-boundaries-backend.md` | `domain-boundaries-backend.md` | kebab |
| `domain-capability-extension-model.md` | `domain-capability-extension-model.md` | kebab |
| `enterprise-admin-model.md` | `enterprise-admin-model.md` | kebab |
| `entitlement-interface-contract.md` | `entitlement-interface-contract.md` | kebab |
| `event-bus-design.md` | `event-bus-design.md` | kebab |
| `file-storage-design.md` | `file-storage-design.md` | kebab |
| `data-ownership-rules.md` | `data-ownership-rules.md` | kebab |
| `media-security-interface-contract.md` | `media-security-interface-contract.md` | kebab |
| `multi-branch-rbac-model.md` | `multi-branch-rbac-model.md` | kebab |
| `offline-sync-interface-contract.md` | `offline-sync-interface-contract.md` | kebab |
| `payment-provider-adapter-contract.md` | `payment-provider-adapter-contract.md` | kebab |
| `platform-evolution-model.md` | `platform-evolution-model.md` | kebab |
| `scalability-strategy.md` | `scalability-strategy.md` | kebab |
| `skills-graph-model.md` | `skills-graph-model.md` | kebab |
| `system-of-record-design.md` | `system-of-record-design.md` | QC-code |
| `storage-adapter-interface-contract.md` | `storage-adapter-interface-contract.md` | kebab |
| `tenant-customization-catalogue.md` | `tenant-customization-catalogue.md` | kebab |
| `tenant-isolation-strategy.md` | `tenant-isolation-strategy.md` | kebab |
| `usage-metering-interface-contract.md` | `usage-metering-interface-contract.md` | kebab |
| `data-isolation-analysis-report.md` | `data-isolation-analysis-report.md` | verb-to-noun + de-dup |
| `event-ownership-analysis-report.md` | `event-ownership-analysis-report.md` | verb-to-noun |
| `service-boundary-analysis-report.md` | `service-boundary-analysis-report.md` | verb-to-noun + de-dup |

> **de-dup note:** `data-isolation-analysis-report.md` → `data-isolation-analysis-report.md` (not `-validation-report` to distinguish from the qc/ validation report pattern). `service-boundary-analysis-report.md` → `service-boundary-analysis-report.md` (not `-validation-report` to distinguish from `docs/qc/service-boundary-validation-report.md`).

---

## docs/data/ — 13 files

| Old Name | New Name | Change |
|---|---|---|
| `analytics-data-model.md` | `analytics-data-model.md` | kebab |
| `auth-service-storage-contract.md` | `auth-service-storage-contract.md` | kebab |
| `core-lms-schema.md` | `core-lms-schema.md` | kebab |
| `global-education-schema.md` | `global-education-schema.md` | DATA-series |
| `learning-event-schema.md` | `learning-event-schema.md` | DATA-series |
| `knowledge-graph-schema.md` | `knowledge-graph-schema.md` | DATA-series |
| `institution-hierarchy-schema.md` | `institution-hierarchy-schema.md` | DATA-series |
| `cohort-batch-schema.md` | `cohort-batch-schema.md` | DATA-series |
| `assessment-data-schema.md` | `assessment-data-schema.md` | DATA-series |
| `ai-interaction-schema.md` | `ai-interaction-schema.md` | DATA-series |
| `data-model-validation-report.md` | `data-model-validation-report.md` | kebab |
| `learning-data-model-overview.md` | `learning-data-model-overview.md` | DOC-series |
| `database-schema-validation-report.md` | `database-schema-validation-report.md` | QC-code |

---

## docs/integrations/ — 6 files

| Old Name | New Name | Change |
|---|---|---|
| `auth-lifecycle-events.md` | `auth-lifecycle-events.md` | kebab |
| `hris-sync-spec.md` | `hris-sync-spec.md` | kebab |
| `lti-consumer-spec.md` | `lti-consumer-spec.md` | kebab |
| `lti-provider-spec.md` | `lti-provider-spec.md` | kebab |
| `standards-support.md` | `standards-support.md` | kebab |
| `webhook-system-spec.md` | `webhook-system-spec.md` | kebab |

---

## docs/market/ — 3 files

| Old Name | New Name | Change |
|---|---|---|
| `competitive-intelligence.md` | `competitive-intelligence.md` | kebab |
| `gtm-entry-strategy.md` | `gtm-entry-strategy.md` | kebab |
| `pakistan-market-pricing-guide.md` | `pakistan-market-pricing-guide.md` | kebab |

---

## docs/qc/ — 27 files

| Old Name | New Name | Change |
|---|---|---|
| `architecture-consistency-check-report.md` | `architecture-consistency-check-report.md` | QC-code |
| `audit-logging-verification-report.md` | `audit-logging-verification-report.md` | kebab |
| `auth-service-qc-report.md` | `auth-service-qc-report.md` | kebab |
| `capability-registry-validation-report.md` | `capability-registry-validation-report.md` | QC-code |
| `entitlement-resolution-validation-report.md` | `entitlement-resolution-validation-report.md` | QC-code |
| `config-resolution-validation-report.md` | `config-resolution-validation-report.md` | QC-code |
| `commerce-flow-validation-report.md` | `commerce-flow-validation-report.md` | QC-code |
| `payment-adapter-validation-report.md` | `payment-adapter-validation-report.md` | QC-code |
| `communication-workflow-validation-report.md` | `communication-workflow-validation-report.md` | QC-code |
| `delivery-system-validation-report.md` | `delivery-system-validation-report.md` | QC-code |
| `end-to-end-system-validation-report.md` | `end-to-end-system-validation-report.md` | QC-code |
| `cross-service-dependency-check-report.md` | `cross-service-dependency-check-report.md` | QC-code |
| `load-test-preparation-report.md` | `load-test-preparation-report.md` | kebab |
| `end-to-end-validation-report.md` | `end-to-end-validation-report.md` | QC-code + de-dup |
| `pakistan-wedge-validation-report.md` | `pakistan-wedge-validation-report.md` | QC-code |
| `feature-completeness-check-report.md` | `feature-completeness-check-report.md` | QC-code |
| `event-architecture-validation-report.md` | `event-architecture-validation-report.md` | QC-code |
| `service-boundary-validation-report.md` | `service-boundary-validation-report.md` | QC-code |
| `code-structure-validation-report.md` | `code-structure-validation-report.md` | QC-code |
| `event-publishing-validation-report.md` | `event-publishing-validation-report.md` | QC-code |
| `service-communication-validation-report.md` | `service-communication-validation-report.md` | QC-code |
| `system-hardening-report.md` | `system-hardening-report.md` | QC-code |
| `full-system-integration-validation-report.md` | `full-system-integration-validation-report.md` | QC-code |
| `service-map-verification-report.md` | `service-map-verification-report.md` | kebab |
| `platform-governor-certification-report.md` | `platform-governor-certification-report.md` | QC-code |
| `system-final-validation-report.md` | `system-final-validation-report.md` | kebab |
| `tenant-model-validation-report.md` | `tenant-model-validation-report.md` | QC-code |

> **de-dup note:** `B7P08` → `end-to-end-system-validation-report.md` (system-level sweep of all B7P reports). `P18` → `end-to-end-validation-report.md` (milestone validation, distinct from system-level). Different names, no collision.

---

## docs/specs/ — 63 files

| Old Name | New Name | Change |
|---|---|---|
| `adapter-inventory.md` | `adapter-inventory.md` | kebab |
| `ai-tutor-service-spec.md` | `ai-tutor-service-spec.md` | AI-series |
| `recommendation-service-spec.md` | `recommendation-service-spec.md` | AI-series |
| `skill-inference-service-spec.md` | `skill-inference-service-spec.md` | AI-series |
| `learning-analytics-service-spec.md` | `learning-analytics-service-spec.md` | AI-series |
| `learning-knowledge-graph-spec.md` | `learning-knowledge-graph-spec.md` | AI-series |
| `analytics-service-spec.md` | `analytics-service-spec.md` | kebab |
| `assessment-service-spec.md` | `assessment-service-spec.md` | kebab |
| `auth-service-spec-v0.md` | `auth-service-spec-v0.md` | legacy |
| `auth-service-test-plan.md` | `auth-service-test-plan.md` | kebab |
| `capability-domain-map.md` | `capability-domain-map.md` | batch-code |
| `capability-registry-service-spec.md` | `capability-registry-service-spec.md` | kebab |
| `compliance-reporting-spec.md` | `compliance-reporting-spec.md` | kebab |
| `content-service-spec.md` | `content-service-spec.md` | kebab |
| `content-versioning-spec.md` | `content-versioning-spec.md` | kebab |
| `capability-inventory.md` | `capability-inventory.md` | DOC-series |
| `billing-and-usage-model.md` | `billing-and-usage-model.md` | DOC-series |
| `economic-capabilities-user-spec.md` | `economic-capabilities-user-spec.md` | kebab |
| `enterprise-control-spec.md` | `enterprise-control-spec.md` | kebab |
| `event-ingestion-spec.md` | `event-ingestion-spec.md` | kebab |
| `exam-engine-spec.md` | `exam-engine-spec.md` | kebab |
| `feature-flags-spec.md` | `feature-flags-spec.md` | kebab |
| `financial-ledger-spec.md` | `financial-ledger-spec.md` | kebab |
| `free-tier-operational-definition.md` | `free-tier-operational-definition.md` | kebab |
| `integration-service-spec.md` | `integration-service-spec.md` | kebab |
| `interaction-layer-spec.md` | `interaction-layer-spec.md` | kebab |
| `learning-analytics-spec.md` | `learning-analytics-spec.md` | kebab |
| `learning-path-spec.md` | `learning-path-spec.md` | kebab |
| `lesson-service-spec.md` | `lesson-service-spec.md` | kebab |
| `localization-spec.md` | `localization-spec.md` | kebab |
| `manager-dashboard-spec.md` | `manager-dashboard-spec.md` | kebab |
| `media-pipeline-spec.md` | `media-pipeline-spec.md` | kebab |
| `media-security-spec.md` | `media-security-spec.md` | kebab |
| `monolith-to-services-migration.md` | `monolith-to-services-migration.md` | ARCH-prefix |
| `notification-service-spec.md` | `notification-service-spec.md` | kebab |
| `offline-sync-spec.md` | `offline-sync-spec.md` | kebab |
| `onboarding-spec.md` | `onboarding-spec.md` | kebab |
| `operations-os-spec.md` | `operations-os-spec.md` | kebab |
| `org-hierarchy-spec.md` | `org-hierarchy-spec.md` | kebab |
| `performance-capabilities-spec.md` | `performance-capabilities-spec.md` | kebab |
| `platform-behavioral-contract.md` | `platform-behavioral-contract.md` | kebab |
| `prerequisite-engine-spec.md` | `prerequisite-engine-spec.md` | kebab |
| `progress-tracking-spec.md` | `progress-tracking-spec.md` | kebab |
| `rbac-service-spec-v0.md` | `rbac-service-spec-v0.md` | legacy |
| `reporting-spec.md` | `reporting-spec.md` | kebab |
| `scorm-runtime-spec.md` | `scorm-runtime-spec.md` | kebab |
| `session-service-spec.md` | `session-service-spec.md` | kebab |
| `skill-analytics-spec.md` | `skill-analytics-spec.md` | kebab |
| `auth-service-spec.md` | `auth-service-spec.md` | SPEC-series |
| `rbac-service-spec.md` | `rbac-service-spec.md` | SPEC-series |
| `tenant-service-spec.md` | `tenant-service-spec.md` | SPEC-series |
| `institution-service-spec.md` | `institution-service-spec.md` | SPEC-series |
| `program-service-spec.md` | `program-service-spec.md` | SPEC-series |
| `cohort-service-spec.md` | `cohort-service-spec.md` | SPEC-series |
| `course-service-spec.md` | `course-service-spec.md` | SPEC-series |
| `enrollment-service-spec.md` | `enrollment-service-spec.md` | SPEC-series |
| `progress-service-spec.md` | `progress-service-spec.md` | SPEC-series |
| `certificate-service-spec.md` | `certificate-service-spec.md` | SPEC-series |
| `sso-spec.md` | `sso-spec.md` | kebab |
| `system-economics-spec.md` | `system-economics-spec.md` | kebab |
| `tenant-service-spec-v0.md` | `tenant-service-spec-v0.md` | legacy |
| `user-service-spec.md` | `user-service-spec.md` | kebab |
| `vocational-training-domain-spec.md` | `vocational-training-domain-spec.md` | kebab |
| `workflow-engine-spec.md` | `workflow-engine-spec.md` | kebab |

> **v0 continuity note:** Three pairs exist where a superseded file and its canonical replacement cover the same service. Both share the same base name; the superseded file carries a `-v0` suffix to show its position in the sequence — readable as "version zero of this spec."
> - `auth-service-spec-v0.md` → `auth-service-spec-v0.md` | `auth-service-spec.md` → `auth-service-spec.md`
> - `rbac-service-spec-v0.md` → `rbac-service-spec-v0.md` | `rbac-service-spec.md` → `rbac-service-spec.md`
> - `tenant-service-spec-v0.md` → `tenant-service-spec-v0.md` | `tenant-service-spec.md` → `tenant-service-spec.md`

---

## Collision check — names that appear in multiple folders

These are acceptable cross-folder occurrences (different folders, different scope):

| New Name | Folder A | Folder B | Verdict |
|---|---|---|---|
| `service-boundary-analysis-report.md` | architecture/ | — | Only in architecture/ (qc/ version is `service-boundary-validation-report.md`) |
| `end-to-end-system-validation-report.md` | — | qc/ | Only in qc/; P18 is `end-to-end-validation-report.md` — distinct |
| `auth-service-spec.md` | — | specs/ | Only in specs/; legacy version is `auth-service-spec-legacy.md` |
| `analytics-service-spec.md` | — | specs/ | Only in specs/; architecture/ file is `analytics-intelligence-layer-design.md` |

No true collisions found within any single folder.

---

## Summary counts

| Folder | Files | kebab-only | Batch-code removed | Series prefix removed | verb-to-noun | legacy / de-dup |
|---|---|---|---|---|---|---|
| anchors | 5 | 5 | — | — | — | — |
| api | 8 | 6 | — | — | 2 | — |
| architecture | 78 | 20 | 26 (B2P-B6P) | 11 (ARCH, DOC, SOR) | 6 | 2 |
| data | 13 | 3 | — | 8 (DATA, DOC) | — | — |
| integrations | 6 | 6 | — | — | — | — |
| market | 3 | 3 | — | — | — | — |
| qc | 27 | 5 | — | 22 (B7P, QC, P, PW, SUP) | — | 1 |
| specs | 63 | 35 | 1 (B0P09) | 19 (AI, SPEC, DOC, MIG) | — | 3 |
| **Total** | **203** | **83** | **27** | **60** | **8** | **6** |

> The 83 kebab-only renames are zero-content changes — only separator and case. The remaining 120 renames remove opaque codes, series prefixes, or verb phrases, all of which are functional improvements.

---

**COMPLETE — all 204 files renamed 2026-05-26.**
