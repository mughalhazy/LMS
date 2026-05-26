# LMS — Master Doc Catalogue
**Version:** 5.4 | **Date:** 2026-05-27 | **Location:** D:\LMS\Repo\doc-catalogue.md
**Merged from:** workspace/doc-catalogue.md v4.0 + Repo/doc-catalogue.md
**Stage:** Stage 3+4 COMPLETE, catalogue audit COMPLETE, Phase 2+3 normalisation COMPLETE, workspace + Repo docs/ restructure COMPLETE 2026-05-27, git initialised on both repos 2026-05-27
**Git:** `D:\LMS` master (2 commits) | `D:\LMS\Repo` master (5 commits, baseline 54c1af5)
**Flags:** `ARCHIVED` = moved to _archive/, file not deleted | `DEPRECATED` = superseded, file retained | `EMPTY` = placeholder stub on disk, content pending normalisation

**Columns:** File | Location | Description | Purpose
**Scope:** .md files only

---

## SECTION A — OPS DOCS

| File | Location | Description | Purpose |
|---|---|---|---|
| `doc-catalogue.md` | `Repo/` | This file — master index of all LMS docs | Single navigation reference for all doc decisions |
| `snapshot.md` | `workspace/ops/` | Session snapshot — project state, active work stream, key file map, do-not-touch rules | Read at session start for instant birds-eye orientation |
| `normalisation-tracker.md` | `Repo/` | 124 findings across 201 files — Phase 2 normalisation COMPLETE 2026-05-26 | Historical finding record; all 166 Phase 2 findings resolved (NF-089 TERM scan deferred per DOC_NORM_01) |
| `docs-rename-map.md` | `Repo/` | 204-file rename map — old name → new name with change reason — COMPLETE 2026-05-26 | Traceability record for the Phase 3 kebab-case rename pass; all 204 files renamed |
| `noise-kill-tracker.md` | `Repo/` | 219 docs scanned, 3 archived | Records all noise-kill decisions from May 2026 cleanup phase |
| `tracker.md` | `Repo/` | Repo restructuring tracker — pending items and approval status | Tracks backend restructuring decisions and sign-off status |
| `backend-restructuring.md` | `Repo/` | Backend restructuring record May 2026 | Documents what was restructured in the May 2026 reorganisation |
| `stage3-read-tracker.md` | `workspace/archive/` | Stage 3 read tracker — 313/313 files read, tagged, and logged across 14 batches | Line-by-line normalisation read progress log; COMPLETE 2026-05-25 |
| `progress.md` | `workspace/ops/` | Normalisation phase tracker — live status of all doc work | Session-by-session progress log for the normalisation project |
| `pending.md` | `workspace/ops/` | Pending work register — BOS gap resolution groups and drift flags | Tracks BOS gaps MO-001–MO-044 and deferred drift flags |
| `gap-register.md` | `workspace/ops/` | BOS overlay gap register — all 18 gaps with candidate docs and status | Formal gap register for behavioral operating spec overlay work |
| `ms-overlay-register.md` | `workspace/archive/` | Master Spec overlay gap register — 14 architectural contracts MSG-001–014 | CLOSED 2026-04-11 — records all MS overlay contract resolutions |
| `code-gap-register.md` | `workspace/archive/` | Code gap register — 111 code gaps CGAP-001 through MO-044 across all service tiers | Tracks implementation gaps from spec/arch overlay audit; 107 resolved, 4 deferred (MO-041–044) |
| `doc-catalogue-v4.0.md` (archived) | `workspace/archive/` | SUPERSEDED by this file — workspace master catalogue v4.0 | Archived to workspace/archive/ 2026-05-25 — replaced by this merged v5.0 |
| `normalisation-findings.md` | `workspace/archive/` | 166 Phase 2 normalisation findings — COMPLETE 2026-05-26 (NF-089 deferred) | Archived Phase 2 finding log; replaced by normalisation-tracker.md as historical record |

---

## SECTION B — REPO / CODE DOCS

### B1 — Anchors — docs/anchors/ (5 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `event-envelope.md` | `Repo/docs/anchors/` | Canonical 7-field event envelope — event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata | Single mandatory event schema all producers and consumers must implement |
| `doc-precedence.md` | `Repo/docs/anchors/` | Document priority order — BATCH > SPEC > ARCH > Legacy | Deterministic tie-breaker for resolving conflicts between LMS documentation sources |
| `capability-resolution.md` | `Repo/docs/anchors/` | Canonical capability → config → entitlement → final_state resolution flow | Single authoritative resolution sequence across config, entitlement, and capability registry services |
| `country-layer-architecture.md` | `Repo/docs/anchors/` | Canonical adapter-binding pattern for country layer | Translates tenant country codes into adapter selections — adapter pattern not country branching |
| `tenant-contract.md` | `Repo/docs/anchors/` | Canonical 6-field tenant payload — tenant_id, name, country_code, segment_type, plan_type, addon_flags | Locks the single authoritative tenant model for cross-service integration |

---

### B2 — Macro Architecture — docs/architecture/ ARCH series (8 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `core-system-architecture.md` | `Repo/docs/architecture/` | Core system architecture — domain map, service boundaries, data ownership | Defines the foundational layered architecture extending the Rails LMS runtime with domain services, API gateway, and event-driven integrations |
| `microservice-boundary-map.md` | `Repo/docs/architecture/` | Microservice boundary map — bounded contexts, service ownership rules | Maps every bounded context and service to its owned data, API surface, and event contracts |
| `domain-driven-design-map.md` | `Repo/docs/architecture/` | DDD map — bounded contexts, aggregates, domain events | Defines bounded contexts, aggregate roots, and DDD tactical elements aligned to existing repository models |
| `service-data-ownership-rules.md` | `Repo/docs/architecture/` | Data ownership rules — single system of record per entity | Establishes a single-system-of-record ownership matrix for every entity across all LMS services |
| `event-driven-architecture.md` | `Repo/docs/architecture/` | Event-driven architecture — event bus, topics, sagas, replay, DLQ | Defines the canonical event-driven architecture for decoupling LMS services via a durable event bus with schema governance and replay |
| `api-versioning-strategy.md` | `Repo/docs/architecture/` | API versioning — URI major versioning, lifecycle states, sunset policy | Specifies URI-based major versioning rules, deprecation policy, and parallel-version operation requirements |
| `multi-tenant-isolation-model.md` | `Repo/docs/architecture/` | Multi-tenant isolation — data, config, identity isolation per tenant | Defines tenant ownership hierarchy, context propagation rules, and row-level isolation enforcement |
| `observability-architecture.md` | `Repo/docs/architecture/` | Observability — metrics, logs, traces, SLA/SLO monitoring | Establishes a unified, tenant-aware observability stack covering logging, metrics, distributed tracing, and audit logging |

---

### B3 — Architecture Audit & Validation (6 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `architecture-full-audit-report.md` | `Repo/docs/architecture/` | Full architecture audit — DB write ownership, event contracts, tenant propagation | Audits all backend services for data ownership correctness, event contract integrity, and cross-service dependency |
| `circular-dependencies-audit-report.md` | `Repo/docs/architecture/` | Circular service dependency detection — Tarjan SCC analysis | Detects and documents circular dependency cycles in the LMS service graph |
| `duplicate-domains-detection-report.md` | `Repo/docs/architecture/` | Domain overlap detection report | Identifies domain boundary overlaps and duplicate responsibilities across the LMS service architecture |
| `data-isolation-analysis-report.md` | `Repo/docs/architecture/` | Data isolation validation report | Audits service data ownership and cross-service isolation risks |
| `event-ownership-analysis-report.md` | `Repo/docs/architecture/` | Event ownership validation report | Audits event producer ownership and detects potential duplications |
| `service-boundary-analysis-report.md` | `Repo/docs/architecture/` | Service boundary validation report | Validates service responsibilities and detects domain overlaps |

---

