# AUTHORITY_MAPPING_MATRIX

Status: Active
Authority Level: High
Last Reviewed: 2026-06-22
Owner: AI

Purpose: For every information domain, identify the single authoritative document, its supporting documents, legacy documents, and retired documents. This matrix enforces the rule that no information domain may have multiple competing authorities.

---

## AUTHORITY TIER PRECEDENCE

When two documents conflict, the higher tier wins:

```
TIER 0  docs/00_authority/        — Platform governance (highest)
TIER 1  docs/anchors/             — Canonical implementation contracts
TIER 2  docs/specs/               — Per-service API contracts
        docs/contracts/           — Interface contracts
        docs/integrations/        — Integration contracts
TIER 3  docs/designs/             — Supporting design detail
        docs/architecture/        — Supporting architecture detail
        docs/data/                — Supporting data schemas
TIER 4  docs/qc/ + docs/08_reports/ — Generated reports (not authoritative for decisions)
TIER 5  workspace/sessions/ + _archive/ — Historical (never authoritative for decisions)
```

---

## DOMAIN 1: PROJECT IDENTITY AND PURPOSE

**Authority:** docs/00_authority/PROJECT_CHARTER.md

**What it owns:**
- Platform name and identity (Global Capability Platform)
- Pakistan-first positioning
- Architectural principles (8 canonical principles)
- Technology stack (69 HTTP services, 67 Python/FastAPI + 2 Node.js)
- Phase status
- Segment model (Academy, School, University, Enterprise, Vocational, Personal)

**Supporting:**
- docs/architecture/core-system-architecture.md (Rails heritage detail, layered architecture diagram)
- docs/architecture/platform-evolution-model.md (evolution roadmap)
- docs/designs/terminology-bridge.md (cross-generation terminology mapping)
- workspace/foundation/product-build-spec.md (HIST — former authority, now historical)

**Retired/Obsolete:**
- workspace/foundation/product-build-spec.md (superseded; HIST)
- docs/_archive/core_system_architecture.md (superseded; RETD)

**Conflict note:** docs/architecture/core-system-architecture.md contains a normalisation note acknowledging PROJECT_CHARTER.md supersedes it for identity. No unresolved conflict.

---

## DOMAIN 2: BOUNDED CONTEXTS AND DOMAIN MODEL

**Authority:** docs/00_authority/DOMAIN_MODEL.md

**What it owns:**
- 9 bounded contexts (Identity, Organization, Learning Structure, Learning Runtime, Assessment, Certification, Commerce, AI, Platform)
- Service-to-domain assignments for all 69 services
- Aggregate root definitions and ownership
- Config resolution hierarchy (4 levels: global → country → segment → tenant)
- Data ownership rules per domain

**Supporting:**
- docs/architecture/domain-driven-design-map.md (DDD tactical detail — may have older bounded context definitions; DOMAIN_MODEL.md takes precedence)
- docs/architecture/microservice-boundary-map.md (boundary detail)
- docs/architecture/service-data-ownership-rules.md (ownership detail)
- docs/designs/data-ownership-rules.md (ownership design — potential partial duplicate of service-data-ownership-rules.md)
- docs/data/core-lms-schema.md (Rails heritage entity schemas)
- docs/designs/tenant-extension-model.md (tenant fields that supply discriminator keys)
- docs/specs/capability-domain-map.md (capability-to-domain mapping)

**Retired/Obsolete:**
- docs/_archive/microservice_boundaries.md (superseded; RETD)
- workspace/sessions/U1/ENTITY_INVENTORY.md (HIST — pre-authority entity catalogue)

**Conflict note:** docs/architecture/domain-driven-design-map.md may contain older bounded context definitions. DOMAIN_MODEL.md is authoritative; any conflict resolves in DOMAIN_MODEL.md's favor.

---

## DOMAIN 3: FEATURE INVENTORY AND SCOPE

**Authority:** docs/00_authority/FEATURE_SCOPE.md

