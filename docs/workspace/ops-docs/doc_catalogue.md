# LMS PLATFORM — MASTER DOC CATALOGUE
**Version:** 3.1 | **Date:** 2026-04-15 | **Repo:** LMS-main-V4h

---

## HOW TO USE
- All paths are relative to `/LMS-main/`
- Use Ctrl+F / section headers to jump to any domain
- **STATUS** codes: `E`=Exists | `N`=New (normalisation) | `D`=Deprecated | `P`=Planned (future)
- **LAYER** codes: `GOV`=Governance | `ARCH`=Architecture | `SPEC`=Specification | `API`=API | `DATA`=Data | `QC`=Validation | `INT`=Integration | `SVC`=Service | `SCHEMA`=Schema
- Drift flags are in Section 11 — deferred, do not action until all phases complete
- Cross-reference: `MS§` = Master Spec section number
- Normalisation progress: see `progress.md`

---

## SECTION 0 — GOVERNANCE (Read First for Every Session)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `LMS PLATFORM — MASTER PRODUCT & BUILD SPEC.md` | GOV | E | Ground truth — capability-driven platform identity, 18 cap domains, non-negotiable rules | All |
| `doc_catalogue.md` | GOV | N | This file — master index for all docs, services, drift flags | — |
| `progress.md` | GOV | N | Normalisation phase tracker — live status of all doc work | — |
| `pending.md` | GOV | N | Pending work register — BOS gap resolution groups + drift flags | — |
| `gap_register.md` | GOV | N | BOS overlay gap register — all 18 gaps with candidate docs and status | — |
| `ms_overlay_gap_register.md` | GOV | N | Master Spec overlay gap register — 14 architectural contracts (MSG-001–014) now written into target docs | All |
| `spec_index.json` | GOV | E | Machine-readable index of all docs/ files — generated 2026-03-31 | — |
| `docs/anchors/doc_precedence.md` | GOV | E | Canonical doc priority order: BATCH > SPEC > ARCH > legacy | — |
| `docs/specs/platform_behavioral_contract.md` | GOV | E | **Master behavioral contract** — §1, §2, §14, §15 + MS-UX-01/02, MS-SIMPLE-01 + 12 BC-* contracts (BC-PAY-01, BC-FREE-01, BC-LANG-01, BC-EXAM-01, BC-ERR-01, BC-AI-02, BC-CONTENT-02, BC-BRANCH-01, BC-LEARN-01, BC-ECON-01, BC-FAIL-01). Updated 2026-04-14 (Phase A1 market overlay). | All |
| `docs/anchors/capability_resolution.md` | GOV | E | Canonical cap→config→entitlement resolution sequence + chain + **MS-CONFIG-01** cross-ref (country/segment are opaque lookup keys, not branch conditions) | MS§3 |
| `docs/anchors/country_layer_architecture.md` | GOV | E | Adapter binding by tenant.country_code — adapter pattern, not country branching | MS§4 |
| `docs/anchors/event_envelope.md` | GOV | E | Canonical event envelope structure for all domain events | MS§5.8 |
| `docs/anchors/tenant_contract.md` | GOV | E | Canonical tenant contract — fields, isolation rules, extension points | MS§6 |

---

## SECTION 1 — PLATFORM CORE ARCHITECTURE (B2P* — Priority 1 BATCH)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/B2P01_config_service_design.md` | ARCH | E | Config service — 5-layer resolution `global→country→segment→plan→tenant` + **MS-CONFIG-01** (no runtime branching: behavioral variation only from config output, never inline conditionals) | MS§3 |
| `docs/architecture/B2P02_entitlement_service_design.md` | ARCH | E | Entitlement service — capability allow/deny from segment+plan+country+addons | MS§2 |
| `docs/architecture/B2P03_feature_flag_system_design.md` | ARCH | E | Capability activation gate system (note: "feature flag" = capability gate per terminology bridge) | MS§2 |
| `docs/architecture/B2P04_usage_metering_service_design.md` | ARCH | E | Usage metering — tracks ai_calls, api_calls, active_learners, storage, analytics credits | MS§5.5 |
| `docs/architecture/B2P05_capability_registry_service_design.md` | ARCH | E | Capability registry — single source of truth for capability metadata + dependency graph. RegistryValidator updated for **MS-CAP-01/02** completeness + validity checks. CGAP-084/085 RESOLVED. | MS§2 |
| `docs/architecture/B2P06_tenant_extension_model.md` | ARCH | E | Tenant extension fields: segment_type, country_code, plan_type, enabled_addons | MS§3 |
| `docs/architecture/B2P07_audit_policy_layer_design.md` | ARCH | E | Audit policy layer — ledger, retention, compliance controls | MS§5.18 |
| `docs/architecture/B2P08_platform_integration_layer_design.md` | ARCH | E | Platform integration layer — adapter registration, routing, observability | MS§4 |

---

## SECTION 2 — COMMERCE DOMAIN ARCHITECTURE (B3P* — Priority 1 BATCH)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/B3P01_commerce_domain_architecture.md` | ARCH | E | Commerce domain — product, pricing, checkout, invoice, subscription, revenue | MS§5.4 |
| `docs/architecture/B3P02_catalog_service_design.md` | ARCH | E | Product catalog — SKUs, plans, bundles, add-ons | MS§5.4 |
| `docs/architecture/B3P03_checkout_service_design.md` | ARCH | E | Checkout service — order assembly, validation, payment handoff | MS§5.4 |
| `docs/architecture/B3P04_invoice_billing_service_design.md` | ARCH | E | Invoice + billing service — SoR for invoices, payment state, adjustments | MS§5.4 |
| `docs/architecture/B3P05_subscription_service_design.md` | ARCH | E | Subscription lifecycle — create/renew/change/cancel | MS§5.4 |
| `docs/architecture/B3P06_revenue_service_design.md` | ARCH | E | Revenue tracking + reporting — read-optimised, no billing duplication + **BC-REV-01** (revenue risk surfacing: anomaly detection, event emission, operator escalation) | MS§5.15 |
| `docs/architecture/B3P07_academy_commerce_extensions.md` | ARCH | E | Academy-specific commerce extensions — fee plans, batch billing | MS§5.4 |
| `docs/architecture/B3P08_owner_economics_service_design.md` | ARCH | N | Owner/instructor economics — revenue participation, earnings, payout calc | MS§5.14 |

---

## SECTION 3 — OPERATIONS DOMAIN ARCHITECTURE (B5P* — Priority 1 BATCH)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/B5P01_academy_operations_domain.md` | ARCH | E | Academy ops — batch/class ops, enrollment tracking, attendance, fee ops, branch/franchise | MS§5.6 |
| `docs/architecture/B5P02_school_engagement_domain_design.md` | ARCH | E | School engagement domain — attendance, grading, parent portal, teacher-parent comms. Body text confirmed clean of segment-product language (DF-05 resolved 2026-04-11) | MS§5.6 |
| `docs/architecture/B5P03_workforce_training_domain.md` | ARCH | E | Workforce training domain — onboarding, compliance, role readiness, manager oversight. Body text confirmed clean of segment-product language (DF-05 resolved 2026-04-11) | MS§5.6 |
| `docs/architecture/B5P04_university_domain_design.md` | ARCH | E | University domain — faculty, advanced assessment, research, LTI/SCORM integration. Body text confirmed clean of segment-product language (DF-05 resolved 2026-04-11) | MS§5.6 |

> **Normalisation note (added Phase 3):** B5P* docs define use-case capability domain extensions, not segment-forked products. All access via entitlement system. See `docs/architecture/domain_capability_extension_model.md`.

---

## SECTION 4 — AI & INTELLIGENCE ARCHITECTURE (B6P* — Priority 1 BATCH)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/B6P01_ai_tutor_assist_capability_design.md` | ARCH | E | AI tutor capability — conversational, guardrailed, escalation to human + **MS-AI-01** (AI assist boundary: labeled outputs, human review available, human action path, no irreversible autonomous decisions) | MS§5.16 |
| `docs/architecture/B6P02_teacher_ai_assist_design.md` | ARCH | E | Teacher AI assist — lesson planning, at-risk detection, outreach tools | MS§5.16 |
| `docs/architecture/B6P03_recommendation_engine_system_design.md` | ARCH | E | Recommendation engine — profile + history + skills → personalised content | MS§5.16 |
| `docs/architecture/B6P04_learner_risk_insights_system_design.md` | ARCH | E | Learner risk — completion/drop-off probability, intervention triggers + **BC-RISK-01** (learner-facing progress push: direct empowerment messaging, action link, opt-out default) | MS§5.16 |
| `docs/architecture/B6P05_analytics_intelligence_layer_design.md` | ARCH | E | Analytics intelligence — optimisation insights, benchmarking, ranking | MS§5.16 |

---