### B4 — Platform Infrastructure — B2P series (8 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `config-service-design.md` | `Repo/docs/designs/` | Config service — 5-layer resolution global→country→segment→plan→tenant | Designs a storage-agnostic hierarchical configuration resolution service supporting global-to-tenant override precedence |
| `entitlement-service-design.md` | `Repo/docs/designs/` | Entitlement service — capability allow/deny from segment, plan, country, add-ons | Designs a deterministic service that resolves which capabilities are enabled for a tenant |
| `feature-flag-system-design.md` | `Repo/docs/designs/` | Capability activation gate system — multi-scope dynamic activation | Designs a runtime feature flag system supporting multi-scope dynamic activation without redeployments |
| `usage-metering-service-design.md` | `Repo/docs/designs/` | Usage metering — tracks ai_calls, api_calls, active_learners, storage, analytics credits | Designs an event-driven usage tracking and aggregation service that feeds billing without owning billing logic |
| `capability-registry-service-design.md` | `Repo/docs/designs/` | Capability registry — single source of truth for capability metadata and dependency graph | Designs the authoritative registry for capability metadata and dependency graph relationships |
| `tenant-extension-model.md` | `Repo/docs/designs/` | Tenant extension fields — segment_type, country_code, plan_type, enabled_addons | Defines lightweight tenant profile extension fields providing stable commercial and regional inputs to downstream services |
| `audit-policy-layer-design.md` | `Repo/docs/designs/` | Audit policy layer — ledger, retention, compliance controls | Designs an independent audit logging and policy enforcement layer providing tamper-evident compliance evidence |
| `platform-integration-layer-design.md` | `Repo/docs/designs/` | Platform integration layer — adapter registration, routing, observability | Defines a stateless orchestration layer coordinating runtime decisions across config, entitlement, feature flags, capability registry, and usage metering |

---

### B5 — Commerce Domain — B3P series (8 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `commerce-domain-architecture.md` | `Repo/docs/designs/` | Commerce domain — product, pricing, checkout, invoice, subscription, revenue | Defines commerce domain architecture for LMS monetization operations |
| `catalog-service-design.md` | `Repo/docs/designs/` | Product catalog — SKUs, plans, bundles, add-ons | Defines and publishes sellable products for commerce without checkout concerns |
| `checkout-service-design.md` | `Repo/docs/designs/` | Checkout service — order assembly, validation, payment handoff | Converts purchase intent into committed order and triggers payment initiation |
| `invoice-billing-service-design.md` | `Repo/docs/designs/` | Invoice and billing service — SoR for invoices, payment state, adjustments | Creates financial obligations and orchestrates subscription billing cycles |
| `subscription-service-design.md` | `Repo/docs/designs/` | Subscription lifecycle — create, renew, change, cancel | Manages recurring access products with plan state and lifecycle transitions |
| `revenue-service-design.md` | `Repo/docs/designs/` | Revenue tracking and reporting — read-optimised, no billing duplication | Provides read-optimized revenue tracking and reporting for commerce operations |
| `academy-commerce-extensions.md` | `Repo/docs/designs/` | Academy commerce extensions — fee plans, batch billing | Defines academy monetization extension layer on core commerce domain |
| `owner-economics-service-design.md` | `Repo/docs/designs/` | Owner/instructor economics — revenue participation, earnings, payout calc | Manages how platform participants earn and track revenue participation |

---

### B6 — Operations Domain — B5P series (4 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `academy-operations-domain.md` | `Repo/docs/designs/` | Academy ops — batch/class ops, enrollment tracking, attendance, fee ops, branches | Governs batch/class operations and enrollment tracking for academies |
| `school-engagement-domain-design.md` | `Repo/docs/designs/` | School engagement — attendance, grading, parent portal, teacher-parent comms | Operationalizes classroom workflows with real-time parent visibility |
| `workforce-training-domain-design.md` | `Repo/docs/designs/` | Workforce training — onboarding, compliance, role readiness, manager oversight | Manages onboarding, compliance, and manager oversight for workforce training |
| `university-domain-design.md` | `Repo/docs/designs/` | University domain — faculty, advanced assessment, research, LTI/SCORM integration | Models higher-education operations for degree-granting institutions |

---

### B7 — AI & Intelligence — B6P series (5 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `ai-tutor-assist-design.md` | `Repo/docs/designs/` | AI tutor capability — conversational, guardrailed, escalation to human | Provides embedded learner support through AI guidance and explanations |
| `teacher-ai-assist-design.md` | `Repo/docs/designs/` | Teacher AI assist — lesson planning, at-risk detection, outreach tools | Defines assistive-only AI tools for teachers to reduce authoring effort |
| `recommendation-engine-design.md` | `Repo/docs/designs/` | Recommendation engine — learner profile, history, skills → personalised content | Designs data-driven recommendation engine for personalized learning paths |
| `learner-risk-insights-design.md` | `Repo/docs/designs/` | Learner risk — completion/drop-off probability, intervention triggers | Detects and explains learner risk conditions with actionable alert routing |
| `analytics-intelligence-layer-design.md` | `Repo/docs/designs/` | Analytics intelligence — optimisation insights, benchmarking, ranking | Generates actionable insights from analytics data for all segments |

---

### B8 — Domain Models & Normalization — DOC series + SOR (9 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `product-capabilities-matrix.md` | `Repo/docs/designs/` | Product capabilities matrix — tenant plan vs capability availability | Defines capability ownership and dependencies across platform modules |
| `global-education-model-framework.md` | `Repo/docs/designs/` | Global education model — framework for market-agnostic delivery | Defines universal education domain framework supporting multiple segments |
| `academy-operational-model.md` | `Repo/docs/designs/` | Academy operational model — lifecycle from onboarding to enrollment | Defines academy operational workflows |
| `tutor-operational-model.md` | `Repo/docs/designs/` | Tutor operational model — how independent tutors operate within LMS | Defines tutor workflows within LMS compatibility |
| `ai-capability-definition.md` | `Repo/docs/designs/` | AI capability definition — scope, guardrails, AI-assist rule | Defines LMS AI capability layer across four integrated services |
| `terminology-bridge.md` | `Repo/docs/designs/` | Terminology bridge — "feature" maps to "capability" in all legacy docs | Maps legacy terminology to canonical Master Spec language |
| `market-enforcements-capability-map.md` | `Repo/docs/designs/` | Maps MS§7 market enforcements to capability keys and service owners | Maps market enforcement requirements to implementing capability domains |
| `system-of-record-design.md` | `Repo/docs/designs/` | System of Record — student lifecycle, financial ledger, unified profile | Defines System of Record architecture for three authoritative data pillars |
| `domain-capability-extension-model.md` | `Repo/docs/designs/` | Extension model — how B5P use-case domains are capability-driven | Enables use-case-specific capability extensions without forking the platform |

---

### B9 — Interface Contracts — Active (10 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `capability-interface-contract.md` | `Repo/docs/contracts/` | Capability interface — lifecycle, dependency validation, usage tracking | Defines the runtime interface contract for capability plug-in modules |
| `capability-gating-model.md` | `Repo/docs/contracts/` | Capability gating — deterministic per-tenant capability enable/disable model | Governs rollout and billing alignment for capability activation |
| `communication-adapter-contract.md` | `Repo/docs/contracts/` | Communication adapter — channel-agnostic send/schedule/broadcast | Defines a channel-agnostic interface for outbound communication adapters |
| `config-resolution-interface-contract.md` | `Repo/docs/contracts/` | Config resolution interface — storage-agnostic runtime interface | Defines the runtime interface for hierarchical config resolution |
| `entitlement-interface-contract.md` | `Repo/docs/contracts/` | Entitlement interface — deterministic capability entitlement resolution | Specifies deterministic capability entitlement resolution for tenants |
| `media-security-interface-contract.md` | `Repo/docs/contracts/` | Media security — tokenised playback, watermark, anti-piracy | Specifies secure media access authorization and playback security |
| `offline-sync-interface-contract.md` | `Repo/docs/contracts/` | Offline sync — download orchestration, idempotent sync, resume | Defines offline synchronization orchestration and resume semantics |
| `payment-provider-adapter-contract.md` | `Repo/docs/contracts/` | Payment adapter — normalised payment create/verify/refund | Specifies provider-agnostic payment adapter contract for commerce |
| `storage-adapter-interface-contract.md` | `Repo/docs/contracts/` | Storage adapter — protocol definition, canonical buckets | Defines provider-agnostic storage adapter for file/object operations |
| `usage-metering-interface-contract.md` | `Repo/docs/contracts/` | Usage metering — billable event schema | Defines reusable capability usage metering and aggregation contract |

