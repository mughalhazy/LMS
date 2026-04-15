# LMS PLATFORM — GAP REGISTER
**Repo:** LMS-main-V4h | **Last updated:** 2026-04-14

---

## BOS OVERLAY GAPS (GAP-001–018) — RESOLVED

All 18 gaps resolved 2026-04-04. Source: `LMS PLATFORM — BEHAVIORAL OPERATING SPEC.md`. Covered behavioral contracts for: automation default-on (§3.1), operator posture (§1), conversational-first (§2.3), proactive pattern push (§4.1), three-tier action model (§4.2), daily action list (§5.1), zero-dashboard (§5.2), in-message actions (§6.1), multi-channel parity (§6.2), offline operations (§7.2), contextual upsell (§8.2), learner progress push (§9.1), revenue risk surfacing (§10.1), insight-to-action economics (§10.2), smart defaults (§12.2), insights-over-reports (§13.1), comparative context mandatory (§13.2), capability gate UX (§1.1). Full detail archived in session transcript.

---

## MARKET OVERLAY GAPS (MO-001–044)

**Source:** 3-doc overlay: Pakistan Market Research MASTER + Master Behavioral Spec + Master Product Spec
**Identified:** 2026-04-13 | **Total:** 44 | **Resolved:** 40 | **Deferred:** 4

### Resolved — MO-001 to MO-040

| ID Range | Phase | Scope | Resolved |
|---|---|---|---|
| MO-001–014 | A1 | 12 BC-* behavioral contracts + table/references updates → `platform_behavioral_contract.md` | 2026-04-14 |
| MO-015–021 | A2 | 6 new docs (vocational spec, free tier def, multi-branch RBAC, PK pricing guide, GTM strategy, competitive intel) + performance spec update | 2026-04-14 |
| MO-022–024 | B | Storage adapter (`integrations/storage/`), file-storage service (§5.11), media-pipeline service (§5.12) | 2026-04-14 |
| MO-025 | C | BC-EXAM-01: `submit_answer()`, `get_session_answers()`, `resume_exam_session()` — exam-engine | 2026-04-14 |
| MO-026 | C | BC-BRANCH-01: `ScopeType.BRANCH`, `branch_ids` field, `require_branch_access()`, `get_effective_branch_ids()` — RBAC service | 2026-04-14 |
| MO-027 | C | BC-FREE-01: `register_free_tier_capability_bundle()` — 4 quota-capped caps — capability-registry | 2026-04-14 |
| MO-028 | C | BC-PAY-01: `activate_entitlement_on_payment()` wired in `handle_provider_callback()` — payment-service | 2026-04-14 |
| MO-029 | C | BC-ECON-01: `receive_revenue_signal()` + `generate_revenue_action_items()` — operations-os | 2026-04-14 |
| MO-030 | C | BC-LEARN-01: `trigger_at_risk_interventions()` emitting `workflow.trigger.learner_intervention` — analytics-service | 2026-04-14 |
| MO-031 | C | BC-LANG-01: `business_impact_description` on `Capability`; MS-CAP-01 enforces non-empty for monetizable — shared models + capability-registry | 2026-04-14 |
| MO-032 | D | BC-LEARN-01: `wf_default_learner_intervention` workflow consuming MO-030 event — workflow-engine | 2026-04-14 |
| MO-033 | D | BC-PAY-01: `activate_from_payment()` consuming MO-028's `entitlement.activated` — entitlement-service | 2026-04-14 |
| MO-034 | D | BC-FREE-01: free-tier bundle wired into `bootstrap_default_capabilities()` for free-plan tenants — onboarding | 2026-04-14 |
| MO-035 | D | BC-ECON-01: `RevenueSignalForwarder` routing B3P07 revenue events to MO-029 — event-ingestion pipeline | 2026-04-14 |
| MO-036 | E | BC-BRANCH-01: `record_branch_snapshot()` + `cross_branch_analytics()` InsightEnvelope — analytics-service | 2026-04-14 |
| MO-037 | E | Vocational segment: 9 base + 6 CAP-VOCATIONAL-* caps seeded in `platform_defaults.py` | 2026-04-14 |
| MO-038 | E | Pakistan fee defaults (`_COUNTRY_FEE_DEFAULTS["PK"]`) seeded at COUNTRY layer — config-service | 2026-04-14 |
| MO-039 | E | BC-FAIL-01: `register_offline_manifest()` + `receive_pipeline_event()` closing media-pipeline→offline-sync chain | 2026-04-14 |
| MO-040 | E | `ingest_exam_result()` + `exam_performance_insight()` BC-ANALYTICS-01/02 InsightEnvelope — analytics-service | 2026-04-14 |

---

### Deferred — MO-041 to MO-044

| ID | Phase | Gap Description | Reason Deferred |
|---|---|---|---|
| MO-041 | F | **Urdu i18n support** — RTL rendering, Urdu string translations, font loading across platform UI | Long-term i18n investment; no immediate market blocker |
| MO-042 | F | **Vocational service build** — implement the 6 CAP-VOCATIONAL-* capabilities (practicum tracking, competency-based progression, industry certifications, placement, employer portal, skills inventory) as running service code | Capabilities seeded in config (MO-037); actual service build is a separate sprint |
| MO-043 | F | **Teacher marketplace** — discovery, rating, booking flow for Pakistan freelance tutor market | New domain requiring product design + UX before implementation |
| MO-044 | F | **Offline LMS-in-a-box** — fully self-contained deployable package for zero-connectivity environments (Raspberry Pi / local server) | Hardware and deployment dependency; long-term roadmap item |