## SECTION 5 — SYSTEM ARCHITECTURE (ARCH_* — Priority 3)

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/ARCH_01_core_system_architecture.md` | ARCH | E | Core system architecture — domain map, service boundaries, data ownership. Heading: "Global Capability Platform" (DF-02 resolved) + **MS-SCALE-01** (global scalability: no code change for new country; adapter substitution + config layer only) | All |
| `docs/architecture/ARCH_02_microservice_boundary_map.md` | ARCH | E | Microservice boundary map — service ownership rules | MS§3 |
| `docs/architecture/ARCH_03_domain_driven_design_map.md` | ARCH | E | DDD map — bounded contexts, aggregates, domain events | MS§3 |
| `docs/architecture/ARCH_04_service_data_ownership_rules.md` | ARCH | E | Data ownership rules — who writes what, no cross-domain writes | MS§6 |
| `docs/architecture/ARCH_05_event_driven_architecture.md` | ARCH | E | Event-driven architecture — event bus, topics, sagas, replay/DLQ | MS§5.8 |
| `docs/architecture/ARCH_06_api_versioning_strategy.md` | ARCH | E | API versioning — date/major versioning, lifecycle states, sunset policy | MS§4 |
| `docs/architecture/ARCH_07_multi_tenant_isolation_model.md` | ARCH | E | Multi-tenant isolation — data, config, identity isolation per tenant | MS§6 |
| `docs/architecture/ARCH_08_observability_architecture.md` | ARCH | E | Observability — metrics, logs, traces, SLA/SLO monitoring | MS§5.18 |
| `docs/architecture/ARCH_AUDIT_01_full_architecture_audit.md` | ARCH | E | Full architecture audit report | — |
| `docs/architecture/AUDIT_02_circular_service_dependencies.md` | ARCH | E | Circular dependency detection report | — |

---

## SECTION 6 — ARCHITECTURE DESIGN DOCS (general — Priority 4)

> Docs with a higher-priority BATCH/ARCH equivalent have `DEPRECATED` status. See Section 15 for banner list.

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/architecture/DOC_02_product_capabilities_matrix.md` | ARCH | E | Product capabilities matrix — tenant plan vs capability availability | MS§2 |
| `docs/architecture/DOC_03_global_education_model_framework.md` | ARCH | E | Global education model — framework for market-agnostic delivery | MS§12 |
| `docs/architecture/DOC_04_academy_operational_model.md` | ARCH | E | Academy operational model | MS§5.6 |
| `docs/architecture/DOC_05_tutor_operational_model.md` | ARCH | E | Tutor operational model | MS§5.6 |
| `docs/architecture/DOC_08_ai_capability_definition.md` | ARCH | E | AI capability definition — scope, guardrails, AI-assist rule | MS§10.8 |
| `docs/architecture/adaptive_learning_engine.md` | ARCH | E | Adaptive learning engine design | MS§5.1 |
| `docs/architecture/agi_ready_architecture.md` | ARCH | E | AGI-ready architecture principles | MS§10.8 |
| `docs/architecture/ai_course_generation.md` | ARCH | E | AI course generation — draft, review, human approval gates | MS§5.16 |
| `docs/architecture/ai_learning_copilot.md` | ARCH | E | AI learning copilot — in-session assistance | MS§5.16 |
| `docs/architecture/audit_logging.md` | ARCH | D | ⚠ DEPRECATED → `B2P07_audit_policy_layer_design.md` | — |
| `docs/architecture/capability_gating_model.md` | ARCH | E | Capability gating — entitlement enforcement at API/UI boundaries + **BC-GATE-01** (gate UX: hide vs block, plain-language denial, always-present next step) | MS§2 |
| `docs/architecture/capability_interface_contract.md` | ARCH | E | Capability interface contract — standard capability activation contract | MS§2 |
| `docs/architecture/cloud_architecture_ems_lms.md` | ARCH | E | Cloud architecture for EMS+LMS combined deployment | — |
| `docs/architecture/cloud_architecture_lms.md` | ARCH | E | Cloud architecture for LMS standalone deployment | — |
| `docs/architecture/communication_adapter_interface_contract.md` | ARCH | E | Communication adapter contract — channel-agnostic send/schedule/broadcast + **BC-COMMS-01** (multi-channel action parity rule) + **MS-ADAPTER-01** cross-ref (communication adapter isolation) | MS§4 |
| `docs/architecture/config_resolution_interface_contract.md` | ARCH | E | Config resolution interface contract | MS§3 |
| `docs/architecture/config_service.md` | ARCH | D | ⚠ DEPRECATED → `B2P01_config_service_design.md` | — |
| `docs/architecture/content_storage_model.md` | ARCH | E | Content storage model — object storage, metadata, versioning | MS§5.11 |
| `docs/architecture/core_system_architecture.md` | ARCH | D | ⚠ DEPRECATED → `ARCH_01_core_system_architecture.md` | — |
| `docs/architecture/define_event_domains.md` | ARCH | E | Event domain definitions — bounded context event ownership | MS§5.8 |
| `docs/architecture/define_lms_security_architecture.md` | ARCH | E | Security architecture — AuthN/AuthZ, data security, compliance | MS§5.18 |
| `docs/architecture/define_service_map.md` | ARCH | E | Service map — all services with ownership and inter-service contracts | All |
| `docs/architecture/detect_duplicate_domains.md` | ARCH | E | Duplicate domain detection report | — |
| `docs/architecture/domain_boundaries_lms_backend.md` | ARCH | E | Domain boundary definitions for LMS backend | MS§3 |
| `docs/architecture/domain_capability_extension_model.md` | ARCH | N | Extension model — how B5P* use-case domains are capability-driven | MS§5.19 |
| `docs/architecture/enterprise_admin_model.md` | ARCH | E | Enterprise admin model — RBAC, delegation, org hierarchy for admins | MS§5.18 |
| `docs/architecture/entitlement_interface_contract.md` | ARCH | E | Entitlement interface contract — standard capability decision contract | MS§2 |
| `docs/architecture/event_bus_design.md` | ARCH | E | Event bus design — topics, partitioning, schema registry, DLQ | MS§5.8 |
| `docs/architecture/event_driven_architecture.md` | ARCH | D | ⚠ DEPRECATED → `ARCH_05_event_driven_architecture.md` | — |
| `docs/architecture/feature_inventory.md` | ARCH | D | ⚠ DEPRECATED → `docs/specs/DOC_01_feature_inventory.md` | — |
| `docs/architecture/file_storage_design.md` | ARCH | E | File storage design — object store, CDN, access control | MS§4 |
| `docs/architecture/lms_data_ownership_rules.md` | ARCH | E | LMS data ownership rules | MS§6 |
| `docs/architecture/media_security_interface_contract.md` | ARCH | E | Media security contract — tokenised playback, watermark, anti-piracy | MS§5.11 |
| `docs/architecture/microservice_boundaries.md` | ARCH | D | ⚠ DEPRECATED → `ARCH_02_microservice_boundary_map.md` | — |
| `docs/architecture/observability_design.md` | ARCH | E | Observability design — metrics, logs, traces | MS§5.18 |
| `docs/architecture/offline_sync_interface_contract.md` | ARCH | E | Offline sync contract — download orchestration, idempotent sync, resume | MS§5.12 |
| `docs/architecture/payment_provider_adapter_interface_contract.md` | ARCH | E | Payment adapter contract — normalised payment create/verify/refund + **MS-ADAPTER-01** cross-ref (payment adapter isolation) | MS§4 |
| `docs/architecture/platform_long_term_evolution_model.md` | ARCH | E | 20-30yr evolution model — service, API, schema, event compatibility | — |
| `docs/architecture/scalability_strategy.md` | ARCH | E | Scalability strategy — concurrency, partitioning, resilience | MS§5.13 |
| `docs/architecture/skills_graph_model.md` | ARCH | E | Skills graph — competency framework, inference, decay | MS§5.16 |
| `docs/architecture/SOR_01_system_of_record_design.md` | ARCH | N | System of Record design — student lifecycle, financial ledger, unified profile + **MS-SOR-01** (SoR state authority: no service may hold durable copy of state it did not originate) | MS§6 |
| `docs/architecture/tenant_customization.md` | ARCH | E | Tenant customisation model | MS§3 |
| `docs/architecture/tenant_isolation_strategy.md` | ARCH | E | Tenant isolation strategy | MS§7 |
| `docs/architecture/usage_metering_interface_contract.md` | ARCH | E | Usage metering contract — billable event schema | MS§5.5 |
| `docs/architecture/validate_data_isolation.md` | ARCH | E | Data isolation validation report | MS§6 |
| `docs/architecture/validate_event_ownership_report.md` | ARCH | E | Event ownership validation report | MS§5.8 |
| `docs/architecture/validate_service_boundaries.md` | ARCH | E | Service boundary validation report | MS§3 |
| `docs/architecture/DOC_NORM_01_terminology_bridge.md` | ARCH | N | Terminology bridge — "feature" maps to "capability" in all legacy docs | MS§1.4 |
| `docs/architecture/DOC_NORM_02_market_enforcements_capability_map.md` | ARCH | N | Maps MS§7 market enforcements to capability keys and service owners + **MS-MARKET-01** (market enforcements as capabilities: non-negotiable, capability-only delivery, no geography gating) | MS§7 |

---