### B9d — Interface Contracts — Deprecated (4 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `audit_logging.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `audit-policy-layer-design.md` | Moved to _archive/ 2026-05-27 |
| `config_service.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `config-service-design.md` | Moved to _archive/ 2026-05-27 |
| `content-storage-model.md` | `Repo/docs/contracts/` | Content storage — object storage, metadata, versioning | Defines storage locations, metadata schemas, and delivery strategies for all LMS content types |
| `core_system_architecture.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `core-system-architecture.md` | Moved to _archive/ 2026-05-27 |

---

### B10 — Domain Models (9 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `adaptive-learning-engine.md` | `Repo/docs/designs/` | Adaptive learning engine — mastery-based path adjustment | Defines components and data flows for dynamically adjusting learner paths based on mastery and engagement signals |
| `agi-ready-architecture.md` | `Repo/docs/designs/` | AGI-compatible architecture — multi-agent workflows, safety, governance | Describes a layered architecture enabling AGI-grade multi-agent workflows |
| `ai-course-generation-pipeline.md` | `Repo/docs/designs/` | AI course generation — draft, review, human approval gates | Defines the staged pipeline for automatically generating structured courses and quiz banks |
| `ai-learning-copilot.md` | `Repo/docs/designs/` | AI learning copilot — in-session assistance and skill recommendations | Describes capabilities and I/O contracts for an AI assistant guiding learners |
| `enterprise-admin-model.md` | `Repo/docs/designs/` | Enterprise admin model — RBAC, delegation, org hierarchy for admins | Defines administrative roles and governance across enterprise organization |
| `data-ownership-rules.md` | `Repo/docs/designs/` | LMS data ownership rules — service-level table assignments | Defines service-level data ownership and database table assignments |
| `multi-branch-rbac-model.md` | `Repo/docs/designs/` | Multi-branch RBAC — HQ role, branch role, enforcement pattern | Enables multi-branch operations with unified HQ visibility |
| `skills-graph-model.md` | `Repo/docs/designs/` | Skills graph — competency framework, inference, decay | Defines skill taxonomy, relationships, and user skill tracking |
| `feature_inventory.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `docs/specs/capability-inventory.md` | Moved to _archive/ 2026-05-27 |

---

### B11 — Cloud, Strategy & Service Map (12 active + 2 deprecated)

| File | Location | Description | Purpose |
|---|---|---|---|
| `cloud-architecture-ems-lms.md` | `Repo/docs/architecture/` | Cloud architecture — EMS+LMS combined deployment on AWS | Catalogues AWS cloud infrastructure components for the combined EMS/LMS platform |
| `cloud_architecture_lms.md` | `Repo/docs/architecture/` | ARCHIVED — moved to _archive/ | Was: Cloud architecture for LMS standalone deployment |
| `event-domain-catalogue.md` | `Repo/docs/architecture/` | Event domain definitions — bounded context event ownership | Catalogues all domain events with producers, consumers, and purposes |
| `security-architecture.md` | `Repo/docs/architecture/` | Security architecture — AuthN/AuthZ, data security, compliance | Defines security components and implementation requirements for the LMS platform |
| `service-map.md` | `Repo/docs/architecture/` | Service map — all services with ownership and inter-service contracts | Maps all backend services to their domain responsibilities and primary entities |
| `domain-boundaries-backend.md` | `Repo/docs/architecture/` | Domain boundary definitions for LMS backend | Defines service ownership and responsibility boundaries across LMS domains |
| `event-bus-design.md` | `Repo/docs/architecture/` | Event bus — topics, partitioning, schema registry, DLQ | Documents LMS domain events and event-driven communication patterns |
| `observability_design.md` | `Repo/docs/architecture/` | ARCHIVED — moved to _archive/ | Was: Observability design — metrics, logs, traces |
| `platform-evolution-model.md` | `Repo/docs/architecture/` | Long-term evolution model — 20–30 year service, API, schema compatibility | Defines platform evolution strategy over a long-horizon timeline |
| `scalability-strategy.md` | `Repo/docs/architecture/` | Scalability strategy — concurrency, partitioning, resilience, multi-region | Outlines horizontal scaling, autoscaling, and multi-region deployment approach |
| `tenant-customization-catalogue.md` | `Repo/docs/architecture/` | Tenant customisation — branding, workflows, compliance, feature control | Enables tenant-level branding, workflows, compliance, and feature control |
| `tenant-isolation-strategy.md` | `Repo/docs/architecture/` | Tenant isolation strategy — shared-schema to database-per-tenant models | Outlines isolation models from shared-schema to database-per-tenant |
| `event_driven_architecture.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `event-driven-architecture.md` | Moved to _archive/ 2026-05-27 |
| `microservice_boundaries.md` (archived) | `Repo/docs/architecture/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `microservice-boundary-map.md` | Moved to _archive/ 2026-05-27 |

---

### B12 — Storage Design — docs/architecture/ (1 file)

| File | Location | Description | Purpose |
|---|---|---|---|
| `file-storage-design.md` | `Repo/docs/designs/` | File storage design — object storage buckets (video, document, SCORM) + CDN access patterns | Maps LMS content types to storage components, delivery methods, and signed URL access patterns |

---

### B13 — Canonical Service Specs — SPEC series (9 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `auth-service-spec.md` | `Repo/docs/specs/` | Auth service spec — credential validation, token issuance, session security | Defines authentication and session-security boundary |
| `rbac-service-spec.md` | `Repo/docs/specs/` | RBAC service spec — roles, permissions, assignments, real-time access decisions | Defines the authorization domain service |
| `institution-service-spec.md` | `Repo/docs/specs/` | Institution service spec — global institution model, lifecycle, hierarchy | Introduces a global institution model above tenant runtime entities |
| `program-service-spec.md` | `Repo/docs/specs/` | Program service spec — curriculum container, ordered course collections | Specifies the curriculum container service organizing ordered course collections into programs |
| `cohort-service-spec.md` | `Repo/docs/specs/` | Cohort service spec — formal cohorts, academy batches, tutor groups | Defines learner grouping constructs supporting multiple cohort types |
| `course-service-spec.md` | `Repo/docs/specs/` | Course service spec — course aggregate lifecycle and metadata management | Specifies the system-of-record microservice for course lifecycle |
| `enrollment-service-spec.md` | `Repo/docs/specs/` | Enrollment service spec — learner-to-course participation lifecycle | Defines the learner-to-course participation record ownership |
| `progress-service-spec.md` | `Repo/docs/specs/` | Progress service spec — learner progress and completion state | Specifies the system of record for learner progress at lesson, course, and path levels |
| `certificate-service-spec.md` | `Repo/docs/specs/` | Certificate service spec — issuance, verification, revocation, badges | Operationalizes the Rails Certificate model for credential issuance |

---

### B14 — AI Service Specs — AI series (5 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `ai-tutor-service-spec.md` | `Repo/docs/specs/` | AI tutor service spec — inputs, logic, guardrails, outputs | Defines inputs, logic, guardrails, and outputs for the AI-powered tutoring service |
| `recommendation-service-spec.md` | `Repo/docs/specs/` | AI recommendation service spec — ranked, explainable content recommendations | Specifies the service that generates ranked, explainable course and content recommendations |
| `skill-inference-service-spec.md` | `Repo/docs/specs/` | AI skill inference service spec — derives and persists learner skill profiles | Defines the service that derives and persists learner skill profiles from evidence |
| `learning-analytics-service-spec.md` | `Repo/docs/specs/` | AI learning analytics service spec — event ingestion, aggregated metrics | Specifies the analytics service that ingests learning events and produces aggregated metrics |
| `learning-knowledge-graph-spec.md` | `Repo/docs/specs/` | AI learning knowledge graph — intelligence graph for AI tutoring, recommendations, skill inference | Defines the derived intelligence graph layer powering AI features |

---

### B15 — Per-Service Specs (31 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `adapter-inventory.md` | `Repo/docs/specs/` | Adapter inventory — all required adapters, interface contracts, implementation status | Catalogues all required external adapters per Master Spec §4 |
| `analytics-service-spec.md` | `Repo/docs/specs/` | Analytics service spec — platform intelligence layer | Documents the analytics service as the platform's primary intelligence layer |
| `assessment-service-spec.md` | `Repo/docs/specs/` | Assessment service spec — definition, delivery, attempts, grading | Specifies the full assessment execution lifecycle |
| `auth-service-test-plan.md` | `Repo/docs/specs/` | Auth service test plan — all test suites and validation scenarios | Enumerates all test suites and scenarios required to validate the auth service |
| `capability-domain-map.md` | `Repo/docs/specs/` | Full capability domain map — all 18 MS§5 domains | Maps all 18 Master Spec capability domains to their service owners, design docs, specs, and build status |
| `capability-registry-service-spec.md` | `Repo/docs/specs/` | Capability registry service spec — metadata, dependency graphs, versioned snapshots | Specifies the single source of truth service for capability metadata |
| `capability-inventory.md` | `Repo/docs/specs/` | Capability domain inventory — platform capability domains mapped to LMS entities | Catalogues all platform capability domains and features |
| `billing-and-usage-model.md` | `Repo/docs/specs/` | Billing and usage model — usage metrics, billing architecture, metering events | Defines usage metrics, billing architecture, metering events, and capability gating |
| `economic-capabilities-user-spec.md` | `Repo/docs/specs/` | Economic capabilities — user-level revenue participation, tracking, payouts | Specifies how individual platform participants earn revenue |
| `enterprise-control-spec.md` | `Repo/docs/specs/` | Enterprise control spec — RBAC, audit logs, compliance, integration management | Defines the enterprise governance service |
| `event-ingestion-spec.md` | `Repo/docs/specs/` | Event ingestion service spec — ingestion, normalization, persistence, forwarding | Specifies the platform boundary service for ingesting and forwarding LMS domain events |
| `exam-engine-spec.md` | `Repo/docs/specs/` | Exam engine spec — secure delivery, session management, proctoring, attempt lifecycle | Specifies the secure exam delivery engine |
| `financial-ledger-spec.md` | `Repo/docs/specs/` | Financial ledger spec — student fee obligations, payment tracking, balance state | Defines the student-facing financial ledger |
| `free-tier-operational-definition.md` | `Repo/docs/specs/` | Free tier operational definition — what free must include and must not restrict | Formally defines free tier entitlements and restrictions |
| `integration-service-spec.md` | `Repo/docs/specs/` | Integration service spec — HRIS sync, webhooks, LTI, third-party adapter routing | Specifies the platform's integration hub |
| `interaction-layer-spec.md` | `Repo/docs/specs/` | Interaction layer spec — conversational and action-driven service for learner and operator channels | Defines the conversational interaction service |
| `media-pipeline-spec.md` | `Repo/docs/specs/` | Media pipeline spec — upload through transcoding to CDN delivery | Describes the end-to-end video processing pipeline |
| `media-security-spec.md` | `Repo/docs/specs/` | Media security spec — entitlement-gated delivery, watermarking, anti-piracy | Defines entitlement-gated media delivery and anti-piracy controls |
| `monolith-to-services-migration.md` | `Repo/docs/specs/` | Monolith to services extraction plan — incremental Rails migration strategy | Defines the incremental migration strategy from the Rails LMS monolith to Enterprise LMS V2 |
| `notification-service-spec.md` | `Repo/docs/specs/` | Notification service spec — dispatch layer routing to email, SMS, WhatsApp, push | Specifies the communication dispatch layer |
| `offline-sync-spec.md` | `Repo/docs/specs/` | Offline sync spec — entitlement-gated offline access, local storage, conflict resolution | Defines entitlement-gated offline content access and sync engine |
| `onboarding-spec.md` | `Repo/docs/specs/` | Onboarding spec — automated tenant setup from creation to first operational use | Specifies automated tenant setup and capability activation |
| `operations-os-spec.md` | `Repo/docs/specs/` | Operations OS spec — admin-facing operational intelligence, prioritised actions | Defines the admin-facing operational intelligence layer |
| `platform-behavioral-contract.md` | `Repo/docs/specs/` | Platform behavioral contract — meta-behavioral governing doc | Establishes the meta-behavioral contract governing how the platform must act as a proactive operator |
| `session-service-spec.md` | `Repo/docs/specs/` | Session service spec — time-bound learning delivery lifecycle, scheduling, cohort linkage | Specifies time-bound learning delivery instance lifecycle |
| `sso-spec.md` | `Repo/docs/specs/` | SSO spec — SAML 2.0, OAuth 2.0, OIDC authentication flows | Specifies authentication flows and required fields for SSO integrations |
| `system-economics-spec.md` | `Repo/docs/specs/` | System economics spec — revenue analytics, cost tracking, profitability | Defines platform-operator financial intelligence |
| `user-service-spec.md` | `Repo/docs/specs/` | User service spec — profile and identity lifecycle domain | Defines the profile and identity lifecycle domain extending the existing LMS User entity |
| `vocational-training-domain-spec.md` | `Repo/docs/specs/` | Vocational training domain spec — 6 capabilities, cert tracking, placement tracking | Defines the capability domain extension for vocational training institutions |
| `workflow-engine-spec.md` | `Repo/docs/specs/` | Workflow engine spec — event-driven automation, multi-step workflows | Specifies the event-driven automation backbone executing multi-step workflows |
| `tenant-service-spec.md` | `Repo/docs/specs/` | EMPTY — Tenant service spec canonical target (placeholder stub) — tenant lifecycle, configuration, plan linkage, isolation policy | Specifies the system-of-record for tenant lifecycle; content pending normalisation |

---

### B15a — Feature Specs (17 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `compliance-reporting-spec.md` | `Repo/docs/specs/features/` | Compliance reporting spec — data sources, fields, report structure | Defines data sources and structure for standard compliance and training reports |
| `content-service-spec.md` | `Repo/docs/specs/features/` | Content service spec — upload, metadata management, retrieval | Specifies upload, metadata management, and retrieval for all supported content types |
| `content-versioning-spec.md` | `Repo/docs/specs/features/` | Content versioning spec — version creation, rollback, publishing | Defines version creation, rollback, and publishing operations for immutable content versioning |
| `feature-flags-spec.md` | `Repo/docs/specs/features/` | Feature flags spec — configurations, targeting rules, rollout strategies | Defines feature flag configurations, targeting rules, and rollout strategies |
| `learning-analytics-spec.md` | `Repo/docs/specs/features/` | Learning analytics spec — completion rate, engagement score, drop-off rate | Defines metric calculations for key learning analytics |
| `learning-path-spec.md` | `Repo/docs/specs/features/` | Learning path spec — data model, sequencing, completion rules, prerequisite graph | Defines the data model and rules for structured learning paths |
| `lesson-service-spec.md` | `Repo/docs/specs/features/` | Lesson service spec — lesson lifecycle, ordering, delivery state within courses | Specifies the lesson service as system of record for lesson lifecycle |
| `localization-spec.md` | `Repo/docs/specs/features/` | Localization spec — language packs, regional formats, translation key taxonomy | Defines language packs, regional format rules, and translation key taxonomy for multi-locale support |
| `manager-dashboard-spec.md` | `Repo/docs/specs/features/` | Manager dashboard spec — team learning progress data sources and metrics | Specifies data sources and metrics powering team-facing dashboards |
| `org-hierarchy-spec.md` | `Repo/docs/specs/features/` | Org hierarchy spec — Organization → Department → Team entity model | Defines the entity model and rules for a three-level org hierarchy |
| `performance-capabilities-spec.md` | `Repo/docs/specs/features/` | Performance capabilities spec — high concurrency, session isolation, load resilience | Documents cross-cutting infrastructure capabilities for performance |
| `prerequisite-engine-spec.md` | `Repo/docs/specs/features/` | Prerequisite engine spec — rule types, enforcement logic, dependency gates | Defines rule types and enforcement logic for course prerequisites |
| `progress-tracking-spec.md` | `Repo/docs/specs/features/` | Progress tracking spec — events, fields, consumer services | Specifies the events, fields, and consumer services for tracking progress |
| `rbac-service-spec-v0.md` | `Repo/docs/specs/features/` | RBAC authorization system spec — roles, permissions, scope bindings | Defines roles, permissions, scope bindings, and assignment lifecycle rules |
| `reporting-spec.md` | `Repo/docs/specs/features/` | Reporting engine spec — scheduled reports, export formats, dashboard feeds | Specifies scheduled reports, export formats, and dashboard feed contracts |
| `scorm-runtime-spec.md` | `Repo/docs/specs/features/` | SCORM runtime spec — package launch, progress tracking, completion reporting | Defines runtime operations for SCORM package launch and completion reporting |
| `skill-analytics-spec.md` | `Repo/docs/specs/features/` | Skill analytics spec — skill progress metrics, gap detection | Defines algorithms for computing skill progress metrics and detecting skill gaps |

---

### B15b — Deprecated Specs (5 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `auth-service-spec-v0.md` | `Repo/docs/specs/` | DEPRECATED → auth-service-spec.md | Legacy auth service spec — superseded |
| `cohort_spec.md` (archived) | `Repo/docs/specs/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `cohort-service-spec.md` | Moved to _archive/ 2026-05-27 |
| `course_service_spec.md` (archived) | `Repo/docs/specs/_archive/` | ARCHIVED — was DEPRECATED+EMPTY redirect stub; canonical is `course-service-spec.md` | Moved to _archive/ 2026-05-27 |
| `GEN_14_certificate_service.md` | `Repo/docs/specs/` | DEPRECATED + EMPTY → certificate-service-spec.md | Legacy certificate service spec — superseded; placeholder stub on disk, content pending |
| `tenant-service-spec-v0.md` | `Repo/docs/specs/` | DEPRECATED → tenant-service-spec.md | Legacy tenant service spec — superseded; file confirmed on disk |

