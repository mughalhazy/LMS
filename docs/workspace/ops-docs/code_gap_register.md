# LMS PLATFORM — CODE GAP REGISTER
**Repo:** LMS-main-V4h | **Last updated:** 2026-04-14
**Rule:** Additive only — gaps logged as found. Resolved when implementation complete.

---

## SUMMARY

| Batch | Source | Count | Status |
|---|---|---|---|
| CGAP-001–083 | Spec/arch overlay onto service code | 83 | ✓ ALL RESOLVED 2026-04-11 |
| CGAP-084–091 | MS Overlay code audit | 8 | ✓ ALL RESOLVED 2026-04-12 |
| MO-025–031 | Market Overlay Phase C (independent) | 7 | ✓ ALL RESOLVED 2026-04-14 |
| MO-032–035 | Market Overlay Phase D (dependent wiring) | 4 | ✓ ALL RESOLVED 2026-04-14 |
| MO-036–040 | Market Overlay Phase E (domain extensions) | 5 | ✓ ALL RESOLVED 2026-04-14 |
| MO-041–044 | Market Overlay Phase F | 4 | DEFERRED |

**Total code gaps:** 111 | **Resolved:** 107 | **Deferred:** 4

---

## CGAP-001–083 — RESOLVED (compact)

83 gaps resolved 2026-04-05–2026-04-11 across tiers T1–T6-H. Service groups covered:

| Group | Services | Gaps |
|---|---|---|
| CG01 | workflow-engine, operations-os, event-ingestion | 20 |
| CG02 | notification-service, integration-service, notification-be, webhook-be | 8 |
| CG03 | analytics-service, capability-registry, reporting-be | 8 |
| CG04 | commerce, subscription-service, entitlement-service | 7 |
| CG05 | offline-sync, onboarding, config-service | 5 |
| CG06 | academy-ops, enterprise-control, system-of-record, auth-be, enrollment-be | 7 |
| CG07 | media-security, exam-engine + backend core services | 7 |
| CG08 | content-be, course-be, lesson-be, learning-path-be | 3 |
| CG09 | assessment-be, session-be, scorm-be, attempt-be | 2 |
| CG10 | rbac-be, sso-be, tenant-be, user-be | 2 |
| CG11 | hris-sync-be, lti-be, payment-be | 2 |
| CG12 | recommendation-be | 1 |
| CG13 | push-be, email-be, badge-be, hr-helpdesk-be, group-be, department-be | 2 |
| CG14 | integrations/payments, shared/ | 2 |

Tier breakdown: T1 (chain-breaking root causes), T2 (default workflows + BC), T3-A/B/C/D (NotImplementedError), T4-A/B/C/D/E (storage), T5-A/B/C/D/E (behavioral intelligence), T6-A/B/C/D/E/F/G/H (completeness). Full detail archived in session transcript.

---

## CGAP-084–091 — MS OVERLAY — RESOLVED (compact)

8 gaps resolved 2026-04-11–2026-04-12 from `ms_overlay_gap_register.md` audit:

| ID | Contract | Service | Status |
|---|---|---|---|
| CGAP-084 | MS-CAP-01 (capability definition completeness validation) | `services/capability-registry/service.py` | ✓ RESOLVED 2026-04-11 |
| CGAP-085 | MS-CAP-02 (capability validity rule — no orphan keys) | `services/capability-registry/service.py` | ✓ RESOLVED 2026-04-11 |
| CGAP-086 | MS-CONFIG-01 (no runtime country/segment branching) | `services/config-service/service.py` | ✓ RESOLVED 2026-04-12 |
| CGAP-087 | MS-ADAPTER-01 (all external I/O through adapter interfaces) | `integrations/` boundary enforcement | ✓ RESOLVED 2026-04-12 |
| CGAP-088 | MS-SOR-01 (SoR is sole state authority) | `services/system-of-record/service.py` | ✓ RESOLVED 2026-04-12 |
| CGAP-089 | MS-CONTENT-01 (paid content protection default-on) | `services/media-security/service.py` | ✓ RESOLVED 2026-04-12 |
| CGAP-090 | MS-AI-01 (AI assist stays within capability boundary) | `services/ai-tutor/service.py` | ✓ RESOLVED 2026-04-12 |
| CGAP-091 | MS-REDUCE-01 (automation coverage target enforced) | `services/operations-os/service.py` | ✓ RESOLVED 2026-04-12 |

---

## MARKET OVERLAY — PHASES C–E — RESOLVED

### Phase C — Independent (MO-025–031)