## SECTION 7 — CAPABILITY JSON DEFINITIONS

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/specs/B0P04_core_capabilities.json` | SCHEMA | E | Core capability set — 7 capabilities (identity, course, enroll, assess, cert, analytics, notifications) | MS§2 |
| `docs/architecture/B0P05_business_capabilities.json` | SCHEMA | E | Business capabilities JSON | MS§5 |
| `docs/architecture/B0P06_communication_capabilities.json` | SCHEMA | E | Communication capabilities JSON | MS§5.7 |
| `docs/architecture/B0P08_intelligence_capabilities.json` | SCHEMA | E | Intelligence/AI capabilities JSON | MS§5.16 |
| `docs/architecture/capabilities/B0P07_delivery_capabilities.json` | SCHEMA | E | Delivery capabilities JSON | MS§5.1 |
| `docs/architecture/schemas/capability_registry.schema.json` | SCHEMA | E | Canonical JSON schema for capability registry entries | MS§2 |
| `docs/architecture/schemas/capability_registry.example.json` | SCHEMA | E | Example capability registry entry | MS§2 |
| `docs/architecture/schemas/segment_configuration.schema.json` | SCHEMA | E | Capability bundle profile schema — profiles indexed by use-case type | MS§1.5 |
| `docs/architecture/schemas/segment_configuration.example.json` | SCHEMA | E | Example capability bundle profiles for 8 use-case types | MS§1.5 |
| `docs/specs/B0P09_full_capability_domain_map.md` | SPEC | N | Full 18-domain capability map — all MS§5 domains → services, specs, status | MS§5 |

---

## SECTION 8 — SPECIFICATION DOCS

> Docs with a `SPEC_` equivalent listed first; plain `*_spec.md` duplicates marked `D`.

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/specs/SPEC_01_auth_service.md` | SPEC | E | Auth service spec | MS§5.18 |
| `docs/specs/auth_service_spec.md` | SPEC | D | ⚠ DEPRECATED → `SPEC_01_auth_service.md` | — |
| `docs/specs/SPEC_03_rbac_service.md` | SPEC | E | RBAC service spec | MS§5.18 |
| `docs/specs/SPEC_05_institution_service.md` | SPEC | E | Institution service spec | MS§5.6 |
| `docs/specs/SPEC_06_program_service.md` | SPEC | E | Program service spec | MS§5.1 |
| `docs/specs/SPEC_07_cohort_service.md` | SPEC | E | Cohort service spec | MS§5.2 |
| `docs/specs/cohort_spec.md` | SPEC | D | ⚠ DEPRECATED → `SPEC_07_cohort_service.md` | — |
| `docs/specs/SPEC_09_course_service.md` | SPEC | E | Course service spec | MS§5.1 |
| `docs/specs/course_service_spec.md` | SPEC | D | ⚠ DEPRECATED → `SPEC_09_course_service.md` | — |
| `docs/specs/SPEC_11_enrollment_service.md` | SPEC | E | Enrollment service spec | MS§5.2 |
| `docs/specs/SPEC_12_progress_service.md` | SPEC | E | Progress service spec | MS§5.2 |
| `docs/specs/SPEC_14_certificate_service.md` | SPEC | E | Certificate service spec | MS§5.1 |
| `docs/specs/GEN_14_certificate_service.md` | SPEC | D | ⚠ DEPRECATED → `SPEC_14_certificate_service.md` | — |
| `docs/specs/DOC_01_feature_inventory.md` | SPEC | E | Capability domain inventory — heading updated to "Global Capability Platform" (DF-02 resolved 2026-04-11) | MS§5 |
| `docs/specs/DOC_07_billing_and_usage_model.md` | SPEC | E | Billing + usage model — metering, billing arch, usage tracking, pricing + **BC-BILLING-01** (contextual upsell) + **MS-MONETIZE-01** (free entry always available, no geography gating, all upgrades via capability activation) | MS§9 |
| `docs/specs/MIG_01_monolith_to_services_extraction.md` | SPEC | E | Migration spec — monolith to microservices extraction plan | — |
| `docs/specs/assessment_service_spec.md` | SPEC | E | Assessment service spec | MS§5.1 |
| `docs/specs/auth_service_test_plan.md` | SPEC | E | Auth service test plan | MS§5.18 |
| `docs/specs/compliance_reporting_spec.md` | SPEC | E | Compliance reporting spec | MS§5.18 |
| `docs/specs/content_service_spec.md` | SPEC | E | Content service spec | MS§5.1 |
| `docs/specs/content_versioning_spec.md` | SPEC | E | Content versioning spec | MS§5.1 |
| `docs/specs/event_ingestion_spec.md` | SPEC | E | Event ingestion spec | MS§5.8 |
| `docs/specs/feature_flags_spec.md` | SPEC | E | Capability activation gate spec (note: "feature flag" = capability gate) | MS§2 |
| `docs/specs/learning_analytics_spec.md` | SPEC | E | Learning analytics spec | MS§5.16 |
| `docs/specs/learning_path_spec.md` | SPEC | E | Learning path spec | MS§5.1 |
| `docs/specs/lesson_service_spec.md` | SPEC | E | Lesson service spec | MS§5.1 |
| `docs/specs/localization_spec.md` | SPEC | E | Localisation spec — locale-aware content and UI | MS§7 |
| `docs/specs/manager_dashboard_spec.md` | SPEC | E | Manager dashboard spec | MS§5.10 |
| `docs/specs/media_pipeline_spec.md` | SPEC | E | Media pipeline spec — upload, transcode, DRM | MS§5.11 |
| `docs/specs/org_hierarchy_spec.md` | SPEC | E | Org hierarchy spec — tenant, BU, dept, cohort, manager | MS§5.6 |
| `docs/specs/prerequisite_engine_spec.md` | SPEC | E | Prerequisite engine spec | MS§5.1 |
| `docs/specs/progress_tracking_spec.md` | SPEC | E | Progress tracking spec | MS§5.2 |
| `docs/specs/rbac_spec.md` | SPEC | E | RBAC spec | MS§5.18 |
| `docs/specs/reporting_spec.md` | SPEC | E | Reporting spec — dashboards, exports, BI connectors | MS§5.16 |
| `docs/specs/scorm_runtime_spec.md` | SPEC | E | SCORM runtime spec | MS§5.1 |
| `docs/specs/session_service_spec.md` | SPEC | E | Session service spec — attempt/session lifecycle | MS§5.1 |
| `docs/specs/skill_analytics_spec.md` | SPEC | E | Skill analytics spec | MS§5.16 |
| `docs/specs/sso_spec.md` | SPEC | E | SSO spec — SAML/OIDC federation | MS§5.18 |
| `docs/specs/tenant_service_spec.md` | SPEC | E | Tenant service spec | MS§3 |
| `docs/specs/user_service_spec.md` | SPEC | E | User service spec | MS§5.18 |

### AI Specs

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/specs/AI_01_ai_tutor_service.md` | SPEC | E | AI tutor service spec | MS§5.16 |
| `docs/specs/AI_02_recommendation_service.md` | SPEC | E | Recommendation service spec | MS§5.16 |
| `docs/specs/AI_03_skill_inference_service.md` | SPEC | E | Skill inference service spec | MS§5.16 |
| `docs/specs/AI_04_learning_analytics_service_engineering_prompt.md` | SPEC | E | Learning analytics service engineering prompt | MS§5.16 |
| `docs/specs/AI_05_learning_knowledge_graph.md` | SPEC | E | Learning knowledge graph spec | MS§5.16 |
| `docs/specs/GEN_14_certificate_service.md` | SPEC | D | ⚠ DEPRECATED → `SPEC_14_certificate_service.md` | — |

### Normalisation — New Capability Domain Specs

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/specs/financial_ledger_spec.md` | SPEC | N | Financial capabilities — student ledger, payment tracking, revenue allocation | MS§5.3 |
| `docs/specs/interaction_layer_spec.md` | SPEC | N | Interaction layer — WhatsApp-style conversational, action-based replies, stateful flows + **BC-INT-01–02**. Status updated PLANNED→BUILT (DF-03 resolved 2026-04-11; CGAP-025) | MS§5.9 |
| `docs/specs/operations_os_spec.md` | SPEC | N | Admin operations OS — dashboards, action prioritisation, system alerts + **BC-OPS-01–04** + **MS-REDUCE-01** (automation coverage: every repeatable operation type must have an automation path) | MS§5.10 |
| `docs/specs/performance_capabilities_spec.md` | SPEC | N | Performance capabilities — high concurrency, session isolation, load resilience | MS§5.13 |
| `docs/specs/economic_capabilities_user_spec.md` | SPEC | N | Economic capabilities (user) — revenue participation, earnings tracking, payout calc | MS§5.14 |
| `docs/specs/system_economics_spec.md` | SPEC | N | Economic capabilities (system) — cost tracking, profitability insights + **BC-ECON-01** (insight-to-action conversion for economics) | MS§5.15 |
| `docs/specs/onboarding_spec.md` | SPEC | N | Onboarding capabilities — instant setup, automated config, guided flows + **BC-ONBOARD-01** (smart defaults for full customisation surface) | MS§5.17 |
| `docs/specs/platform_behavioral_contract.md` | SPEC | N | **Platform behavioral contract** — meta-behavioral governing doc: system as operator, user psychology, final principle + **MS-UX-01** (mobile-first: all primary journeys fully functional on mobile) + **MS-UX-02** (outcome-driven: every surface answers "what next?") + **MS-SIMPLE-01** (simplicity preservation: sensible defaults, no cognitive load increase) | BOS§1,§14,§15 |