**What it owns:**
- Feature inventory organized by domain section (§1.1 through §1.11)
- Service-to-feature mapping
- Course-generation-service classification (AI domain, §1.10)
- Review-service classification (Learning Structure, §1.3)
- Features not yet scoped (TBD items)

**Supporting:**
- docs/specs/capability-inventory.md (capability-level inventory)
- docs/specs/capability-domain-map.md (capability-to-domain)
- docs/designs/product-capabilities-matrix.md (capabilities matrix)
- docs/designs/market-enforcements-capability-map.md (market-specific capabilities)
- workspace/sessions/U1/FEATURE_INVENTORY.md (HIST — pre-authority feature list)

**Retired/Obsolete:**
- docs/_archive/feature_inventory.md (superseded; RETD)

---

## DOMAIN 4: CORE PLATFORM WORKFLOWS

**Authority:** docs/00_authority/PRODUCT_WORKFLOWS.md

**What it owns:**
- WF-001 through WF-010 canonical workflow definitions
- Service orchestration per workflow
- Event definitions per workflow
- Workflow actors and triggers

**Supporting:**
- docs/designs/academy-operational-model.md (operational workflow context)
- docs/designs/academy-operations-domain.md (ops domain workflow detail)
- workspace/foundation/behavioral-spec.md (HIST — former workflow authority)
- workspace/sessions/U1/WORKFLOW_INVENTORY.md (HIST — pre-authority workflow list)

**Retired/Obsolete:**
- workspace/foundation/behavioral-spec.md (superseded; HIST)

---

## DOMAIN 5: CROSS-LAYER TRACEABILITY (FULL-STACK)

**Authority:** docs/00_authority/FULLSTACK_STITCHING_CONTRACT.md *(DRAFT — backend column complete, frontend column TBD)*

**What it owns:**
- FSC-001 through FSC-N: Per-contract traceability rows linking backend API → frontend component → shared type
- Backend API endpoints (confirmed for FSC-001: POST /api/v2/auth/sessions/login)
- Frontend bindings (currently TBD — Frontend Authority Capture not yet done)