---

### B16 — API Docs — docs/api/ (8 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `analytics-api.md` | `Repo/docs/api/` | Analytics API — query endpoints for dashboards and reports | API surface for analytics consumers |
| `api-contract-validation-report.md` | `Repo/docs/api/` | API contract validation — gate 2 QC report | Validates API contracts at gate 2 |
| `api-gateway-design.md` | `Repo/docs/api/` | API gateway design — routing, auth, rate limiting, versioning | Defines API gateway architecture and configuration |
| `api-spec-validation-report.md` | `Repo/docs/api/` | API spec validation — gate 1 QC report | Validates API specs at gate 1 |
| `auth-service-api.md` | `Repo/docs/api/` | Auth service API — token issuance, session, MFA endpoints | API reference for auth service endpoints |
| `content-api.md` | `Repo/docs/api/` | Content API — course/lesson CRUD, media, versioning endpoints | API reference for content service endpoints |
| `core-rest-api.md` | `Repo/docs/api/` | Core REST API — canonical API patterns, versioning, error contracts | Canonical API pattern reference for all services |
| `integration-api.md` | `Repo/docs/api/` | Integration API — webhooks, HRIS sync, LTI endpoints | API reference for integration service endpoints |

---

### B17 — Data Schemas — docs/data/ (13 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `global-education-schema.md` | `Repo/docs/data/` | Global education schema — canonical entity definitions across all segments | Extends the existing LMS entity set to support global education operations |
| `learning-event-schema.md` | `Repo/docs/data/` | Learning event schema — event envelope, event types, xAPI alignment | Defines the canonical event model for all learner and system activity |
| `knowledge-graph-schema.md` | `Repo/docs/data/` | Knowledge graph schema — skills, concepts, relationships | Defines an AI-reasoning-ready knowledge graph augmenting relational LMS entities |
| `institution-hierarchy-schema.md` | `Repo/docs/data/` | Institution hierarchy schema — schools, universities, academies, corporate | Defines a single hierarchy model supporting all institution types |
| `cohort-batch-schema.md` | `Repo/docs/data/` | Cohort/batch schema — formal cohorts, academy batches, tutor-led groups | Designs a delivery-structure schema supporting all cohort types |
| `assessment-data-schema.md` | `Repo/docs/data/` | Assessment data schema — quiz, assignment, exam, mock test, board-style | Defines the assessment data model covering all delivery modes |
| `ai-interaction-schema.md` | `Repo/docs/data/` | AI interaction schema — AI tutor conversations, recommendations, skill inference | Defines a tenant-safe, auditable schema for capturing AI interactions |
| `learning-data-model-overview.md` | `Repo/docs/data/` | Learning data model overview — Institution, Program, Cohort, Session, Course | Defines a simple, extensible learning data model for institutional training operations |
| `analytics-data-model.md` | `Repo/docs/data/` | Analytics data model — event types, data fields, aggregation strategies | Defines event types, data fields, and aggregation strategies for learner activity analytics |
| `auth-service-storage-contract.md` | `Repo/docs/data/` | Auth service storage contract — exclusive ownership, table structure | Specifies the exclusive ownership and table structure of auth-service persistence objects |
| `core-lms-schema.md` | `Repo/docs/data/` | Core LMS relational schema — User, Course, Lesson, Enrollment, Progress, Certificate | Defines the core relational table set and relationships for the LMS platform |
| `data-model-validation-report.md` | `Repo/docs/data/` | Data model validation report — cross-schema findings, missing entities, gaps | Documents cross-schema validation findings |
| `database-schema-validation-report.md` | `Repo/docs/data/` | Database schema validation — gate 2 QC | Records QC gate 2 findings on table ownership, cross-service coupling, and terminology |