### Normalisation — New Service Specs

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/specs/workflow_engine_spec.md` | SPEC | N | Workflow engine spec — event-driven automation, rule engine, multi-step flows + **BC-WF-01** (default-on automation posture) | MS§5.8 |
| `docs/specs/exam_engine_spec.md` | SPEC | N | Exam engine spec — delivery, proctoring rules, attempt lifecycle | MS§5.1 |
| `docs/specs/notification_service_spec.md` | SPEC | N | Notification service spec — messaging, workflow triggers, routing | MS§5.7 |
| `docs/specs/media_security_spec.md` | SPEC | N | Media security service spec — DRM, watermark, session control + **MS-CONTENT-01** (content protection enforcement: default-on for paid content, no delivery without session token) | MS§5.11 |
| `docs/specs/offline_sync_spec.md` | SPEC | N | Offline sync service spec — download, idempotent sync, conflict resolution + **BC-OFFLINE-01** (operational offline actions: attendance, payments, notes, approvals) | MS§5.12 |
| `docs/specs/enterprise_control_spec.md` | SPEC | N | Enterprise control spec — RBAC, audit, compliance integrations | MS§5.18 |
| `docs/specs/analytics_service_spec.md` | SPEC | N | Analytics service spec — event ingestion, projections, dashboard APIs + **BC-ANALYTICS-01–02** (insights over reports, comparative context as default) | MS§5.16 |
| `docs/specs/capability_registry_service_spec.md` | SPEC | N | Capability registry service spec — CRUD, versioning, dependency graph API + **MS-CAP-01** (capability definition completeness: 6 required fields) + **MS-CAP-02** (capability validity rule: independently enable/disable, measurable, reusable) | MS§2 |
| `docs/specs/integration_service_spec.md` | SPEC | N | Integration service spec — HRIS sync, webhooks, LTI, adapter routing | MS§4 |
| `docs/specs/adapter_inventory.md` | SPEC | N | Adapter inventory — all required adapters, interface contracts, impl status + **MS-ADAPTER-01** (adapter isolation: all external deps use adapters, adapters in /integrations, no provider logic in core, swappable) | MS§4 |

---

## SECTION 9 — API DOCS

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/api/analytics_api.md` | API | E | Analytics API — query endpoints for dashboards and reports | MS§5.16 |
| `docs/api/api_contract_validation_qc_gate_2.md` | API | E | API contract validation — gate 2 QC report | — |
| `docs/api/api_gateway_design.md` | API | E | API gateway design — routing, auth, rate limiting, versioning | MS§4 |
| `docs/api/api_spec_validation_qc_gate_1.md` | API | E | API spec validation — gate 1 QC report | — |
| `docs/api/auth_service_api.md` | API | E | Auth service API — token issuance, session, MFA | MS§5.18 |
| `docs/api/content_api.md` | API | E | Content API — course/lesson CRUD, media, versioning | MS§5.1 |
| `docs/api/core_rest_api.md` | API | E | Core REST API — canonical API patterns, versioning, error contracts | MS§4 |
| `docs/api/integration_api.md` | API | E | Integration API — webhooks, HRIS sync, LTI | MS§4 |
| `infrastructure/api-gateway/gateway.yaml` | API | E | API gateway config YAML | MS§4 |
| `infrastructure/api-gateway/openapi-aggregate.yaml` | API | E | Aggregated OpenAPI spec | MS§4 |
| `infrastructure/api-gateway/routes.yaml` | API | E | Route definitions | MS§4 |

---

