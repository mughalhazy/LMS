# LMS PLATFORM — MASTER SPEC OVERLAY GAP REGISTER
**Started:** 2026-04-11 | **Source:** `LMS PLATFORM — MASTER PRODUCT & BUILD SPEC.md`
**Rule:** Additive only — each gap adds a named MS-* contract to the relevant doc. No content deleted.
**Scope:** Doc overlay only. Code gaps identified here move to `code_gap_register.md` after doc work is complete.

---

## LEGEND
- **Type:** MISSING = no contract exists | PARTIAL = rule referenced but not named/enforced
- **Priority:** HIGH = core architectural rule | MEDIUM = platform principle | LOW = quality/scale rule
- **Status:** OPEN | RESOLVED

---

## WHY THIS REGISTER EXISTS

The BOS overlay (see `gap_register.md`) captured behavioral contracts — how the platform *acts* toward
operators, learners, and automations. The Master Spec overlay captures architectural contracts — what
the platform *is*, what it must *never become*, and what every new component must conform to.

The Master Spec was used as ground truth during Phase A/B code gap auditing, but its rules were never
formally written into the service/architecture docs as named, enforceable contracts. This register
closes that gap.

---

## GAP REGISTER

### §2 — CAPABILITY MODEL

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-001 | §2.2 | HIGH | MISSING | No formal **Capability Definition Completeness Contract**. MS§2.2 requires every capability to define: unique key, domain, dependencies, usage metrics, billing type, required adapters. B2P05 describes the registry structure but never states this as an enforced rule that all capability registrations must satisfy. | `docs/specs/capability_registry_service_spec.md` + `docs/architecture/B2P05_capability_registry_service_design.md` | RESOLVED 2026-04-11 |
| MSG-002 | §2.3 | HIGH | MISSING | No formal **Capability Validity Rule**. MS§2.3 states: if something cannot be independently enabled/disabled, cannot be measured, and cannot be reused — it is NOT a valid capability. This is a gatekeeping rule that prevents non-capability constructs entering the registry. Not stated in any spec. | `docs/specs/capability_registry_service_spec.md` | RESOLVED 2026-04-11 |

### §3 — CONFIG-DRIVEN BEHAVIOR

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-003 | §3.2 | HIGH | MISSING | No formal **No Runtime Branching Contract**. MS§3.2 states: no runtime branching inside services, no hardcoded workflows, deterministic behavior. The normalisation notes on individual docs say "not a segment-forked product" but there is no named, enforceable contract that ALL services must follow: behavioral variation must come only from config resolution output, never from inline conditionals on segment/country/plan. | `docs/architecture/B2P01_config_service_design.md` + `docs/anchors/capability_resolution.md` | RESOLVED 2026-04-11 |

### §4 — ADAPTER LAYER

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-004 | §4 | HIGH | MISSING | No formal **Adapter Isolation Contract**. MS§4 rules: (a) all external dependencies must use adapters; (b) adapters live in `/integrations`; (c) core services must never contain provider logic; (d) adapters must be swappable without core changes. `adapter_inventory.md` lists adapters but never states these as enforced rules that ALL services must comply with. | `docs/specs/adapter_inventory.md` + `docs/architecture/payment_provider_adapter_interface_contract.md` + `docs/architecture/communication_adapter_interface_contract.md` | RESOLVED 2026-04-11 |

### §6 — SYSTEM OF RECORD

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-005 | §6 | HIGH | MISSING | No formal **SoR State Authority Contract**. MS§6 rules: system must maintain a single source of truth; no duplication of core state across services. `SOR_01_system_of_record_design.md` defines the SoR service but never states this as a named, enforceable boundary rule: no service may hold a durable copy of student lifecycle state, financial ledger state, or unified profile state that it did not originate. | `docs/architecture/SOR_01_system_of_record_design.md` | RESOLVED 2026-04-11 |

### §7 — MARKET ENFORCEMENTS

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-006 | §7 | MEDIUM | PARTIAL | No formal **Market Enforcement as Capabilities Contract**. MS§7 lists 7 market requirements (mobile-first, low-tech operators, async interaction, unreliable connectivity, instant payment activation, content protection, operational automation) and explicitly states these must be implemented as capabilities — not as country logic. `DOC_NORM_02` maps them to capability keys but never states the enforcement rule: these requirements are non-negotiable, must be fully satisfiable via capability activation alone, and must never require a country-specific fork to deliver. | `docs/architecture/DOC_NORM_02_market_enforcements_capability_map.md` | RESOLVED 2026-04-11 |

### §8 — USER EXPERIENCE PRINCIPLES

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-007 | §8 | MEDIUM | MISSING | No formal **Mobile-First UX Contract**. MS§8 lists mobile-first as a non-negotiable UX principle. No spec defines what this means as an enforceable rule: all primary user journeys (learner, operator, instructor) must be fully functional on mobile-class devices without feature degradation. Dashboard-equivalent functionality must be available via mobile-native interaction patterns. | `docs/specs/platform_behavioral_contract.md` | RESOLVED 2026-04-11 |
| MSG-008 | §8 | MEDIUM | MISSING | No formal **Outcome-Driven UX Contract**. MS§8 lists outcome-driven as a UX principle. No spec defines this as a rule: every data surface must answer "what should I do next?" — raw data without a suggested action or outcome framing violates this principle. Complements BC-ANALYTICS-01 (insight over reports) but applies to ALL surfaces, not just analytics. | `docs/specs/platform_behavioral_contract.md` | RESOLVED 2026-04-11 |