---

### B18 — QC Reports — docs/qc/ (28 .md files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `architecture-consistency-check-report.md` | `Repo/docs/qc/` | Architecture consistency — QC gate 1 | Documents service naming issues, domain boundary overlaps, and event-service misalignments |
| `audit-logging-verification-report.md` | `Repo/docs/qc/` | Audit logging verification | Verifies all required audit events include mandatory fields across backend services |
| `auth-service-qc-report.md` | `Repo/docs/qc/` | Auth service QC loop report | Records multi-pass QC scoring and incremental defect corrections for the authentication service |
| `B3P05_payment_integration_qc_report.md` | `Repo/docs/qc/` | ARCHIVED — moved to _archive/ | Was: Payment integration QC report |
| `capability-registry-validation-report.md` | `Repo/docs/qc/` | Capability registry validation — PASS | Summarises validation results for 19 capabilities across 10 domains |
| `entitlement-resolution-validation-report.md` | `Repo/docs/qc/` | Entitlement resolution validation — PASS | Validates entitlement resolution flow across multiple tenant segment scenarios |
| `config-resolution-validation-report.md` | `Repo/docs/qc/` | Config resolution validation — PASS | Validates deterministic config layer merging across test scenarios |
| `commerce-flow-validation-report.md` | `Repo/docs/qc/` | Commerce flow validation — PASS | Validates end-to-end commerce purchase flow across success, failure, and refund paths |
| `payment-adapter-validation-report.md` | `Repo/docs/qc/` | Payment adapter validation — PASS | Validates JazzCash and Easypaisa adapter flows |
| `communication-workflow-validation-report.md` | `Repo/docs/qc/` | Communication workflow validation — PASS | Validates WhatsApp/SMS workflow trigger-to-delivery sequences |
| `delivery-system-validation-report.md` | `Repo/docs/qc/` | Delivery system validation — PASS | Validates secure media access control and offline sync entitlement enforcement |
| `end-to-end-system-validation-report.md` | `Repo/docs/qc/` | End-to-end system validation | Consolidates all Batch 7 upstream validation results |
| `cross-service-dependency-check-report.md` | `Repo/docs/qc/` | Final QC — cross-service dependency check | Parses all service import graphs to detect boundary violations and circular dependencies |
| `load-test-preparation-report.md` | `Repo/docs/qc/` | Load test preparation report | Documents gateway scaling tuning, autoscaling policy additions, and k6 load script creation |
| `end-to-end-validation-report.md` | `Repo/docs/qc/` | P18 end-to-end validation | Confirms all 39 runtime services pass registration, security, observability, and gateway checks |
| `pakistan-wedge-validation-report.md` | `Repo/docs/qc/` | Pakistan wedge validation — final | Final validation across 10 Pakistan-market wedge categories |
| `feature-completeness-check-report.md` | `Repo/docs/qc/` | QC gate 1 — feature completeness | Identifies missing modules and overlapping feature ownership risks |
| `event-architecture-validation-report.md` | `Repo/docs/qc/` | QC gate 2 — event architecture validation | Checks every domain event for single-producer ownership, naming convention, and consumer alignment |
| `service-boundary-validation-report.md` | `Repo/docs/qc/` | QC gate 2 — service boundary validation | Identifies responsibility overlaps, domain boundary mismatches, and stage-alignment gaps |
| `code-structure-validation-report.md` | `Repo/docs/qc/` | QC gate 3 — code structure validation | Scans 38 services to verify required file layout and absence of cross-service imports |
| `event-publishing-validation-report.md` | `Repo/docs/qc/` | QC gate 3 — event publishing validation | Validates all domain events conform to schema contracts and use the event bus abstraction |
| `service-communication-validation-report.md` | `Repo/docs/qc/` | QC gate 4 — service communication validation | Validates inter-service communication patterns against architecture, spec, API, and integration docs |
| `system-hardening-report.md` | `Repo/docs/qc/` | System hardening QC | Validates production hardening across security, performance, resilience, observability, AI safety |
| `full-system-integration-validation-report.md` | `Repo/docs/qc/` | Full system integration validation | Validates the integration surface between all generated services and core LMS runtime entities |
| `service-map-verification-report.md` | `Repo/docs/qc/` | Stage 3 service map verification | Checks that all expected services across all domains are present |
| `platform-governor-certification-report.md` | `Repo/docs/qc/` | Platform governor final certification | Final cross-wave governance certification covering domain ownership, APIs, events, tenant isolation |
| `system-final-validation-report.md` | `Repo/docs/qc/` | System final validation report | Consolidates results from QC Gates 3–4, Final QC Gate, and Hardening Gate |
| `tenant-model-validation-report.md` | `Repo/docs/qc/` | Tenant model validation — QC gate 2 | Identifies missing tenant_id columns and tenant boundary enforcement gaps |