## SECTION 10 — DATA MODEL DOCS

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/data/DATA_01_global_education_schema.md` | DATA | E | Global education schema — canonical entity definitions | MS§6 |
| `docs/data/DATA_02_learning_event_schema.md` | DATA | E | Learning event schema — event envelope, xAPI alignment | MS§5.8 |
| `docs/data/DATA_03_knowledge_graph_schema.md` | DATA | E | Knowledge graph schema — skills, concepts, relationships | MS§5.16 |
| `docs/data/DATA_04_institution_hierarchy_schema.md` | DATA | E | Institution hierarchy schema | MS§5.6 |
| `docs/data/DATA_05_cohort_batch_schema.md` | DATA | E | Cohort/batch schema | MS§5.2 |
| `docs/data/DATA_06_assessment_data_schema.md` | DATA | E | Assessment data schema | MS§5.1 |
| `docs/data/DATA_07_ai_interaction_schema.md` | DATA | E | AI interaction schema — session, prompt/response structure | MS§5.16 |
| `docs/data/DOC_09_learning_data_model_overview.md` | DATA | E | Learning data model overview | MS§6 |
| `docs/data/analytics_data_model.md` | DATA | E | Analytics data model | MS§5.16 |
| `docs/data/auth_service_storage_contract.md` | DATA | E | Auth service storage contract | MS§5.18 |
| `docs/data/core_lms_schema.md` | DATA | E | Core LMS schema — User, Course, Lesson, Enrollment, Progress, Certificate | MS§6 |
| `docs/data/data_model_validation.md` | DATA | E | Data model validation report | MS§6 |
| `docs/data/qc_gate_2_database_schema_validation.md` | DATA | E | Database schema validation — gate 2 QC | — |

---

## SECTION 11 — QC / VALIDATION DOCS

| Path | Layer | Status | Description |
|------|-------|--------|-------------|
| `docs/qc/B3P05_payment_integration_qc_report.md` | QC | E | Payment integration QC report |
| `docs/qc/B7P01_capability_registry_validation_report.md` | QC | E | Capability registry validation — PASS 10/10 |
| `docs/qc/B7P02_entitlement_resolution_validation_report.md` | QC | E | Entitlement resolution validation — PASS 10/10 |
| `docs/qc/B7P03_config_resolution_validation_report.md` | QC | E | Config resolution validation — PASS 10/10 |
| `docs/qc/B7P04_commerce_flow_validation_report.md` | QC | E | Commerce flow validation — PASS 10/10 |
| `docs/qc/B7P05_payment_adapter_validation_report.md` | QC | E | Payment adapter validation — PASS 10/10 |
| `docs/qc/B7P06_communication_workflow_validation_report.md` | QC | E | Communication workflow validation — PASS 10/10 |
| `docs/qc/B7P07_delivery_system_validation_report.md` | QC | E | Delivery system validation — PASS 10/10 |
| `docs/qc/B7P08_end_to_end_system_validation_report.md` | QC | E | End-to-end system validation |
| `docs/qc/P18_end_to_end_validation_report.md` | QC | E | P18 end-to-end validation report |
| `docs/qc/PW3_PROMPT10_final_pakistan_wedge_validation_report.md` | QC | E | Pakistan-wedge adapter validation — validates country adapter pattern compliance |
| `docs/qc/QC_HARD_01_system_hardening_report.md` | QC | E | System hardening QC report |
| `docs/qc/QC_INT_01_full_system_integration_validation.md` | QC | E | Full system integration validation |
| `docs/qc/SUP_01_platform_governor_final_certification.md` | QC | E | Platform governor certification |
| `docs/qc/architecture_consistency_check_qc_gate1.md` | QC | E | Architecture consistency — gate 1 |
| `docs/qc/audit_logging_verification.md` | QC | E | Audit logging verification |
| `docs/qc/auth_service_qc_loop_report.md` | QC | E | Auth service QC loop report |
| `docs/qc/final_qc_cross_service_dependency_check.md` | QC | E | Cross-service dependency check |
| `docs/qc/load_test_preparation_report.md` | QC | E | Load test preparation report |
| `docs/qc/qc_gate_1_feature_completeness_check.md` | QC | E | Feature (capability) completeness — gate 1 |
| `docs/qc/qc_gate_2_event_architecture_validation.md` | QC | E | Event architecture validation — gate 2 |
| `docs/qc/qc_gate_2_service_boundary_validation.md` | QC | E | Service boundary validation — gate 2 |
| `docs/qc/qc_gate_3_code_structure_validation.md` | QC | E | Code structure validation — gate 3 |
| `docs/qc/qc_gate_3_event_publishing_validation.md` | QC | E | Event publishing validation — gate 3 |
| `docs/qc/qc_gate_4_service_communication_validation.md` | QC | E | Service communication validation — gate 4 |
| `docs/qc/stage3_service_map_verification.md` | QC | E | Service map verification — stage 3 |
| `docs/qc/system_final_validation_report.md` | QC | E | System final validation report |
| `docs/qc/tenant_model_validation_qc_gate2.md` | QC | E | Tenant model validation — gate 2 |
| `docs/qc/b7p01_capability_registry_validation.py` | QC | E | Capability registry validation script |
| `docs/qc/b7p02_entitlement_resolution_validation.py` | QC | E | Entitlement resolution validation script |
| `docs/qc/b7p03_config_resolution_validation.py` | QC | E | Config resolution validation script |
| `docs/qc/b7p04_commerce_flow_validation.py` | QC | E | Commerce flow validation script |
| `docs/qc/b7p05_payment_adapter_validation.py` | QC | E | Payment adapter validation script |
| `docs/qc/b7p06_communication_workflow_validation.py` | QC | E | Communication workflow validation script |
| `docs/qc/b7p07_delivery_system_validation.py` | QC | E | Delivery system validation script |
| `docs/qc/b7p08_end_to_end_system_validation.py` | QC | E | End-to-end validation script |
| `docs/qc/p18_end_to_end_validation.py` | QC | E | P18 end-to-end validation script |
| `docs/qc/b7p01_capability_registry_validation_report.json` | QC | E | Capability registry validation result JSON |
| `docs/qc/b7p02_entitlement_resolution_validation_report.json` | QC | E | Entitlement resolution result JSON |
| `docs/qc/b7p03_config_resolution_validation_report.json` | QC | E | Config resolution result JSON |
| `docs/qc/b7p04_commerce_flow_validation_report.json` | QC | E | Commerce flow result JSON |
| `docs/qc/b7p05_payment_adapter_validation_report.json` | QC | E | Payment adapter result JSON |
| `docs/qc/b7p06_communication_workflow_validation_report.json` | QC | E | Communication workflow result JSON |
| `docs/qc/b7p07_delivery_system_validation_report.json` | QC | E | Delivery system result JSON |
| `docs/qc/b7p08_end_to_end_system_validation_report.json` | QC | E | End-to-end result JSON |
| `docs/qc/load_test_readiness_check.py` | QC | E | Load test readiness script |
| `docs/qc/performance_smoke_tests.py` | QC | E | Performance smoke test script |
| `p18_end_to_end_validation_report.json` | QC | E | P18 result JSON |

---

## SECTION 12 — INTEGRATION DOCS

| Path | Layer | Status | Description | MS§ |
|------|-------|--------|-------------|-----|
| `docs/integrations/auth_lifecycle_events.md` | INT | E | Auth lifecycle events — login, logout, provision, deprovision events | MS§5.18 |
| `docs/integrations/hris_sync_spec.md` | INT | E | HRIS sync spec — user, org, enrollment sync | MS§4 |
| `docs/integrations/lti_consumer_spec.md` | INT | E | LTI consumer spec — receive LTI launch from external tools | MS§4 |
| `docs/integrations/lti_provider_spec.md` | INT | E | LTI provider spec — expose courses as LTI tools | MS§4 |
| `docs/integrations/standards_support.md` | INT | E | Standards support — xAPI, SCORM, LTI, SCIM, SAML, OIDC | MS§4 |
| `docs/integrations/webhook_system_spec.md` | INT | E | Webhook system spec — event delivery, retry, signature | MS§4 |

---

## SECTION 13 — SERVICES (Code Layer)

> Each service entry shows its spec status. Services without a spec doc are `N` (new spec to be created).
> **Phase B build status** (as of 2026-04-11): T1–T6-H complete (83/83 resolved). Phase B COMPLETE. Drift flag resolution (DF-01, DF-02, DF-03, DF-05) deferred as next work stream. See `code_gap_register.md` for full gap inventory.
> **Market Overlay Phase B** (2026-04-14): MO-022/023/024 resolved — storage adapter + file-storage + media-pipeline built.
> **Market Overlay Phase C** (2026-04-14): MO-025–031 resolved — 7 BC-* behavioral contracts wired into code. See `code_gap_register.md` Market Overlay section for detail.
> **Market Overlay Phase D** (2026-04-14): MO-032–035 resolved — 4 dependent cross-service wiring completions. Event chain now end-to-end: payment→entitlement, at-risk→intervention workflow, revenue event→DAL, free-plan onboarding→bundle.
> **Market Overlay Phase E** (2026-04-14): MO-036–040 resolved — 5 domain extensions: cross-branch analytics, vocational segment defaults, Pakistan fee defaults, offline manifest registration, exam performance analytics.

| Service path | Status | Spec doc | Description | MS§ |
|---|---|---|---|---|
| `services/academy-ops/` | E | `B5P01` (ARCH) | Academy operations — batch, attendance, fee tracking, branch; `AttendanceRecord`/`FeePayment` annotated with MS-SOR-01 boundary (originating service; SoR delegation enforced on write — CGAP-088 resolved 2026-04-12) | MS§5.6 |
| `services/analytics-service/` | E | `N` → `analytics_service_spec.md` | Learning analytics — events, projections, dashboards | MS§5.16 |
| `services/capability-registry/` | E | `B2P05` (ARCH) + `N` → `capability_registry_service_spec.md` | Capability registry service — `assert_capability_is_single_billing_unit()` (CGAP-034); `_validate_ms_cap_01()` + `_validate_ms_cap_02()` validation gates added, self-dependency guard in `register_capability_dependencies()` (CGAP-084/085 resolved 2026-04-11) | MS§2 |
| `services/commerce/` | E | `B3P01`–`B3P07` | Commerce — billing, catalog, checkout, monetisation, owner economics; `build_commerce_service_for_country()` generic factory replaces inline PKR→PK hack (CGAP-086 resolved 2026-04-12) | MS§5.4 |
| `services/config-service/` | E | `B2P01` (ARCH) | Config service; `platform_defaults.py` (NEW 2026-04-12) — seeds COUNTRY/SEGMENT layers with locale, whatsapp, gdpr, compliance, capability defaults (MS-CONFIG-01 / CGAP-086) | MS§3 |
| `services/enterprise-control/` | E | `N` → `enterprise_control_spec.md` | Enterprise control — RBAC, audit, compliance, SSO identity federation (CGAP-052 resolved 2026-04-08) | MS§5.18 |
| `services/entitlement-service/` | E | `B2P02` (ARCH) | Entitlement service — billing lifecycle (active/grace/suspended/terminated), entitlement.updated event emission (CGAP-039, CGAP-040 resolved 2026-04-08) | MS§2 |
| `services/exam-engine/` | E | `N` → `exam_engine_spec.md` | Exam engine — delivery, proctoring, attempts | MS§5.1 |
| `services/integration-service/` | E | `N` → `integration_service_spec.md` | Integration service — HRIS, webhooks, LTI | MS§4 |
| `services/media-security/` | E | Contract exists + `N` → `media_security_spec.md` | Media security — DRM, watermark, playback auth; `gate_delivery()` added for MS-CONTENT-01 paid content token enforcement (CGAP-089 resolved 2026-04-12) | MS§5.11 |
| `services/notification-service/` | E | `N` → `notification_service_spec.md` | Notification service — routing, orchestration, delivery | MS§5.7 |
| `services/offline-sync/` | E | Contract exists + `N` → `offline_sync_spec.md` | Offline sync — download, idempotent queue, retry, operator action conflict detection (CGAP-045 resolved 2026-04-08) | MS§5.12 |
| `services/onboarding/` | E | `N` → `onboarding_spec.md` | Onboarding service — tenant setup, config bootstrap, notification template defaults; MS-CONFIG-01 compliant: `_COUNTRY_CURRENCY`/`_WHATSAPP_PRIMARY_COUNTRIES`/`_SEGMENT_CAPABILITY_DEFAULTS` removed; `_resolve_country_segment_defaults()` reads from config resolution output (CGAP-086 resolved 2026-04-12) | MS§5.17 |
| `services/operations-os/` | E | `N` → `operations_os_spec.md` | Operations OS — dashboards, action prioritisation, alerts | MS§5.10 |
| `services/subscription-service/` | E | `B3P05` (ARCH) | Subscription service | MS§5.4 |
| `services/system-of-record/` | E | `N` → `SOR_01_system_of_record_design.md` | System of record — student lifecycle, financial ledger, profile, student.lifecycle_event emission (CGAP-050 resolved 2026-04-08) | MS§6 |
| `services/workflow-engine/` | E | `N` → `workflow_engine_spec.md` | Workflow engine — automation, rule engine, multi-step flows, human approval gates (CGAP-007), automation audit log (CGAP-009); `wf_default_compliance_tracking` + `wf_default_daily_action_list` added for MS-REDUCE-01 (CGAP-091 resolved 2026-04-12) | MS§5.8 |

---

## SECTION 13B — BACKEND SERVICES (Code Layer — `backend/services/`)

> Services marked `STUB` have `NotImplementedError` implementations. Build order: T3-A → T3-B → T3-C → T3-D per `pending.md`.

| Service path | Status | Gap | Spec doc | T3 Sub-tier |
|---|---|---|---|---|
| `backend/services/group-service/` | BUILT | CGAP-073 | `org_hierarchy_spec.md` | T3-A ✓ |
| `backend/services/department-service/` | BUILT | CGAP-074 | `org_hierarchy_spec.md` | T3-A ✓ |
| `backend/services/content-service/` | BUILT | CGAP-063 | `content_service_spec.md` + `content_versioning_spec.md` | T3-A ✓ |
| `backend/services/learning-path-service/` | BUILT | CGAP-064 | `learning_path_spec.md` | T3-B ✓ |
| `backend/services/prerequisite-engine-service/` | BUILT | CGAP-079 | `prerequisite_engine_spec.md` | T3-B ✓ |
| `backend/services/skill-analytics-service/` | BUILT | CGAP-081 | `skill_analytics_spec.md` | T3-B ✓ |
| `backend/services/scorm-service/` | BUILT | CGAP-066 | `scorm_runtime_spec.md` | T3-C ✓ |
| `backend/services/hris-sync-service/` | BUILT | CGAP-070 | `hris_sync_spec.md` | T3-C ✓ |
| `backend/services/integration-service/` | BUILT | CGAP-078 | `integration_service_spec.md` | T3-C ✓ |
| `backend/services/webhook-service/` | BUILT | CGAP-027 | `webhook_system_spec.md` | T3-D ✓ |
| `services/interaction-service/` | BUILT | CGAP-025 | `interaction_layer_spec.md` | T3-D ✓ |
| `backend/services/auth-service/app/store_db.py` | N | CGAP-058 (partial) | `auth_service_storage_contract.md` | T4-B ✓ |
| `backend/services/rbac-service/app/store_db.py` | N | CGAP-058 (partial) | `SPEC_03_rbac_service.md` | T4-B ✓ |
| `backend/services/tenant-service/app/store_db.py` | N | CGAP-058 (partial) | `tenant_service_spec.md` | T4-B ✓ |
| `backend/services/user-service/app/store_db.py` | N | CGAP-058 (partial) | `user_service_spec.md` | T4-C ✓ |
| `backend/services/enrollment-service/app/store_db.py` | N | CGAP-058 (partial) | `SPEC_11_enrollment_service.md` | T4-C ✓ |
| `backend/services/progress-service/app/store_db.py` | N | CGAP-058 (partial) | `SPEC_12_progress_service.md` | T4-C ✓ |
| `backend/services/session-service/app/store_db.py` | N | CGAP-058 (partial) | `session_service_spec.md` | T4-C ✓ |
| `backend/services/assessment-service/app/store_db.py` | N | CGAP-058 (partial) | `assessment_service_spec.md` | T4-D ✓ |
| `backend/services/lesson-service/app/store_db.py` | N | CGAP-058 (partial) | `lesson_service_spec.md` | T4-D ✓ |
| `backend/services/course-service/app/store_db.py` | N | CGAP-058 (partial) | `course_service_spec.md` | T4-D ✓ |
| `backend/services/badge-service/app/store_db.py` | N | CGAP-058 (partial) | badge-service (no standalone spec) | T4-D ✓ |
| `backend/services/certificate-service/app/service.py` | E | CGAP-077 resolved 2026-04-08 — `handle_enrollment_completed()` added; triggers certificate issuance on `enrollment.completed` events | `SPEC_14` |
| `backend/services/subscription-service/app/models.py` + `app/service.py` | E | CGAP-080 resolved 2026-04-08 — `GRACE`/`SUSPENDED` states + `GRACE_ENTRY`/`SUSPENSION` events added to `SubscriptionLifecycleService` | `B3P05` |
| `backend/services/auth-service/app/service.py` | E | CGAP-054 resolved 2026-04-08 — `sso_initiate()` + `sso_callback()` SSO handlers added | `SPEC_01` |
| `backend/services/enrollment-service/app/service.py` | E | CGAP-055 resolved 2026-04-08 — `PlatformEventBridgePublisher` bridges `enrollment.completed` to platform event bus | `SPEC_11` |
| `backend/services/course-service/app/service.py` | E | CGAP-065 resolved 2026-04-08 — `version`/`version_history` on `CourseRecord`, `get_version_history()`, `rollback_to_version()` added | content_versioning_spec |
| `backend/services/tenant-service/app/service.py` | E | CGAP-069 resolved 2026-04-08 — `get_plan_capabilities()` queries capability registry first, env-var fallback | `B2P02` |
| `backend/services/payment-service/service.py` | N (NEW) | CGAP-071 resolved 2026-04-08 — `PaymentService` with history storage, event emission, reconciliation | `B3P03` |
| `backend/services/ai-tutor-service/app/schemas.py` | E | `TutorResponse` extended with `ai_generated`, `guidance_level`, `human_review_available`, `override_path` for MS-AI-01 compliance (CGAP-090 resolved 2026-04-12) | `AI_01` |
| `backend/services/ai-tutor-service/app/service.py` | E | CGAP-061 resolved 2026-04-08 — degraded-mode sentinel; MS-AI-01: `_GUIDANCE_LEVEL_MAP` + explicit MS-AI-01 fields populated in `_store_interaction()` (CGAP-090 resolved 2026-04-12) | `AI_01` |
| `backend/services/sso-service/app/service.py` | E | `SSOService.__init__` accepts injected `providers` dict; concrete OIDC/SAML/OAuth2 imports removed — service is provider-agnostic per MS-ADAPTER-01 (CGAP-087 resolved 2026-04-12) | MS§4 |

---

## SECTION 14 — SHARED MODELS & VALIDATION

| Path | Status | Description |
|------|--------|-------------|
| `shared/models/academy.py` | E | Academy domain shared models |
| `shared/models/addon.py` | E | Add-on entitlement models |
| `shared/models/branch.py` | E | Branch/franchise models |
| `shared/models/capability.py` | E | Core capability model; `domain` + `required_adapters` fields added for MS-CAP-01 definition completeness (CGAP-084 resolved 2026-04-11) |
| `shared/models/capability_pricing.py` | E | Capability pricing models |
| `shared/models/config.py` | E | Config resolution models |
| `shared/models/event.py` | E | Domain event envelope models |
| `shared/models/exam_session.py` | E | Exam session models |
| `shared/models/invoice.py` | E | Invoice models |
| `shared/models/ledger.py` | E | Financial ledger models |
| `shared/models/media_policy.py` | E | Media security policy models; `content_tier` field added for MS-CONTENT-01 paid/free distinction (CGAP-089 resolved 2026-04-12) |
| `shared/models/network_analytics.py` | E | Teacher/tutor network analytics models |
| `shared/models/offline_progress.py` | E | Offline progress sync models |
| `shared/models/onboarding.py` | E | Onboarding flow models |
| `shared/models/operations_dashboard.py` | E | Operations dashboard models |
| `shared/models/owner_economics.py` | E | Owner/instructor economics models — `OwnerEconomicsSnapshot.suggested_action` added 2026-04-08 (CGAP-043) |
| `shared/models/plan.py` | E | Plan/tier models |
| `shared/models/school.py` | E | School engagement domain models |
| `shared/models/student_profile.py` | E | Unified student profile models |
| `shared/models/teacher_economics.py` | E | Teacher economics models |
| `shared/models/teacher_network.py` | E | Teacher network/marketplace models |
| `shared/models/teacher_performance.py` | E | Teacher performance models |
| `shared/models/template.py` | E | Template models (certs, comms) |
| `shared/models/timetable.py` | E | Timetable/scheduling models |
| `shared/models/university.py` | E | University domain models |
| `shared/models/usage_record.py` | E | Usage metering record models |
| `shared/models/workflow.py` | E | Workflow engine models |
| `shared/models/workforce.py` | E | Workforce training models |
| `shared/control_plane.py` | E | Platform control plane logic |
| `shared/segment_runtime.py` | E | Segment runtime behavior mixins — boundary decision documented in module docstring (CGAP-083 / DF-06 resolved 2026-04-11). Stays in `shared/` as control-plane delegation helper. |
| `shared/validation/contracts.py` | E | Shared validation contracts |

### Backend Services Shared Layer

| Path | Status | Description |
|------|--------|-------------|
| `backend/services/shared/events/envelope.py` | E | EventEnvelope model + `build_event()` + `publish_event()` (CGAP-059 fix) |
| `backend/services/shared/events/bus.py` | N | **EventBus** — in-process pub/sub transport per ARCH_05 §5. Singleton `get_default_bus()`. (CGAP-082 fix) |
| `backend/services/shared/db/__init__.py` | N | **Shared DB package** — re-exports BaseRepository, connect, resolve_db_path |
| `backend/services/shared/db/engine.py` | N | **BaseRepository + connect + resolve_db_path** — stdlib sqlite3 persistence infrastructure. Enforces ARCH_04 (per-service isolation) and ARCH_07 (tenant_id NOT NULL, tenant-first queries). T4-A foundation. |
| `backend/services/auth-service/app/store_db.py` | N | **SQLiteAuthStore + AuthStoreProtocol** — 7-table SQLite auth store. auth_tenants, auth_user_credentials, auth_sessions, auth_refresh_tokens, auth_password_reset_challenges, auth_audit_log, auth_outbox_events. T4-B. |
| `backend/services/rbac-service/app/store_db.py` | N | **SQLiteRBACStore + RBACStoreProtocol** — 6-table SQLite RBAC store. Global permissions catalog + tenant-scoped roles/bindings/assignments/policy_rules/decision_logs. T4-B. |
| `backend/services/tenant-service/app/store_db.py` | N | **SQLiteTenantStore** — implements TenantStore Protocol. 6 tables covering all 5 SPEC_04 entities + tenant_namespaces. tenant_key column supports by_code() lookup. T4-B. |
| `backend/services/user-service/app/store_db.py` | N | **SQLiteUserStore + SQLiteAuditLogStore** — UserAggregate stored as model_dump_json; indexed by email. Append-only user_audit_log. T4-C. |
| `backend/services/enrollment-service/app/store_db.py` | N | **SQLiteEnrollmentStore** — enrollments table per SPEC_11 §3.1; active_for_learner_course query; enrollment_audit_log. T4-C. |
| `backend/services/progress-service/app/store_db.py` | N | **SQLiteProgressStore + SQLiteIdempotencyStore** — 5 tables per SPEC_12 §3 (progress_records upsert, course/path snapshots, metrics, audit). idempotency_keys for dedup. T4-C. |
| `backend/services/session-service/app/store_db.py` | N | **SQLiteSessionRepository** — extends abstract SessionRepository. sessions/session_audit_logs/session_events. Nested dataclasses serialised to JSON data column. T4-C. |
| `backend/services/assessment-service/app/store_db.py` | N | **SQLiteAssessmentStore** — Category A (Protocol exists). 3 tables: assessments, attempts, submissions. metadata/payload as JSON. 11 Protocol methods. T4-D. |
| `backend/services/lesson-service/app/store_db.py` | N | **SQLiteLessonStore** — extends LessonStore ABC (Category B). 3 tables: lessons (learning_objectives/availability_rules/metadata/delivery_state as JSON), lesson_audit_log, lesson_outbox_events. Ordered list by course_id+order_index+created_at. T4-D. |
| `backend/services/course-service/app/store_db.py` | N | **SQLiteCourseStorage** — implements CourseStorageContract Protocol (Category C). 1 table: courses. Pydantic fields (CourseMetadata/ProgramLink/SessionLink) serialised via model_dump_json/model_dump. save() uses INSERT…ON CONFLICT upsert. T4-D. |
| `backend/services/badge-service/app/store_db.py` | N | **BadgeRepositoryProtocol + SQLiteBadgeRepository** — Category C (no prior Protocol). 2 tables: badge_definitions, badge_issuances. criteria/metadata/evidence as JSON. list_issuances() supports learner_id+badge_id filters. T4-D. |

---

## SECTION 15 — INTEGRATIONS (Code Layer)

| Path | Status | Description | MS§ |
|------|--------|-------------|-----|
| `integrations/communication/base_adapter.py` | E | Base communication adapter | MS§4 |
| `integrations/communication/email_adapter.py` | E | Email adapter implementation | MS§4 |
| `integrations/communication/sms_adapter.py` | E | SMS adapter implementation | MS§4 |
| `integrations/communication/whatsapp_adapter.py` | E | WhatsApp adapter — supports §5.9 interaction layer delivery | MS§4, §5.9 |
| `integrations/payment/base_adapter.py` | E | Base payment adapter | MS§4 |
| `integrations/payment/easypaisa_adapter.py` | E | Easypaisa payment adapter (PK market) — valid adapter pattern | MS§4 |
| `integrations/payment/jazzcash_adapter.py` | E | JazzCash payment adapter (PK market) — valid adapter pattern | MS§4 |
| `integrations/payment/router.py` | E | Payment adapter router | MS§4 |
| `integrations/payments/base_adapter.py` | E | **CANONICAL** payment base adapter — `integrations/payments/` is authoritative (CGAP-076 / DF-04 resolved 2026-04-11) | MS§4 |
| `integrations/payments/orchestration.py` | E | Payment orchestration | MS§4 |
| `integrations/payments/reconciliation.py` | E | Payment reconciliation | MS§4 |
| `integrations/payments/router.py` | E | Payment adapter router — canonical router | MS§4 |
| `integrations/payment/__init__.py` | E | ⚠ DEPRECATED → `integrations/payments/` (CGAP-076 / DF-04 resolved) | MS§4 |
| `integrations/identity/__init__.py` | E | Identity adapter package marker (NEW 2026-04-12) | MS§4 |
| `integrations/identity/registry.py` | E | SSO provider registry — `build_sso_providers()` factory; canonical construction point per MS-ADAPTER-01; `SSOService` is provider-agnostic via injection (CGAP-087 resolved 2026-04-12) | MS§4 |
| `integrations/storage/base_adapter.py` | N | **BaseStorageAdapter Protocol** — 6-method contract: upload/download/presigned-upload-url/presigned-download-url/delete/exists. MO-022 Phase B. | MS§4 |
| `integrations/storage/s3_adapter.py` | N | **S3StorageAdapter** — AWS S3 / MinIO / Wasabi / Cloudflare R2 / DigitalOcean Spaces. Stub mode when no client injected. | MS§4 |
| `integrations/storage/local_adapter.py` | N | **LocalStorageAdapter** — local filesystem adapter for dev / offline LMS-in-a-box. | MS§4 |
| `integrations/storage/router.py` | N | **StorageRouter** — content_category→bucket routing; per-tenant adapter selection; `resolve_bucket()` utility. | MS§4 |
| `integrations/storage/__init__.py` | N | Storage adapter package exports. | MS§4 |
| `services/file-storage/service.py` | N | **FileStorageService** — upload lifecycle (initiate/confirm/mark_ready), download URL generation, BC-CONTENT-02 enforcement (paid→media_security_required), archive/delete. MO-023 Phase B. | MS§5.11 |
| `services/media-pipeline/service.py` | N | **MediaPipelineService** — video transcode + thumbnail + offline package (BC-FAIL-01), image optimize, SCORM extract, doc preview. Events: media.pipeline.*. MO-024 Phase B. | MS§5.11, §5.12 |
| `docs/architecture/storage_adapter_interface_contract.md` | N | Storage adapter interface contract — Protocol definition, canonical buckets, MS§4 enforcement rules, BC-CONTENT-02 integration. | MS§4 |
| `services/exam-engine/service.py` *(updated)* | E | **BC-EXAM-01 answer checkpointing** — `submit_answer()` (immediate checkpoint per question), `get_session_answers()` (reconnect state), `resume_exam_session()` (full restore). MO-025 Phase C. | MS§5.8 |
| `backend/services/rbac-service/app/models.py` *(updated)* | E | **BC-BRANCH-01 RBAC scope** — `ScopeType.BRANCH` enum value; `branch_ids: list[str] \| None` on `SubjectRoleAssignment`. MO-026 Phase C. | MS§5.2 |
| `backend/services/rbac-service/app/service.py` *(updated)* | E | **BC-BRANCH-01 enforcement** — `get_effective_branch_ids()` (None=HQ/tenant-wide), `require_branch_access()` (403 if branch not in scope). MO-026 Phase C. | MS§5.2 |
| `services/capability-registry/service.py` *(updated)* | E | **BC-FREE-01 bundle** — `register_free_tier_capability_bundle()` (4 quota-capped caps). **BC-LANG-01 validation** — MS-CAP-01 now rejects monetizable caps without `business_impact_description`. MO-027/031 Phase C. | MS§2 |
| `shared/models/capability.py` *(updated)* | E | **BC-LANG-01** — `business_impact_description: str = ""` field added to `Capability` dataclass. MO-031 Phase C. | MS§2 |
| `backend/services/payment-service/service.py` *(updated)* | E | **BC-PAY-01** — `activate_entitlement_on_payment()` emits `entitlement.activated` synchronously on `payment.verified`; wired into `handle_provider_callback()`. MO-028 Phase C. | MS§5.3 |
| `services/operations-os/service.py` *(updated)* | E | **BC-ECON-01** — `receive_revenue_signal()` + `generate_revenue_action_items()` ingest revenue risk signals into Daily Action List immediately. MO-029 Phase C. | MS§5.10 |
| `services/analytics-service/service.py` *(updated)* | E | **BC-LEARN-01** — `trigger_at_risk_interventions()` wraps `at_risk_learner_signals()`, emits `workflow.trigger.learner_intervention` per at-risk learner for automatic intervention dispatch. MO-030 Phase C. | MS§5.16 |
| `services/workflow-engine/service.py` *(updated)* | E | **BC-LEARN-01** — `wf_default_learner_intervention` workflow registered: handles `workflow.trigger.learner_intervention`, notifies learner + creates IMPORTANT action item. MO-032 Phase D. | MS§5.7 |
| `services/entitlement-service/service.py` *(updated)* | E | **BC-PAY-01** — `activate_from_payment()` refreshes/bootstraps tenant subscription on payment verification. Consuming side of MO-028 event chain. MO-033 Phase D. | MS§2 |
| `services/onboarding/service.py` *(updated)* | E | **BC-FREE-01** — `bootstrap_default_capabilities()` calls `register_free_tier_capability_bundle()` for free-plan tenants at onboarding. MO-034 Phase D. | MS§5.17 |
| `backend/services/event-ingestion-service/app/forwarders.py` *(updated)* | E | **BC-ECON-01** — `RevenueSignalForwarder` maps 8 revenue event types to `receive_revenue_signal()` in operations-os. MO-035 Phase D. | MS§5.10 |
| `backend/services/event-ingestion-service/app/main.py` *(updated)* | E | `RevenueSignalForwarder` wired into `ForwardingPipeline`. MO-035 Phase D. | MS§5.10 |
| `services/analytics-service/service.py` *(updated)* | E | **BC-BRANCH-01** — `record_branch_snapshot()` + `cross_branch_analytics()` (MO-036). **Exam analytics** — `ingest_exam_result()` + `exam_performance_insight()` BC-ANALYTICS-01/02 InsightEnvelope (MO-040). Phase E. | MS§5.16 |
| `services/config-service/platform_defaults.py` *(updated)* | E | Vocational segment capabilities seeded (MO-037). Pakistan fee/payment defaults at COUNTRY layer — PKR, JazzCash/EasyPaisa priority, installments (MO-038). Phase E. | MS§3 |
| `services/offline-sync/service.py` *(updated)* | E | **BC-FAIL-01** — `register_offline_manifest()`, `receive_pipeline_event()` — closes media-pipeline→offline delivery chain (MO-039). Phase E. | MS§5.11 |

---

## SECTION 16 — INFRASTRUCTURE

| Path | Status | Description |
|------|--------|-------------|
| `infrastructure/api-gateway/` | E | API gateway config, OpenAPI aggregate, routes |
| `infrastructure/deployment/` | E | Deployment configs |
| `infrastructure/event-bus/` | E | Event bus infrastructure |
| `infrastructure/load-testing/` | E | Load testing infrastructure |
| `infrastructure/observability/` | E | Observability stack config |
| `infrastructure/secrets-management/` | E | Secrets management config |
| `infrastructure/service-discovery/` | E | Service discovery config |

---

## SECTION 17 — VALIDATION (Test Layer)

| Path | Status | Description |
|------|--------|-------------|
| `validation/tests/test_exam_economics_validation.py` | E | Exam economics validation tests |
| `validation/tests/test_network_analytics_validation.py` | E | Network analytics validation tests |
| `validation/tests/test_system_integration_validation.py` | E | System integration validation tests |
| `validation/tests/test_whatsapp_integration_consolidation.py` | E | WhatsApp integration consolidation tests — supports §5.9 |
| `validation/contracts.py` | E | Validation contracts |

---

## SECTION 18 — DRIFT FLAGS (DEFERRED — DO NOT ACTION YET)

> These are flagged contradictions and build drift risks. Documented here for awareness and end-of-normalisation resolution.

| ID | Location | Risk | Description |
|---|---|---|---|
| **DF-01** | `docs/anchors/capability_resolution.md` + `B2P01` + `B2P02` | CRITICAL | Config chain uses `country` and `segment` as named resolution LAYERS, not just entitlement inputs. This means config VALUES can differ by segment/country — broader than just capability entitlement. Whether segment-differentiated config is permitted needs an explicit architectural decision. |
| **DF-02** | `ARCH_01`, `DOC_01` vs Master Spec §12 | HIGH | "Enterprise LMS V2 extending Rails LMS" vs "Global Capability Platform" are competing identities. Without a formal heritage statement in the Master Spec, architectural decisions will be made toward different targets depending on which doc a developer encounters first. |
| **DF-03** | Master Spec §5.9 vs entire repo | HIGH | §5.9 Interaction Layer (conversational, action-based, stateful flows) has no service, no spec, no model. Only `whatsapp_adapter.py` and `test_whatsapp_integration_consolidation.py` exist. Gap between MS spec and build is total for this domain. Spec doc created (PLANNED status) — but the service is unbuilt. |
| **DF-04** | `integrations/payment/` vs `integrations/payments/` | MEDIUM | Two payment adapter folders with overlapping files (`base_adapter.py`, `router.py`). Canonical path is ambiguous. Any new payment adapter work risks going into the wrong folder. |
| **DF-05** | `B5P02`, `B5P03`, `B5P04` doc language | MEDIUM | Despite normalisation preambles added, B5P* body text still uses segment terminology ("school segment", "corporate segment"). New domain work built from these docs may still default to segment-forked thinking. |
| **DF-06** | `shared/segment_runtime.py` | MEDIUM | Segment runtime logic exists in the shared layer. This is the most direct instance of segment awareness inside the system core. Needs explicit documentation of purpose and a boundary decision: is this a valid entitlement helper or a segment-branching risk? |

---

## QUICK DOMAIN LOOKUP

> Fast reference for the most common build/retrieval needs.

| What you need | Go to |
|---|---|
| Capability model & entitlement | `B2P02` → `B2P05` → `capability_resolution.md` |
| Config resolution chain | `B2P01` → `capability_resolution.md` |
| Commerce / billing / subscription | `B3P01` → `B3P04` → `B3P05` → `DOC_07` |
| Learning core (courses, lessons, progress) | `ARCH_01` → `SPEC_09` → `SPEC_11` → `SPEC_12` |
| Assessment & certification | `assessment_service_spec.md` → `SPEC_14` |
| AI capabilities | `B6P01`–`B6P05` → `AI_01`–`AI_05` |
| Academy operations | `B5P01` → `services/academy-ops/` |
| School / workforce / university domains | `B5P02` / `B5P03` / `B5P04` |
| Auth, SSO, RBAC | `SPEC_01` → `SPEC_03` → `sso_spec.md` |
| Multi-tenancy | `ARCH_07` → `B2P06` → `tenant_service_spec.md` |
| System of Record | `SOR_01_system_of_record_design.md` → `services/system-of-record/` |
| Adapters (payment, comms, storage) | `adapter_inventory.md` → `B2P08` → `integrations/` |
| Offline capability | `offline_sync_interface_contract.md` → `offline_sync_spec.md` |
| Content protection / DRM | `media_security_interface_contract.md` → `media_security_spec.md` |
| Onboarding | `onboarding_spec.md` → `services/onboarding/` |
| Analytics & reporting | `B6P05` → `analytics_service_spec.md` → `learning_analytics_spec.md` |
| Event architecture | `ARCH_05` → `event_envelope.md` → `event_bus_design.md` |
| QC validation | `docs/qc/SUP_01` → `B7P01`–`B7P08` |
| API design | `core_rest_api.md` → `ARCH_06` → `infrastructure/api-gateway/` |
| Normalisation status | `progress.md` |
| Terminology (feature vs capability) | `DOC_NORM_01_terminology_bridge.md` |
| Drift flags | Section 18 of this file |
| Market overlay gaps | `gap_register.md` — Market Overlay section (MO-001–MO-044) |
| Market / GTM docs | Section 19 of this file |

---

## SECTION 19 — MARKET + BEHAVIORAL MASTER DOCS

### External Master Docs (outside repo root — `C:\LMS\LMS New\`)

| Path | Layer | Status | Description |
|---|---|---|---|
| `LMS_Pakistan_Market_Research_MASTER.md` | GOV | E | Master market research — merged MANUS AI + ChatGPT research. 21 sections, all 8 segments, pricing, SWOT, gaps, entry strategy. Authority for all market-derived behavioral contracts. |
| `LMS_Platform_Master_Behavioral_Spec.md` | GOV | E | Master behavioral spec — merged BOS + market-derived behavioral contract (BC-MR-01 through BC-MR-12). 8-part structure. Source authority for all BC-* contracts in this repo. |
| `LMS PLATFORM — MASTER PRODUCT & BUILD SPEC.md` | GOV | E | Master product spec — capability-driven platform definition, 18 cap domains, 5-layer config hierarchy, non-negotiable rules. Ground truth for all architecture. |

### Phase A2 Docs — PENDING (MO-015–MO-021)

| Path | Layer | Status | Description | Gap |
|---|---|---|---|---|
| `docs/specs/vocational_training_domain_spec.md` | SPEC | N | Vocational training domain spec — 6 capabilities, cert tracking, placement tracking, practical assessment. Most underserved niche. | MO-015 |
| `docs/specs/free_tier_operational_definition.md` | SPEC | N | Free tier operational definition — implements BC-FREE-01. Defines what free MUST include vs upgrade unlocks. | MO-016 |
| `docs/architecture/multi_branch_rbac_model.md` | ARCH | N | Multi-branch RBAC model — implements BC-BRANCH-01. HQ role, branch role, enforcement pattern, cross-branch analytics, Daily Action List scoping. | MO-017 |
| `docs/market/pakistan_market_pricing_guide.md` | GOV | N | Pakistan market pricing guide — PKR tiers per segment, payment method requirements, psychological thresholds, monetization model comparison. | MO-018 |
| `docs/market/gtm_entry_strategy.md` | GOV | N | GTM entry strategy — academy-first entry, WhatsApp-first wedge, 5-phase expansion sequence, anti-patterns. | MO-019 |
| `docs/market/competitive_intelligence.md` | GOV | N | Competitive intelligence — Nearpeer, Maqsad, Noon, Moodle, Google Classroom, gap map, differentiation summary. | MO-020 |