**Supporting:**
- All docs/specs/*.md (backend API surface per service)
- All docs/contracts/*.md (interface contracts)
- docs/api/*.md (API surface documentation)

**Status:** Promotion from Draft → Active blocked pending Frontend Authority Capture.

---

## DOMAIN 6: ARCHITECTURAL DECISIONS

**Authority:** docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md

**What it owns:**
- 8 canonical architectural principles (same order as PROJECT_CHARTER.md §9)
- Decision 1: Python/FastAPI microservices
- Decision 2: Multi-tenant row-level isolation
- Decision 3: Config resolution (4 levels — GLOBAL, COUNTRY, SEGMENT, TENANT)
- Decision 4: Capability registry pattern
- Decision 5: JWT RS256 only (HS256 exceptions: legacy, test, internal services)
- Decision 6: Event envelope schema
- Decision 7: Two-layer architecture (Rails runtime + capability platform)
- Decision 8: Country factory pattern (Pakistan-first)
- ADR roadmap (R-001 through R-010+) in docs/08_reports/RECOMMENDED_ADR_ROADMAP.md

**Supporting:**
- docs/08_reports/RECOMMENDED_ADR_ROADMAP.md (future ADR topics)
- docs/architecture/api-versioning-strategy.md (AUTH — versioning decision detail)
- docs/architecture/security-architecture.md (RS256 implementation detail)
- workspace/sessions/U10/U10_LMS_ARCHITECTURE_DECISION_REPORT.md (HIST — decision forensic)

**Future ADRs needed:** R-001 through R-010+ per RECOMMENDED_ADR_ROADMAP.md. No ADR-002 exists yet.

---

## DOMAIN 7: AI SESSION GOVERNANCE

**Authority:** docs/07_governance/AI_OPERATING_CONTEXT.md

**What it owns:**
- Frozen decisions (FROZEN_DECISIONS table)
- Active blockers (GEB-001 through GEB-008)
- AI session rules (what AI may/may not do)
- Tech stack snapshot for AI context
- Escalation triggers

**Supporting:**
- docs/07_governance/DECISION_ESCALATION_MATRIX.md (escalation routing detail)
- docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md (GEB blocker detail)
- workspace/sessions/U11/U11_LMS_GOVERNANCE_ENTRY_BLOCKERS.md (HIST — original GEB identification)

---

## DOMAIN 8: ESCALATION AND DECISION ROUTING

**Authority:** docs/07_governance/DECISION_ESCALATION_MATRIX.md

**What it owns:**
- Decision categories and routing rules
- Which decisions AI may make autonomously
- Which decisions require owner approval
- Escalation paths and thresholds

---

## DOMAIN 9: EVENT CONTRACTS

**Authority:** docs/anchors/event-envelope.md

**What it owns:**
- Canonical 7-field event envelope schema (event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata)
- All event producers and consumers must implement this schema

**Supporting:**
- docs/architecture/event-driven-architecture.md (event bus design detail)
- docs/architecture/event-bus-design.md (event bus implementation)
- docs/architecture/event-consumer-infrastructure.md (consumer patterns)
- docs/architecture/event-domain-catalogue.md (event domain catalogue)
- docs/data/learning-event-schema.md (learning domain event schemas)
- infrastructure/event-bus/event_topics.json (canonical event topic registry — code)
- docs/integrations/auth-lifecycle-events.md (auth lifecycle events)

---

## DOMAIN 10: TENANT MODEL

**Authority:** docs/anchors/tenant-contract.md

**What it owns:**
- Canonical 6-field tenant payload (tenant_id, name, country_code, segment_type, plan_type, addon_flags)
- Cross-service tenant context propagation rules

**Supporting:**
- docs/architecture/multi-tenant-isolation-model.md (isolation detail)
- docs/architecture/tenant-isolation-strategy.md (isolation strategy)
- docs/architecture/tenant-customization-catalogue.md (customization options)
- docs/designs/tenant-extension-model.md (tenant extension fields)
- docs/00_authority/DOMAIN_MODEL.md §3 (tenant contract reference)

---

## DOMAIN 11: CAPABILITY AND CONFIG RESOLUTION

**Authority:** docs/anchors/capability-resolution.md *(PENDING UPDATE — see conflict note)*

**What it owns:**
- Canonical capability → config → entitlement → final_state resolution flow
- Config resolution hierarchy definition
- Capability, config, and entitlement term definitions

**Conflict note — CRITICAL:** capability-resolution.md currently documents:
`global → country → segment → plan → tenant → runtime_override (optional)` (6 levels)

The actual code (shared/models/config.py ConfigLevel enum, config-service/service.py) implements:
`global → country → segment → tenant` (4 levels, no PLAN, no runtime_override)

The governance documents (PROJECT_CHARTER.md, DOMAIN_MODEL.md, ADR-001, AI_OPERATING_CONTEXT.md, PRODUCT_WORKFLOWS.md) have all been corrected to 4 levels per remediation.

**Required action:** Update docs/anchors/capability-resolution.md to correct the config hierarchy to 4 levels. This requires owner approval (protected area).

**Supporting:**
- docs/contracts/config-resolution-interface-contract.md (config interface contract)
- docs/contracts/capability-interface-contract.md (capability interface)
- docs/contracts/entitlement-interface-contract.md (entitlement interface)
- docs/contracts/capability-gating-model.md (gating model)
- docs/designs/config-service-design.md (config service design)
- docs/designs/capability-registry-service-design.md (registry design)
- docs/designs/entitlement-service-design.md (entitlement design)

---

## DOMAIN 12: COUNTRY LAYER ARCHITECTURE

**Authority:** docs/anchors/country-layer-architecture.md

**What it owns:**
- Canonical adapter-binding pattern for country layer
- Distinction: adapter pattern (correct) vs. country branching (prohibited)
- Pakistan-first adapter binding

**Supporting:**
- docs/00_authority/PROJECT_CHARTER.md §5 (Pakistan-first principle)
- docs/00_authority/ADR-001 Decision 8 (country factory pattern)
- docs/designs/commerce-domain-architecture.md (Pakistan commerce adapter detail)

---

## DOMAIN 13: PER-SERVICE API CONTRACTS

**Authority:** One spec per service (docs/specs/*.md)

The authority for each service's API contract is its spec file. No two spec files should define the same service.

**Known naming misalignment (resolved):**
- Service name: `media-service`, Spec file: `docs/specs/media-pipeline-spec.md` — spec covers the service; naming mismatch documented in DOCUMENTATION_COVERAGE_MATRIX.md

**Retired v0 specs:**
- docs/specs/auth-service-spec-v0.md → superseded by auth-service-spec.md
- docs/specs/tenant-service-spec-v0.md → superseded by tenant-service-spec.md
- docs/specs/features/rbac-service-spec-v0.md → superseded by rbac-service-spec.md

**Duplicate spec:**
- docs/specs/GEN_14_certificate_service.md → duplicate of certificate-service-spec.md; retire

---

## DOMAIN 14: INTERFACE CONTRACTS

**Authority:** docs/contracts/*.md (one per interface type)

No competing authorities identified. All 11 interface contracts are the sole authority for their interface domain.

---

## DOMAIN 15: API VERSIONING

**Authority:** docs/architecture/api-versioning-strategy.md

No competing authority. This document is the sole authority on URI-based major versioning, deprecation policy, and parallel-version operation.

---

## DOMAIN 16: INTEGRATION SPECS (THIRD-PARTY)

**Authority:** docs/integrations/*.md (one per integration type)

| Integration | Authority Document |
|---|---|
| Auth lifecycle events | docs/integrations/auth-lifecycle-events.md |
| HRIS sync | docs/integrations/hris-sync-spec.md |
| LTI consumer | docs/integrations/lti-consumer-spec.md |
| LTI provider | docs/integrations/lti-provider-spec.md |
| Webhook system | docs/integrations/webhook-system-spec.md |
| Standards overview | docs/integrations/standards-support.md (SUPP, not AUTH) |

---

## DOMAIN 17: DATA SCHEMAS

**Authority:** docs/data/ (per schema type, no single authority for all data)

The only authority-level data doc is:
- docs/data/auth-service-storage-contract.md (storage contract for auth service)

All other data docs are Supporting References. No competing authorities within data/.

**Note:** docs/designs/data-ownership-rules.md and docs/architecture/service-data-ownership-rules.md overlap. See DUPLICATION_ANALYSIS_REPORT.md.

---

## DOMAIN 18: MARKET AND GO-TO-MARKET

**Authority:** docs/market/*.md (one per market topic)

| Topic | Authority |
|---|---|
| Competitive intelligence | docs/market/competitive-intelligence.md |
| GTM strategy | docs/market/gtm-entry-strategy.md |
| Pakistan pricing | docs/market/pakistan-market-pricing-guide.md |

No competing authorities.

---

## DOMAIN 19: SERVICE COVERAGE AND INVENTORY

**Authority:** docs/08_reports/DOCUMENTATION_COVERAGE_MATRIX.md

**What it owns:**
- Canonical count of 69 HTTP services (45 specced, 24 unspecced)
- Service-to-spec mapping
- Coverage percentage (65%)

**Supersedes:**
- docs/governance/doc-catalogue.md (OBSOL — v7.3 catalogue used pre-governance authority model)
- workspace/sessions/U2/DOC_CATALOGUE.md (HIST — pre-authority catalogue)
- docs/architecture/service-map.md (SUPP — may have older service names)

---

## DOMAIN 20: ARCHITECTURAL GAP REGISTER

**Authority:** docs/08_reports/ARCHITECTURAL_GAP_REGISTER.md

**What it owns:**
- GEB-001 through GEB-008 and other gap registrations
- Gap status tracking

**Supersedes:**
- workspace/ops/gap-register.md (OPS — pre-governance gap register; stale)
- workspace/ops/pending.md (OPS — stale pending register)

---

## DOMAIN 21: DOCUMENT PRECEDENCE RULES

**Conflict — AUTHORITY GAP:** docs/anchors/doc-precedence.md establishes BATCH > SPEC > ARCH > Legacy priority. However:

1. The BATCH naming convention (B2*, B3*, B5*, B6*) no longer exists in the repository. All BATCH docs have been reorganized into docs/specs/, docs/designs/, docs/architecture/.
2. The new docs/00_authority/ tier is not represented in this model at all.
3. The new tier model (TIER 0 through TIER 5 as defined in this document) supersedes the old BATCH > SPEC > ARCH > Legacy model.

**Required action:** Update docs/anchors/doc-precedence.md to reflect the new 5-tier authority model. Owner review required (anchor = protected area).

**Current authority (this document):** The TIER 0–5 model defined in the AUTHORITY_TIER_PRECEDENCE section above is the operative precedence model for this governance phase.

---

## DOMAIN 22: TEST STRATEGY

**Authority:** workspace/sessions/U9/TEST_SUITE_PLAN.md *(HIST — no active auth doc yet)*

An authority document for testing does not exist in docs/04_testing/ (that directory is empty). The test suite plan from U9 is Historical but is the most complete testing strategy document.

**Action needed:** Phase 3 Testing Authority Capture should produce an authoritative docs/04_testing/TEST_STRATEGY.md.

---

## DOMAIN 23: DEPLOYMENT

**No authority document exists.** docs/05_deployment/ is empty.

**Action needed:** Phase 3 Deployment Authority Capture should produce an authoritative docs/05_deployment/DEPLOYMENT_STRATEGY.md.

---

## DOMAINS WITHOUT AUTHORITY DOCUMENTS (GAPS)

| Domain | Gap | Action |
|---|---|---|
| Frontend architecture | No authority doc; workspace/design-system/ is pre-phase Draft | Frontend Authority Capture (Phase 2) |
| Deployment strategy | docs/05_deployment/ empty | Deployment Authority Capture (Phase 3) |
| Test strategy (active) | docs/04_testing/ empty | Testing Authority Capture (Phase 3) |
| interaction-layer-service feature scope | Not in FEATURE_SCOPE.md | Phase 2 R-008 spec work |
| Document precedence | doc-precedence.md is OBSOL | Update anchor (owner approval required) |
| Capability resolution (4 levels) | capability-resolution.md not yet updated | Owner update required (protected anchor) |

---

## AUTHORITY MAP SUMMARY

| Domain | Authority Document | Status |
|---|---|---|
| Project Identity | PROJECT_CHARTER.md | Active |
| Domain Model | DOMAIN_MODEL.md | Active |
| Feature Scope | FEATURE_SCOPE.md | Active |
| Core Workflows | PRODUCT_WORKFLOWS.md | Active |
| Full-stack Traceability | FULLSTACK_STITCHING_CONTRACT.md | Draft |
| Architectural Decisions | ADR-001_PROJECT_FOUNDATION.md | Active |
| AI Governance | AI_OPERATING_CONTEXT.md | Active |
| Escalation Rules | DECISION_ESCALATION_MATRIX.md | Active |
| Event Contracts | anchors/event-envelope.md | Active |
| Tenant Model | anchors/tenant-contract.md | Active |
| Capability + Config Resolution | anchors/capability-resolution.md | Active (PENDING 4-level fix) |
| Country Layer | anchors/country-layer-architecture.md | Active |
| Document Precedence | anchors/doc-precedence.md | OBSOLETE (needs update) |
| Per-service API Contracts | docs/specs/*.md (per service) | Active (53 services) |
| Interface Contracts | docs/contracts/*.md | Active (11 contracts) |
| Integration Specs | docs/integrations/*.md | Active (5 specs) |
| API Versioning | architecture/api-versioning-strategy.md | Active |
| Market / GTM | docs/market/*.md | Active |
| Service Coverage | DOCUMENTATION_COVERAGE_MATRIX.md | Active |
| Architectural Gap Register | ARCHITECTURAL_GAP_REGISTER.md | Active |
| Test Strategy | (none active — U9 plan is HIST) | GAP |
| Deployment | (none — docs/05_deployment/ empty) | GAP |
| Frontend | (none — docs/02_frontend/ empty) | GAP |
