# LMS PLATFORM — DOC NORMALISATION PROGRESS TRACKER
**Repo:** LMS-main-V4h | **Last updated:** 2026-04-15

---

## CURRENT STATUS

| Work Stream | Gaps / Items | Resolved | Deferred | Status |
|---|---|---|---|---|
| BOS Overlay (GAP-001–018) | 18 | 18 | 0 | ✓ COMPLETE 2026-04-04 |
| Doc Normalisation (Phases 0–8) | 11 phases | 11 | 0 | ✓ COMPLETE 2026-04-11 |
| Code Gap Build (CGAP-001–083) | 83 | 83 | 0 | ✓ COMPLETE 2026-04-11 |
| MS Overlay Code Gaps (CGAP-084–091) | 8 | 8 | 0 | ✓ COMPLETE 2026-04-12 |
| Market Overlay — Phase A (MO-001–021) | 21 | 21 | 0 | ✓ COMPLETE 2026-04-14 |
| Market Overlay — Phase B (MO-022–024) | 3 | 3 | 0 | ✓ COMPLETE 2026-04-14 |
| Market Overlay — Phase C (MO-025–031) | 7 | 7 | 0 | ✓ COMPLETE 2026-04-14 |
| Market Overlay — Phase D (MO-032–035) | 4 | 4 | 0 | ✓ COMPLETE 2026-04-14 |
| Market Overlay — Phase E (MO-036–040) | 5 | 5 | 0 | ✓ COMPLETE 2026-04-14 |
| Market Overlay — Phase F (MO-041–044) | 4 | 0 | 4 | DEFERRED |
| UI Foundation — Phase 1 (design system + DL + icon + behavior→UI) | 4 docs | 4 | 0 | ✓ COMPLETE 2026-04-15 |
| UI Foundation — Phase 2 (shadcn integration layer) | 1 item | 0 | 0 | PENDING |

**Total gaps identified:** 153 (18 BOS + 83+8 code + 44 market overlay)
**Total resolved:** 149 | **Total deferred:** 4

---

## ACTIVE: MARKET OVERLAY — PHASE F (DEFERRED)

| ID | Description | Reason Deferred |
|---|---|---|
| MO-041 | Urdu i18n — RTL rendering, string translations, font loading | Long-term i18n investment; no immediate blocker |
| MO-042 | Vocational service build — implement 6 CAP-VOCATIONAL-* capabilities as running code | Capabilities seeded in config (MO-037); service build is a separate sprint |
| MO-043 | Teacher marketplace — discovery, rating, booking for Pakistan freelance tutor market | New domain; requires product design before build |
| MO-044 | Offline LMS-in-a-box — fully self-contained deployable for zero-connectivity environments | Hardware/deployment dependency; long-term roadmap item |

---

## RESOLVED PHASES — COMPACT SUMMARY

### Doc Normalisation (Phases 0–8)

| Phase | Scope | Outcome |
|---|---|---|
| 0 | Infrastructure | `doc_catalogue.md`, `progress.md` created |
| 1 | Master Spec updates | 6 new sections in MASTER PRODUCT & BUILD SPEC (§0.1, §1.5, §3.1, §5.9, §5.19, §5 ref) |
| 2 | Deprecation banners | 10 lower-priority docs pointed to canonical equivalents |
| 3 | Framing/terminology | Normalisation notes added to 11 existing docs (additive, no deletions) |
| 4 | Core system new docs | 6 new docs: terminology bridge, market enforcements map, domain extension model, SoR design, adapter inventory, capability domain map |
| 5 | Capability domain specs | 7 new specs for MS§5 domains (financial ledger, interaction layer, ops OS, performance, economic, system economics, onboarding) |
| 6 | Service specs | 9 new specs for undocumented services |
| 7 | Architecture docs | B3P06, B3P07, B3P08 revenue + financial architecture |
| 8 | MS Overlay doc contracts | 14 MS§ contracts (MSG-001–014) written into target docs |

### BOS Overlay (GAP-001–018)
All 18 gaps resolved 2026-04-04 across 12 doc groups (G01–G12). Behavioral contracts for: automation default-on, operator posture, proactive push, daily action list, zero-dashboard, in-message actions, channel parity, offline operations, smart defaults, learner push, insights-over-reports, upsell, revenue risk, capability gate UX, conversational-first.

### Code Gap Build (CGAP-001–091)
- **CGAP-001–083** (83 gaps): Resolved 2026-04-05–2026-04-11 across tiers T1–T6-H. Covered: workflow engine, operations OS, event ingestion, notification, integration, analytics, capability registry, commerce, subscription, entitlement, offline sync, onboarding, config service, identity stack, learning record, content/assessment, backend services.
- **CGAP-084–091** (8 MS overlay gaps): Resolved 2026-04-11–2026-04-12. Covered: MS-CAP-01/02 validation, MS-CONFIG-01 no-runtime-branching, MS-ADAPTER-01 isolation, MS-SOR-01 state authority, MS-CONTENT-01 content protection, MS-AI-01 boundary, MS-REDUCE-01 automation coverage.

### Market Overlay (MO-001–040)
- **Phase A** (MO-001–021): 14 BC-* behavioral contracts + table/references updates to `platform_behavioral_contract.md`; 6 new market/domain docs; performance spec update.
- **Phase B** (MO-022–024): Storage adapter built (`integrations/storage/`); file-storage + media-pipeline services completed (§5.11/§5.12).
- **Phase C** (MO-025–031): 7 behavioral contract implementations — exam checkpointing, branch RBAC scope, free-tier capability bundle, payment→entitlement activation, revenue signal ingestion, at-risk learner trigger, business impact language validation.
- **Phase D** (MO-032–035): 4 cross-service wiring completions — learner intervention workflow, entitlement activation consumer, onboarding free-tier wire-up, revenue signal forwarding pipeline.
- **Phase E** (MO-036–040): 5 domain extensions — multi-branch analytics, vocational segment defaults, Pakistan fee defaults, offline manifest registration, exam performance InsightEnvelope.

### UI Foundation (Phase 1 — COMPLETE 2026-04-15)
- **design-system.md v2.1** (`UI/design-system.md`): Pattern-extracted from 52 built pages, integrated with lms-design-language.html v1.4, extended with §7 Icon System (60-icon registry, token mapping, SVG inline pattern). §6 issue #1 closed.
- **Design Language integrated** (`UI/lms-design-language.html`): 4-state color rule, surface density, motion language, primary=ink correction absorbed into design system.
- **Icon System integrated** (`UI/-- ICON_SYSTEM_LAYER--v1.md`): 8→60 semantic icons, Tailwind→CSS var mapping, SVG inline pattern for HTML pages, hard rules enforced.
- **Behavior→UI doc v2.0** (`UI/_BEHAVIOR → UI IMPLEMENTATION_.md`): 15→32 rules, full coverage of Master Behavioral Spec §1–§16. 18 new rules added, 4 existing rules deepened, §32 Copy Rules added.

### UI Foundation (Phase 2 — PENDING)
- **§8 shadcn Integration** to be added to `design-system.md`: CSS var → shadcn CSS var mapping, component coverage table (Dialog/Sonner/Pagination/Breadcrumb/Sheet), visual override rules.
