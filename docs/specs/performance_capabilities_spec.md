# Performance Capabilities Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.13

---

## Capability Domain: §5.13 Performance Capabilities

Covers: high concurrency handling | session isolation | load resilience

---

## Nature of This Domain

Performance capabilities are cross-cutting infrastructure capabilities — they are not implemented as a standalone service but enforced through the gateway, event bus, tenant isolation model, and service design patterns. This spec documents where and how each capability is implemented.

---

## Capabilities Defined

### CAP-HIGH-CONCURRENCY
- The platform must handle high concurrent learner sessions without performance degradation
- Implementation points:
  - API gateway rate limiting per tenant (`infrastructure/api-gateway/`)
  - Event bus partitioning by tenant key (`infrastructure/event-bus/`)
  - Async processing via event-driven patterns (ARCH_05)
  - Background job processing for analytics and reporting workloads
- Spec ref: `docs/architecture/scalability_strategy.md`
- QC: `docs/qc/performance_smoke_tests.py`, `docs/qc/load_test_preparation_report.md`

### CAP-SESSION-ISOLATION
- Each learner session must be isolated — no cross-tenant or cross-session data leakage
- Implementation points:
  - Tenant context resolution at API gateway (all requests carry tenant_id)
  - Tenant partitioning as primary DB key (`ARCH_07`)
  - Token-scoped session tokens with tenant binding
  - No shared session state across tenant boundaries
- Spec ref: `docs/architecture/ARCH_07_multi_tenant_isolation_model.md`
- QC: `docs/qc/tenant_model_validation_qc_gate2.md`

### CAP-LOAD-RESILIENCE
- The platform must degrade gracefully under load, not fail hard
- Implementation points:
  - Circuit breakers and retry policies at service boundaries
  - Dead letter queues for failed event processing (ARCH_05)
  - Rate limiting and quota enforcement at gateway
  - Capability gating to shed non-critical load during peak
- Spec ref: `docs/architecture/scalability_strategy.md`, `docs/architecture/platform_long_term_evolution_model.md`
- QC: `docs/qc/load_test_readiness_check.py`

---

## Configuration

All performance thresholds (rate limits, concurrency caps, circuit breaker thresholds) are config-driven — stored in the config service, not hardcoded in services.

---

---

## Exam Session Concurrency SLA (BC-EXAM-01)

**Added:** 2026-04-14 | **Gap:** MO-021 | **Contract:** BC-EXAM-01 — High-Stakes Sessions Are Inviolable

BC-EXAM-01 requires that exam sessions run in "stability-prioritised mode" — the platform must handle the full expected concurrent load for the tenant's largest batch without degradation. This section defines the concurrency SLA for exam sessions.

### SLA Requirements

| Metric | Requirement |
|---|---|
| Concurrent exam sessions per tenant | Must handle the tenant's `max_batch_size × 1.2` concurrent sessions without degradation |
| Answer submission latency (p99) | < 500ms under full concurrent exam load |
| Answer checkpoint persistence | Every submitted answer must be persisted within 2 seconds of submission |
| Session resumption (after disconnect) | Learner must resume from last checkpointed state within 5 seconds of reconnection |
| Background process suppression | During an active exam session, no background sync, analytics batch jobs, or upgrade checks may compete for session bandwidth |
| Failure rate | < 0.1% of exam submissions lost during any single tenant's exam event |

### Load Profile Definitions

| Tier | Expected Concurrent Exam Sessions | Rationale |
|---|---|---|
| Free tier | Up to 50 | Single batch, 50 student limit |
| Starter tier | Up to 500 | Up to 3 batches × ~150 students |
| Pro tier | Up to 5,000 | Up to 20 batches × ~250 students, or large single-batch exams |
| Enterprise tier | Up to 50,000 | Coaching academy mock tests (KIPS, Star) — single-event peak |

**Note:** The 50,000-session load profile (enterprise mock test scenario) requires dedicated infrastructure allocation — it cannot be served from shared SaaS infrastructure without prior capacity planning. Enterprise tenants must configure peak exam event windows in advance.

### Implementation Points

- Exam engine: `services/exam-engine/` — answer checkpointing on every `submit_answer()` call (CGAP-057 partial; checkpoint storage pending)
- API gateway: dedicated `exam-session` route group with rate limit bypass for enrolled exam participants
- Event bus: exam-session events use dedicated partition, isolated from analytics/reporting event streams during active exam windows
- Config: `exam_session.checkpoint_interval_ms = 2000` (default — configurable per tenant)
- Monitoring: exam session active count exposed as a metric in `infrastructure/observability/` — triggers capacity alert at 80% of tier limit

---

## Multi-Branch Scale Profile (BC-BRANCH-01)

**Added:** 2026-04-14 | **Gap:** MO-021 | **Contract:** BC-BRANCH-01 — Multi-Branch Operations: Unified Visibility Without Context Switching

### SLA Requirements for Multi-Branch Tenants

| Metric | Requirement |
|---|---|
| Cross-branch Daily Action List generation | < 3 seconds for tenants with up to 50 branches |
| Cross-branch analytics aggregate query | < 5 seconds for tenants with up to 50 branches |
| Branch-scoped RBAC check latency (p99) | < 50ms added overhead vs single-branch equivalent |
| Concurrent branch operator sessions | Must handle all branch managers operating simultaneously during peak hours (typically 08:00–10:00 local time) |

### Branch Scale Tiers

| Plan | Max Branches | Concurrent Branch Operators | Analytics Scope |
|---|---|---|---|
| Free | 1 | 1 | Single branch |
| Starter | 5 | 10 | Up to 5 branches aggregate |
| Pro | 20 | 50 | Up to 20 branches aggregate |
| Enterprise | Unlimited | Unlimited | Full cross-branch aggregate |

### Implementation Notes

- Cross-branch queries must use branch_id index on all data tables — not sequential branch-by-branch queries
- HQ Daily Action List aggregation must be pre-computed at scheduled intervals (every 15 minutes), not generated on-demand per HQ login
- Branch-scope RBAC check must be cached per user session (TTL = session length, invalidated on role binding change)

---

## References

- Master Spec §5.13, §7 (load resilience as market enforcement)
- `docs/architecture/scalability_strategy.md`
- `docs/architecture/ARCH_07_multi_tenant_isolation_model.md`
- `docs/architecture/ARCH_08_observability_architecture.md`
- `infrastructure/load-testing/`
- `docs/specs/platform_behavioral_contract.md` — BC-EXAM-01, BC-BRANCH-01
- `docs/architecture/multi_branch_rbac_model.md` — multi-branch RBAC model
- `docs/specs/exam_engine_spec.md` — exam engine spec
- `LMS_Pakistan_Market_Research_MASTER.md` §3.2 (coaching academies — server crashes during mock tests)
