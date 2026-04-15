# LMS PLATFORM — PENDING WORK REGISTER
**Repo:** LMS-main-V4h | **Last updated:** 2026-04-15
**Rule:** Items move from PENDING → COMPLETE when doc action is taken and progress.md + doc_catalogue.md are updated.

---

## ACTIVE WORK STREAM: UI FOUNDATION — PHASE 2

**Source:** design-system.md v2.1 §6 open issues + shadcn migration decision
**Phase 1:** ✓ COMPLETE 2026-04-15
**Phase 2:** PENDING — one item

| ID | Description | Notes |
|---|---|---|
| UI-P2-001 | §8 shadcn Integration — add to `design-system.md`: CSS var→shadcn CSS var mapping table, component coverage (Dialog/Sonner/Pagination/Breadcrumb/Sheet), visual override rules for brand alignment | Prerequisite for shadcn build start |

---

## DEFERRED: MARKET OVERLAY — PHASE F

**Source:** 3-doc overlay: Pakistan Market Research MASTER + Master Behavioral Spec + Master Product Spec
**Phases A–E:** ✓ COMPLETE 2026-04-14
**Phase F:** DEFERRED — long-term items requiring dedicated sprints or hardware dependencies

| ID | Description | Blocker / Reason |
|---|---|---|
| MO-041 | Urdu i18n — RTL rendering, Urdu string translations, font loading | Long-term i18n investment |
| MO-042 | Vocational service build — implement 6 CAP-VOCATIONAL-* capabilities as running service code | Capabilities seeded (MO-037); service build is a separate sprint |
| MO-043 | Teacher marketplace — discovery, rating, booking flow for Pakistan freelance tutor market | New domain; requires product design before build |
| MO-044 | Offline LMS-in-a-box — fully self-contained deployable for zero-connectivity environments | Hardware/deployment dependency; long-term roadmap item |

---

## COMPLETED WORK STREAMS — SUMMARY

| Work Stream | Completed | Items Resolved |
|---|---|---|
| BOS Overlay Gap Resolution | 2026-04-04 | 18 gaps (GAP-001–018) |
| Doc Normalisation Phases 0–8 | 2026-04-11 | 11 phases, ~60 docs created/updated |
| Code Gap Build Phase B (CGAP-001–083) | 2026-04-11 | 83 gaps across 14 service groups |
| MS Overlay Code Gap Build (CGAP-084–091) | 2026-04-12 | 8 MS contract gaps |
| Market Overlay Phases A–E (MO-001–040) | 2026-04-14 | 40 gaps — docs, infra, behavioral contracts, wiring, domain extensions |
| UI Foundation Phase 1 | 2026-04-15 | 4 docs — design-system v2.1, DL integrated, icon system (60 icons), behavior→UI v2.0 (32 rules) |

Full detail in `progress.md`. Code detail in `code_gap_register.md`.