| ID | BC Contract | Service | What was built |
|---|---|---|---|
| MO-025 | BC-EXAM-01 | `services/exam-engine/service.py` | `submit_answer()` — checkpoints every answer, emits `exam.answer.checkpointed`. `get_session_answers()` — returns all checkpointed answers. `resume_exam_session()` — restores full state + answers on reconnect, emits `exam.session.resumed`. |
| MO-026 | BC-BRANCH-01 | `backend/services/rbac-service/app/models.py`, `app/service.py` | `ScopeType.BRANCH` added. `branch_ids: list[str] \| None` on `SubjectRoleAssignment`. `get_effective_branch_ids()` — None=HQ, list=branch-restricted. `require_branch_access()` — raises 403 if not in scope. |
| MO-027 | BC-FREE-01 | `services/capability-registry/service.py` | `register_free_tier_capability_bundle()` — 4 quota-capped caps: CAP-ENROLL-FREE (50 students), CAP-PAYMENT-FREE (unlimited), CAP-WHATSAPP-FREE (100/mo), CAP-DAILY-ACTION-LIST-FREE. Each with `business_impact_description`. |
| MO-028 | BC-PAY-01 | `backend/services/payment-service/service.py` | `activate_entitlement_on_payment()` — emits `entitlement.activated` synchronously on `payment.verified`. Wired into `handle_provider_callback()`. Same request cycle — no queue delay. |
| MO-029 | BC-ECON-01 | `services/operations-os/service.py` | `receive_revenue_signal()` + `generate_revenue_action_items()` — ingests installment_overdue/subscription_lapsing/churn_risk/payment_failed into Daily Action List. CRITICAL if overdue ≥14 days. |
| MO-030 | BC-LEARN-01 | `services/analytics-service/service.py` | `trigger_at_risk_interventions()` — wraps `at_risk_learner_signals()`, emits `workflow.trigger.learner_intervention` per at-risk learner with risk_level/completion_rate/trend/suggested_action. |
| MO-031 | BC-LANG-01 | `shared/models/capability.py`, `services/capability-registry/service.py` | `business_impact_description: str = ""` on `Capability`. MS-CAP-01 rejects monetizable capabilities without non-empty `business_impact_description`. |

### Phase D — Dependent Wiring (MO-032–035)

| ID | Depends on | Service | What was built |
|---|---|---|---|
| MO-032 | MO-030 | `services/workflow-engine/service.py` | `wf_default_learner_intervention` in `bootstrap_default_workflows()`. Triggers on `workflow.trigger.learner_intervention`. Step 1: notify learner (at_risk_learner_outreach). Step 2: `at_risk_learner_follow_up` IMPORTANT action item (24h due). |
| MO-033 | MO-028 | `services/entitlement-service/service.py` | `activate_from_payment()` — refreshes or bootstraps tenant subscription on payment verification. Emits `entitlement.activated.confirmed`. |
| MO-034 | MO-027 | `services/onboarding/service.py` | `bootstrap_default_capabilities()` calls `register_free_tier_capability_bundle()` for free-plan tenants via lazy-loaded registry. Idempotent. |
| MO-035 | MO-029 | `backend/services/event-ingestion-service/app/forwarders.py`, `app/main.py` | `RevenueSignalForwarder` — maps 8 B3P07 revenue event types to `receive_revenue_signal()`. Wired into `ForwardingPipeline`. |

### Phase E — Domain Extensions (MO-036–040)

| ID | Domain | Service | What was built |
|---|---|---|---|
| MO-036 | Analytics / BC-BRANCH-01 | `services/analytics-service/service.py` | `_branch_snapshots` dict. `record_branch_snapshot()`. `cross_branch_analytics()` — aggregates completion across branches, best/worst callout, BC-ANALYTICS-01/02 InsightEnvelope. |
| MO-037 | Vocational segment | `services/config-service/platform_defaults.py` | `"vocational"` added to `_SEGMENT_CAPABILITY_DEFAULTS` — 9 base ops caps + 6 CAP-VOCATIONAL-* caps. Activated when `segment_type="vocational"` at onboarding. |
| MO-038 | Pakistan market | `services/config-service/platform_defaults.py` | `_COUNTRY_FEE_DEFAULTS["PK"]` — PKR, JazzCash/EasyPaisa priority, 5-day grace, 2-day reminder cadence, installment support, late fee disabled. Seeded at COUNTRY layer in `seed_platform_defaults()`. |
| MO-039 | Offline / BC-FAIL-01 | `services/offline-sync/service.py` | `register_offline_manifest()` + `list_offline_manifests()` + `receive_pipeline_event()`. Handles `media.pipeline.offline_package_ready`. `offline_manifests` key in default state. |
| MO-040 | Analytics / exams | `services/analytics-service/service.py` | `_exam_results` dict. `ingest_exam_result()`. `exam_performance_insight()` — pass_rate, avg_score, trend, tiered suggested action (<50% critical, 50–75% watchlist, >75% healthy), BC-ANALYTICS-01/02 InsightEnvelope. |

---

## MARKET OVERLAY — PHASE F — DEFERRED

| ID | Description | Status |
|---|---|---|
| MO-041 | Urdu i18n — RTL rendering, string translations, font loading | DEFERRED — no code yet |
| MO-042 | Vocational service build — 6 CAP-VOCATIONAL-* capabilities as running code | DEFERRED — config seeded (MO-037); service build pending |
| MO-043 | Teacher marketplace — discovery, rating, booking for Pakistan freelance tutors | DEFERRED — product design required first |
| MO-044 | Offline LMS-in-a-box — fully self-contained zero-connectivity deployable | DEFERRED — hardware dependency |