### §9 — MONETIZATION MODEL

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-009 | §9 | MEDIUM | PARTIAL | No formal **Free Entry + Capability Upgrade Contract**. MS§9 states: free entry must be possible, upgrades are capability-based, revenue scales with capability usage. `DOC_07` describes billing tiers but never states this as a named rule: the platform must always have a zero-cost entry point, no capability may be gated by geography, and all commercial growth paths must flow through capability activation — not plan reassignment or geography unlock. | `docs/specs/DOC_07_billing_and_usage_model.md` | RESOLVED 2026-04-11 |

### §10 — STRATEGIC INSIGHTS

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-010 | §10.5 | MEDIUM | MISSING | No formal **Content Protection Enforcement Contract**. MS§10 rule 5: "Content protection must be enforced." `media_security_spec.md` defines the mechanism (DRM, watermark, session control, anti-piracy) but never states the enforcement contract: all monetized/paid content must have protection active by default; content protection is opt-out only for explicitly declared public content; no paid content may be delivered without a protection session token. | `docs/specs/media_security_spec.md` | RESOLVED 2026-04-11 |
| MSG-011 | §10.8 | MEDIUM | MISSING | No formal **AI Assist Boundary Contract**. MS§10 rule 8: "AI must assist, not replace." No spec defines this as a named rule: AI-generated outputs must be clearly labeled as AI-assisted; human review must always be available; AI must surface a human action path (dismiss, correct, override); AI must not make irreversible decisions autonomously. Distinguishes AI *assist* (present in platform) from AI *replace* (prohibited). | `docs/architecture/B6P01_ai_tutor_assist_capability_design.md` | RESOLVED 2026-04-11 |
| MSG-012 | §10.6 | LOW | MISSING | No formal **Automation Coverage Contract**. MS§10 rule 6: "System must reduce manual work." No spec names this as an enforced rule: every repeatable operational action type (attendance, fee collection, enrollment confirmation, compliance tracking) must have a corresponding automation path available. Manual-only workflows for automatable operations are a platform deficiency, not a feature. | `docs/specs/operations_os_spec.md` | RESOLVED 2026-04-11 |
| MSG-013 | §10.7 | LOW | MISSING | No formal **Simplicity Preservation Contract**. MS§10 rule 7: "Simplicity must be preserved." No spec captures this as a rule: new capabilities must not increase operator cognitive load without explicit justification; the default tenant experience must be navigable without training; configurability must be hidden behind sensible defaults. | `docs/specs/platform_behavioral_contract.md` | RESOLVED 2026-04-11 |

### §13 — FINAL SUCCESS CRITERIA

| ID | MS§ | Priority | Type | Gap Description | Target Doc(s) | Status |
|---|---|---|---|---|---|---|
| MSG-014 | §13 | MEDIUM | MISSING | No formal **Global Scalability Contract**. MS§13 success criterion 9: "system scales globally without modification." No architecture doc states this as a named rule: the core platform must never require code changes to support a new country or market; all market-specific requirements must be satisfied via adapter substitution and config layer values alone; any change requiring a core code change to support a new geography is a platform defect. | `docs/architecture/ARCH_01_core_system_architecture.md` | RESOLVED 2026-04-11 |

---

## SUMMARY

| Section | Gaps | Status |
|---|---|---|
| §2 Capability Model | 2 (MSG-001, MSG-002) | ✓ RESOLVED |
| §3 Config-Driven Behavior | 1 (MSG-003) | ✓ RESOLVED |
| §4 Adapter Layer | 1 (MSG-004) | ✓ RESOLVED |
| §6 System of Record | 1 (MSG-005) | ✓ RESOLVED |
| §7 Market Enforcements | 1 (MSG-006) | ✓ RESOLVED |
| §8 UX Principles | 2 (MSG-007, MSG-008) | ✓ RESOLVED |
| §9 Monetization | 1 (MSG-009) | ✓ RESOLVED |
| §10 Strategic Insights | 4 (MSG-010–013) | ✓ RESOLVED |
| §13 Success Criteria | 1 (MSG-014) | ✓ RESOLVED |
| **Total** | **14** | **✓ ALL RESOLVED 2026-04-11** |

---

## ALREADY COVERED (by BOS overlay — not re-opened here)

| MS§ | BOS Contract | Doc |
|---|---|---|
| §5.9 / §6.1 | BC-INT-01 (action inside message) | `interaction_layer_spec.md` |
| §5.9 / §2.3 | BC-INT-02 (conversational-first) | `interaction_layer_spec.md` |
| §5.8 | BC-WF-01 (default-on automation) | `workflow_engine_spec.md` |
| §5.10 | BC-OPS-01–04 (proactive ops OS) | `operations_os_spec.md` |
| §5.12 / §7.2 | BC-OFFLINE-01 (operational offline) | `offline_sync_spec.md` |
| §5.17 | BC-ONBOARD-01 (smart defaults) | `onboarding_spec.md` |
| §5.16 | BC-ANALYTICS-01–02 (insights over reports) | `analytics_service_spec.md` |
| §5.4 / §8.2 | BC-BILLING-01 (contextual upsell) | `DOC_07_billing_and_usage_model.md` |
| §10.2 | BC-REV-01 (revenue risk surfacing) | `B3P06_revenue_service_design.md` |
| §5.18 | BC-GATE-01 (capability gate UX) | `capability_gating_model.md` |
| §6.2 | BC-COMMS-01 (multi-channel parity) | `communication_adapter_interface_contract.md` |
| §9.1 | BC-RISK-01 (learner progress push) | `B6P04_learner_risk_insights_system_design.md` |
| §5.15 | BC-ECON-01 (insight-to-action economics) | `system_economics_spec.md` |