---

### B19 — Integration Docs — docs/integrations/ (6 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `auth-lifecycle-events.md` | `Repo/docs/integrations/` | Auth lifecycle events — login, logout, provision, deprovision events | Defines the event envelope and payload structure for all authentication lifecycle events |
| `hris-sync-spec.md` | `Repo/docs/integrations/` | HRIS sync spec — employee, org, enrollment field mapping | Specifies the field-level mapping between HRIS source data and LMS destination tables |
| `lti-consumer-spec.md` | `Repo/docs/integrations/` | LTI consumer spec — receive LTI 1.3 launch from external tools | Specifies how the LMS acts as an LTI 1.3 consumer to integrate and capture results |
| `lti-provider-spec.md` | `Repo/docs/integrations/` | LTI provider spec — expose LMS courses as LTI tools | Defines how the LMS acts as an LTI 1.3 provider exposing content to external platforms |
| `standards-support.md` | `Repo/docs/integrations/` | Standards support — xAPI, SCORM, LTI, SCIM, SAML, OIDC | Documents e-learning standards supported by the LMS and their implementation requirements |
| `webhook-system-spec.md` | `Repo/docs/integrations/` | Webhook system spec — event delivery, retry, HMAC signature | Specifies the webhook delivery system including event payloads, retry policies, and security signing |

---

### B20 — Market Docs — docs/market/ (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `competitive-intelligence.md` | `Repo/docs/market/` | Competitive intelligence — Nearpeer, Maqsad, Noon, Moodle, Google Classroom | Provides gap map and differentiation summary for Pakistan LMS market |
| `gtm-entry-strategy.md` | `Repo/docs/market/` | GTM entry strategy — academy-first entry, WhatsApp-first wedge, 5-phase expansion | Defines the go-to-market sequence, entry wedge, and expansion anti-patterns |
| `pakistan-market-pricing-guide.md` | `Repo/docs/market/` | Pakistan market pricing — PKR tiers, payment methods, psychological thresholds | Defines per-segment pricing, payment method requirements, and monetization model comparison |

---

### B21 — Workspace Foundation — workspace/foundation/ (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `product-build-spec.md` | `workspace/foundation/` | Master product spec v1.0 — capability-driven platform identity, 18 cap domains | Ground truth for all architecture — non-negotiable capability rules and platform identity |
| `market-research.md` | `workspace/foundation/` | Master market research — 21 sections, 8 segments, pricing, SWOT, gaps, entry strategy | Authority for all market-derived behavioral contracts BC-MR-01 through BC-MR-12 |
| `behavioral-spec.md` | `workspace/foundation/` | Master behavioral spec v1.0 — merged BOS + market-derived behavioral contract | Source authority for all BC-* contracts in the repo |

---

### B22 — Design System — workspace/design-system/ (3 .md + 1 .html)

| File | Location | Description | Purpose |
|---|---|---|---|
| `design-system.md` | `workspace/design-system/` | Design system v2.4 — tokens, shells, 25 component specs, motion, interaction rules, icons | Single source of truth for all UI component design decisions |
| `behavior-to-ui.md` | `workspace/design-system/` | 32 behavioral rules mapped to UI patterns | Source authority for all R-rule references in Assembly Contracts |
| `framework-gap-register.md` | `workspace/design-system/` | Framework evolution register — 14 gaps logged and resolved FG-001–FG-014 | Sole entry point for framework changes — two-layer resolution protocol |

---

### B23 — Page Definitions — workspace/page-definitions/ (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `ui-framework.md` | `workspace/page-definitions/` | Master UI system v3.7 — 16 archetypes, 32 behavioral rules, component registry, Assembly Contracts A1–A16 | Source of truth for all UI decisions and page build sequence |
| `page-inventory.md` | `workspace/page-definitions/` | Authoritative page inventory v1.0 — 119 pages across 16 archetypes A1–A16 | Full listing of all pages derived from 23 backend services |
| `entity-contracts.md` | `workspace/page-definitions/` | Backend-grounded contract reference — entity state machines, operations, required fields, business rules | Source of truth for entity state and operation contracts used in UI |

---

### B24 — Audit Docs — workspace/audit/ (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `html-audit-approach.md` | `workspace/audit/` | HTML audit methodology — scope, per-page checks, audit order | Defines the audit approach for 118 HTML prototype pages |
| `inconsistency-register.md` | `workspace/audit/` | HTML audit output — 191 findings across 60 pages INC-001–INC-191 | Records all UI inconsistency findings and their fix status |
| `backend-audit-plan.md` | `workspace/audit/` | Backend audit plan v2.0 — 58 new pages vs. backend, 20 risk flags | Defines the audit plan for validating 58 new pages against backend contracts |

---

---

## SECTION C — BACKEND SERVICES

### C1 — Service READMEs (45 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `README.md` | `Repo/backend/services/ai-tutor-service/` | AI tutor service — service overview and setup | Technical overview for ai-tutor-service |
| `README.md` | `Repo/backend/services/api-key-service/` | API key service — service overview and setup | Technical overview for api-key-service |
| `README.md` | `Repo/backend/services/assessment-service/` | Assessment service — service overview and setup | Technical overview for assessment-service |
| `README.md` | `Repo/backend/services/attempt-service/` | Attempt service — service overview and setup | Technical overview for attempt-service |
| `README.md` | `Repo/backend/services/auth-service/` | Auth service — service overview and setup | Technical overview for auth-service |
| `README.md` | `Repo/backend/services/badge-service/` | Badge service — service overview and setup | Technical overview for badge-service |
| `README.md` | `Repo/backend/services/certificate-service/` | Certificate service — service overview and setup | Technical overview for certificate-service |
| `README.md` | `Repo/backend/services/cohort-service/` | Cohort service — service overview and setup | Technical overview for cohort-service |
| `README.md` | `Repo/backend/services/content-service/` | Content service — service overview and setup | Technical overview for content-service |
| `README.md` | `Repo/backend/services/course-generation-service/` | Course generation service — service overview and setup | Technical overview for course-generation-service |
| `README.md` | `Repo/backend/services/course-service/` | Course service — service overview and setup | Technical overview for course-service |
| `README.md` | `Repo/backend/services/department-service/` | Department service — service overview and setup | Technical overview for department-service |
| `README.md` | `Repo/backend/services/email-service/` | Email service — service overview and setup | Technical overview for email-service |
| `README.md` | `Repo/backend/services/enrollment-service/` | Enrollment service — service overview and setup | Technical overview for enrollment-service |
| `README.md` | `Repo/backend/services/event-ingestion-service/` | Event ingestion service — service overview and setup | Technical overview for event-ingestion-service |
| `README.md` | `Repo/backend/services/group-service/` | Group service — service overview and setup | Technical overview for group-service |
| `README.md` | `Repo/backend/services/hr-helpdesk-service/` | HR helpdesk service — service overview and setup | Technical overview for hr-helpdesk-service |
| `README.md` | `Repo/backend/services/hris-sync-service/` | HRIS sync service — service overview and setup | Technical overview for hris-sync-service |
| `README.md` | `Repo/backend/services/institution-service/` | Institution service — service overview and setup | Technical overview for institution-service |
| `README.md` | `Repo/backend/services/learning-analytics-service/` | Learning analytics service — service overview and setup | Technical overview for learning-analytics-service |
| `README.md` | `Repo/backend/services/learning-path-service/` | Learning path service — service overview and setup | Technical overview for learning-path-service |
| `README.md` | `Repo/backend/services/lesson-service/` | Lesson service — service overview and setup | Technical overview for lesson-service |
| `README.md` | `Repo/backend/services/lti-service/` | LTI service — service overview and setup | Technical overview for lti-service |
| `README.md` | `Repo/backend/services/media-service/` | Media service — service overview and setup | Technical overview for media-service |
| `README.md` | `Repo/backend/services/notification-service/` | Notification service — service overview and setup | Technical overview for notification-service |
| `README.md` | `Repo/backend/services/org-service/` | Org service — service overview and setup | Technical overview for org-service |
| `README.md` | `Repo/backend/services/prerequisite-engine-service/` | Prerequisite engine service — service overview and setup | Technical overview for prerequisite-engine-service |
| `README.md` | `Repo/backend/services/program-service/` | Program service — service overview and setup | Technical overview for program-service |
| `README.md` | `Repo/backend/services/progress-service/` | Progress service — service overview and setup | Technical overview for progress-service |
| `README.md` | `Repo/backend/services/push-service/` | Push service — service overview and setup | Technical overview for push-service |
| `README.md` | `Repo/backend/services/quiz-engine/` | Quiz engine — service overview and setup | Technical overview for quiz-engine |
| `README.md` | `Repo/backend/services/rbac-service/` | RBAC service — service overview and setup | Technical overview for rbac-service |
| `README.md` | `Repo/backend/services/recommendation-service/` | Recommendation service — service overview and setup | Technical overview for recommendation-service |
| `README.md` | `Repo/backend/services/reporting-service/` | Reporting service — service overview and setup | Technical overview for reporting-service |
| `README.md` | `Repo/backend/services/scorm-service/` | SCORM service — service overview and setup | Technical overview for scorm-service |
| `README.md` | `Repo/backend/services/session-service/` | Session service — service overview and setup | Technical overview for session-service |
| `README.md` | `Repo/backend/services/skill-analytics-service/` | Skill analytics service — service overview and setup | Technical overview for skill-analytics-service |
| `README.md` | `Repo/backend/services/skill-inference-service/` | Skill inference service — service overview and setup | Technical overview for skill-inference-service |
| `README.md` | `Repo/backend/services/sso-service/` | SSO service — service overview and setup | Technical overview for sso-service |
| `README.md` | `Repo/backend/services/tenant-service/` | Tenant service — service overview and setup | Technical overview for tenant-service |
| `README.md` | `Repo/backend/services/user-service/` | User service — service overview and setup | Technical overview for user-service |
| `README.md` | `Repo/backend/services/webhook-service/` | Webhook service — service overview and setup | Technical overview for webhook-service |
| `README.md` | `Repo/backend/services/integration-service/` | Integration service — StatelessDecisionOrchestrator, B2P08 pattern, CGAP-078 | Technical overview for integration-service; gateway registration pending |
| `README.md` | `Repo/backend/services/payment-service/` | Payment service — Pakistan payment orchestration (JazzCash/Easypaisa) | Technical overview for payment-service; gateway registration pending |
| `README.md` | `Repo/backend/services/subscription-service/` | Subscription service — lifecycle state machine TRIAL→ACTIVE→GRACE→SUSPENDED→EXPIRED/CANCELLED, CGAP-080 | Technical overview for subscription-service; gateway registration pending |

---

### C2 — Migration Notes (6 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `MIGRATION_NOTES.md` | `Repo/backend/services/assessment-service/` | Assessment service migration notes | Documents migration strategy for assessment-service |
| `MIGRATION_NOTES.md` | `Repo/backend/services/cohort-service/` | Cohort service migration notes | Documents migration strategy for cohort-service |
| `MIGRATION_NOTES.md` | `Repo/backend/services/program-service/migrations/` | Program service migration notes | Documents migration strategy for program-service |
| `migration_notes.md` | `Repo/backend/services/progress-service/` | Progress service migration notes — dual-read, dual-write, event parity, cutover, cleanup | Migration from Rails monolith write paths to progress-service while preserving Progress semantics |
| `migration_notes.md` | `Repo/backend/services/session-service/docs/` | Session service migration notes — session backfill, API rollout, consumer migration | Introduces session_service as delivery-instance owner via staged rollout from legacy scheduling |
| `0002_user_service_projection_notes.md` | `Repo/backend/services/user-service/migrations/` | User service projection migration — backfill, dual-read, write cutover, event subscribers | Introduces dedicated User Service projection store while keeping Rails User model as source identity |

---

### C3 — Module READMEs (15 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `README.md` | `Repo/backend/services/cohort-service/modules/membership/` | Cohort membership module overview | Technical overview for cohort-service membership module |
| `README.md` | `Repo/backend/services/content-service/modules/metadata/` | Content metadata module overview | Technical overview for content-service metadata module |
| `README.md` | `Repo/backend/services/content-service/modules/storage/` | Content storage module overview | Technical overview for content-service storage module |
| `README.md` | `Repo/backend/services/course-service/events/` | Course service events module overview | Technical overview for course-service events module |
| `README.md` | `Repo/backend/services/course-service/modules/enrollment/` | Course enrollment module overview | Technical overview for course-service enrollment module |
| `README.md` | `Repo/backend/services/course-service/modules/versioning/` | Course versioning module overview | Technical overview for course-service versioning module |
| `README.md` | `Repo/backend/services/learning-path-service/events/` | Learning path events module overview | Technical overview for learning-path-service events module |
| `README.md` | `Repo/backend/services/learning-path-service/modules/assignment/` | Learning path assignment module overview | Technical overview for learning-path-service assignment module |
| `README.md` | `Repo/backend/services/learning-path-service/modules/rules/` | Learning path rules module overview | Technical overview for learning-path-service rules module |
| `README.md` | `Repo/backend/services/lesson-service/modules/content/` | Lesson content module overview | Technical overview for lesson-service content module |
| `README.md` | `Repo/backend/services/media-service/modules/media_pipeline/` | Media pipeline module overview | Technical overview for media-service media_pipeline module |
| `README.md` | `Repo/backend/services/media-service/modules/media_pipeline/events/` | Media pipeline events module overview | Technical overview for media-service media_pipeline events module |
| `README.md` | `Repo/backend/services/prerequisite-engine-service/modules/rules/` | Prerequisite rules module overview | Technical overview for prerequisite-engine-service rules module |
| `README.md` | `Repo/backend/services/progress-service/modules/aggregation/` | Progress aggregation module overview | Technical overview for progress-service aggregation module |
| `README.md` | `Repo/backend/services/scorm-service/modules/scorm_runtime/` | SCORM runtime module overview | Technical overview for scorm-service scorm_runtime module |

---

### C4 — QC Loop Reports (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `QC_LOOP.md` | `Repo/backend/services/hr-helpdesk-service/` | HR helpdesk service QC loop — multi-pass scoring, all categories 10/10 pass 2 | Records QC defect detection and correction for hr-helpdesk-service implementation |
| `QC_LOOP.md` | `Repo/backend/services/program-service/` | Program service QC loop — activation gate, endpoint shape, registry registration; all 10/10 pass 2 | Records QC defect detection and correction for program-service implementation |
| `qc_loop_report.md` | `Repo/backend/services/session-service/docs/` | Session service QC loop report — delivery model, boundary, API, event; all 10/10 pass 2 | Records QC defect detection and correction for session-service implementation |

---

### C5 — Service Rules & API Contracts (3 files)

| File | Location | Description | Purpose |
|---|---|---|---|
| `service_rules.md` | `Repo/backend/services/learning-path-service/` | Learning path service rules — creation, course sequencing, publishing workflows, tenant access policy | Authoritative behavioral rules for learning-path-service operations |
| `api_contract.md` | `Repo/backend/services/progress-service/src/` | Progress Service API Endpoints (v1) — upsert, complete, learner summary, course progress, path assignment | Service-internal REST endpoint contract for progress-service at base path /api/v1/progress |
| `api_contract.md` | `Repo/backend/services/skill-analytics-service/src/` | Skill Analytics API Contract (service-internal) — progression metrics, gap detection, mastery scoring, trends | Service-internal function contract for skill-analytics-service analytics operations |

---

## SECTION D — FRONTEND

| File | Location | Description | Purpose |
|---|---|---|---|
| `AGENTS.md` | `Repo/frontend/` | Frontend agent instructions — AI coding agent rules for frontend codebase | Governs AI-assisted development behaviour within the frontend layer |
| `CLAUDE.md` | `Repo/frontend/` | Claude Code context — frontend-specific Claude Code session instructions | Provides Claude Code with frontend context, conventions, and constraints |
| `README.md` | `Repo/frontend/` | Frontend README — overview, setup, and development guide | Technical overview and setup guide for the LMS frontend application |

---

## SECTION E — INFRASTRUCTURE

| File | Location | Description | Purpose |
|---|---|---|---|
| `README.md` | `Repo/infrastructure/api-gateway/` | API gateway README — overview and setup | Technical overview for the API gateway component |
| `verification.md` | `Repo/infrastructure/api-gateway/` | API gateway verification — 38-service exposure check, route matching, rate limiting QC (10/10) | Verifies all backend services registered in gateway with correct routes and rate limit policies |
| `README.md` | `Repo/infrastructure/event-bus/` | Event bus README — overview and setup | Technical overview for the event bus component |
| `README.md` | `Repo/infrastructure/load-testing/` | Load testing README — overview and setup | Technical overview for load testing infrastructure |
| `README.md` | `Repo/infrastructure/observability/` | Observability README — overview and setup | Technical overview for observability infrastructure |
| `README.md` | `Repo/infrastructure/secrets-management/` | Secrets management README — overview and setup | Technical overview for secrets management infrastructure |
| `README.md` | `Repo/infrastructure/service-discovery/` | Service discovery README — overview and setup | Technical overview for service discovery infrastructure |

---

## SECTION F — WORKSPACE ARCHIVE

| File | Location | Description | Purpose |
|---|---|---|---|
| `ARCHIVE-README.md` | `workspace/archive/` | Archive README — index of superseded docs and what each was absorbed into | Explains archive contents; icon-system-v1 absorbed into design-system §7, pattern-checklist superseded by Assembly Contracts |
| `icon-system-v1.md` | `workspace/archive/` | ARCHIVED 2026-05-13 — icon system v1, 8 icons, Tailwind mapping, SVG pattern | Superseded by 60-icon registry in design-system/design-system.md §7; retained for design history |
| `pattern-checklist.md` | `workspace/archive/` | ARCHIVED — pattern extraction checklist, pre-framework audit instrument | Superseded by Assembly Contracts in page-definitions/ui-framework.md §10; retained for history |

---

## Entry Counts

| Section | Group | .md |
|---|---|---|
| A | Ops Docs | 14 |
| B1 | Anchors | 5 |
| B2 | Macro Architecture ARCH_* | 8 |
| B3 | Architecture Audit | 6 |
| B4 | Platform Infrastructure B2P* | 8 |
| B5 | Commerce Domain B3P* | 8 |
| B6 | Operations Domain B5P* | 4 |
| B7 | AI & Intelligence B6P* | 5 |
| B8 | Domain Models + Normalization | 9 |
| B9 | Interface Contracts (active) | 10 |
| B9d | Interface Contracts (deprecated) | 4 |
| B10 | Domain Models | 9 |
| B11 | Cloud, Strategy, Service Map | 14 |
| B12 | Storage Design | 1 |
| B13 | Canonical Service Specs SPEC_* | 9 |
| B14 | AI Service Specs AI_* | 5 |
| B15 | Per-Service Specs | 31 |
| B15a | Feature Specs | 17 |
| B15b | Deprecated Specs | 5 |
| B16 | API Docs | 8 |
| B17 | Data Schemas | 13 |
| B18 | QC Reports | 28 |
| B19 | Integration Docs | 6 |
| B20 | Market Docs | 3 |
| B21 | Workspace Foundation | 3 |
| B22 | Design System | 3 |
| B23 | Page Definitions | 3 |
| B24 | Audit Docs | 3 |
| C1 | Backend Service READMEs | 45 |
| C2 | Backend Migration Notes | 6 |
| C3 | Backend Module READMEs | 15 |
| C4 | Backend QC Loops | 3 |
| C5 | Backend Service Rules + Contracts | 3 |
| D | Frontend | 3 |
| E | Infrastructure | 7 |
| F | Workspace Archive | 3 |
| **TOTAL** | | **327** |

---

**Phantom entries:** 0 — all 10 former phantoms now have placeholder stubs on disk (created 2026-05-26). Entries updated from PHANTOM to EMPTY. Content to be filled during normalisation sprint.
