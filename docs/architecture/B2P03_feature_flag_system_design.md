# B2P03 — Feature Flag System Design

## Purpose
Design a runtime feature flag system that enables dynamic feature activation controls without redeployments.

The system supports:
- tenant-level flags,
- segment-level flags,
- experiment flags,
- deterministic runtime evaluation,
- strict integration with config + entitlement boundaries.

---

## Scope & Non-Goals (QC Alignment)

### In scope
- Runtime-evaluated `on/off` feature activation decisions.
- Multi-scope targeting with deterministic precedence:
  - global baseline,
  - segment-level rules,
  - tenant-level overrides,
  - experiment allocations.
- Fast decision path suitable for per-request checks.
- Read-only integration with entitlement decisions and config values.
- Versioned rule snapshots and low-latency cache invalidation.

### Out of scope
- Entitlement computation (who is commercially allowed).
- Configuration value merge/resolution (what parameter value to use).
- Experiment analysis/statistics/reporting UI.
- Domain feature execution logic in product services.

### Explicit QC guarantees
- **No overlap with entitlement logic:** flags can only further restrict or stage rollout of already-entitled capabilities.
- **No duplication of config system:** flag system returns activation states only (`enabled/disabled + reason`), never key/value config payloads.
- **Must support experimentation:** first-class experiment allocator with deterministic bucketing.
- **Lightweight and fast:** single in-memory evaluation path with precompiled rule snapshots and cache-first reads.
- **Clear evaluation boundaries:** explicit ordered pipeline with isolated integrations at defined steps.

---

## Service Design (Modules + Responsibilities)

## 1) `FeatureFlagAPI`
**Responsibility:** Runtime read interface for callers.

- `isEnabled(context, featureKey)` → boolean + metadata.
- `resolveMany(context, featureKeys[])` → vectorized decisions for batch checks.
- Accepts evaluation context (`tenantId`, `segment`, `userId/sessionId`, optional request attributes).
- Returns decision envelope with `state`, `reason`, `ruleId`, `snapshotVersion`, `evaluatedAt`.

## 2) `FlagDefinitionStorePort`
**Responsibility:** Read flag definitions/rules from backing storage.

- Storage-agnostic adapter (DB/KV/config repo/API).
- Provides immutable, versioned rule snapshots.
- Supports incremental updates for low-cost cache refresh.

## 3) `SnapshotCompiler`
**Responsibility:** Convert raw rules into evaluation-optimized structures.

- Precompiles targeting predicates (segment matchers, tenant sets, experiment metadata).
- Produces compact in-memory index:
  - `featureKey -> ordered rule chain`.
- Runs on snapshot publish/update, not on request path.

## 4) `RuntimeDecisionEngine`
**Responsibility:** Deterministic hot-path evaluation.

- Executes fixed precedence order:
  1. hard safety kill-switch,
  2. entitlement gate integration,
  3. segment rule,
  4. tenant override,
  5. experiment allocation,
  6. default fallback.
- Emits exactly one terminal decision per feature.

## 5) `EntitlementGuardPort` (read-only)
**Responsibility:** Enforce hard boundary with entitlement service.

- Consumes entitlement decision (`allowed|denied`) for capability/feature mapping.
- If denied by entitlement, final flag decision is always `disabled` regardless of flag rules.
- Never computes or mutates entitlement.

## 6) `ConfigContextPort` (read-only)
**Responsibility:** Consume resolved runtime context from config system without duplicating it.

- Reads only the minimal selector inputs needed for targeting (for example `segment`, environment ring, region markers).
- Does not merge config values.
- Optional dependency for context enrichment, not for decision ownership.

## 7) `ExperimentAllocator`
**Responsibility:** Deterministic experiment assignment.

- Uses stable hashing over `(experimentId, subjectKey)` where subjectKey is typically `tenantId:userId` (or tenant-level fallback).
- Maps hash to weighted variant buckets.
- Returns assignment metadata (`experimentId`, `variant`, `bucket`, `allocationVersion`).
- Supports holdout/control and gradual ramp.

## 8) `EdgeFlagCache`
**Responsibility:** Low-latency runtime performance.

- In-memory L1 per instance + optional distributed L2.
- Caches compiled snapshot and optionally recent decision tuples.
- Invalidation by snapshot version events; TTL as safety fallback.

## 9) `FlagAuditAndMetricsEmitter`
**Responsibility:** Observability and replay.

- Emits counters and latency histograms by feature and reason code.
- Emits sampled decision traces for debugging (without sensitive payloads).
- Tracks experiment exposure events for downstream analytics.

---

## Clear Ownership Boundaries (QC FIX)

- **Entitlement Service owns:** whether tenant/context is allowed to access capability at all.
- **Config Service owns:** hierarchical key/value resolution and provenance.
- **Feature Flag Service owns:** runtime activation toggles and rollout targeting for already-defined features.
- **Experimentation/Analytics Platform owns:** statistical analysis, winner selection, and reporting.
- **Product Runtime Services own:** executing feature behavior once activation decision is provided.

**Boundary rule:**
`final_access = entitlement_allow AND feature_flag_enable`

This means feature flags can narrow exposure but cannot grant access beyond entitlement.

---

## Evaluation Flow (Runtime)

## Input contract
Required:
- `featureKey`
- `tenantId`
- `segment`

Optional:
- `userId` / `sessionId`
- `requestAttributes` (channel, locale, app version, etc.)
- `snapshotVersion` pin for replay

## Deterministic evaluation sequence
1. **Load compiled snapshot**
   - Read current compiled rules from `EdgeFlagCache`.
   - If cache miss, fetch versioned snapshot via `FlagDefinitionStorePort` and compile if needed.

2. **Evaluate hard kill-switch**
   - If global kill-switch for feature is active, return `disabled(reason=kill_switch)`.

3. **Check entitlement boundary**
   - Call/read `EntitlementGuardPort` for mapped capability access.
   - If entitlement denies, return `disabled(reason=entitlement_denied)`.

4. **Apply segment-level rule**
   - Evaluate segment targeting predicate for `segment` and optional attributes.
   - Produce provisional state.

5. **Apply tenant-level override**
   - If explicit tenant override exists, it supersedes segment/default state.

6. **Apply experiment rule (if attached)**
   - Execute deterministic bucket assignment in `ExperimentAllocator`.
   - Convert assigned variant into terminal `enabled/disabled` (or variant metadata for caller).

7. **Finalize decision + emit telemetry**
   - Return envelope with terminal state, reason, matched rule IDs, snapshot version, and experiment metadata.
   - Emit metrics/audit asynchronously.

## Precedence summary
`kill_switch > entitlement_guard > tenant_override > experiment_rule > segment_rule > default`

(Experiment is evaluated after tenant overrides so explicit tenant operational controls always win.)

---

## Lightweight/Fast Design Notes

- Precompile rule DAG/index per snapshot; avoid dynamic parsing during request handling.
- Use lock-free atomic pointer swap to activate new compiled snapshot in-process.
- Keep hot-path operations O(1) to O(log n) by direct `featureKey` index lookup.
- Vectorized API (`resolveMany`) reduces round trips for pages/services checking multiple flags.
- Async telemetry emission prevents blocking decision latency.
- Fallback behavior is fail-safe:
  - if snapshot unavailable → conservative default (`disabled`) for protected features,
  - if entitlement dependency unavailable → fail closed (`disabled(reason=entitlement_unavailable)`).

---

## Pseudocode
```text
function evaluate(featureKey, context):
  snapshot = cache.getCompiled(snapshotVersion=context.pin) or loadCompiledLatest()

  ruleChain = snapshot.rulesByFeature[featureKey]
  if ruleChain.killSwitch == ON:
    return disabled("kill_switch")

  ent = entitlementGuard.isAllowed(context.tenantId, featureKey)
  if ent == false:
    return disabled("entitlement_denied")

  state = ruleChain.defaultState

  if ruleChain.segmentRule.matches(context.segment, context.requestAttributes):
    state = ruleChain.segmentRule.state

  if ruleChain.tenantOverrides.contains(context.tenantId):
    state = ruleChain.tenantOverrides[context.tenantId]

  if ruleChain.experiment is not null:
    assignment = allocator.assign(ruleChain.experiment, subjectKey(context))
    state = assignmentToState(assignment)

  emitTelemetry(featureKey, context, state, snapshot.version)
  return decision(state, snapshot.version)
```

---

## QC FIX RE QC 10/10 Mapping

- **No overlap with entitlement logic:** entitlement is a read-only hard gate in step 3; flag service does not compute commercial rights.
- **No duplication of config system:** config is optional context input only; no config merge/value APIs in this design.
- **Must support experimentation:** deterministic allocator, weighted variants, control/holdout, exposure telemetry.
- **Must be lightweight and fast:** precompiled snapshots, cache-first reads, O(1)/O(log n) lookup, async telemetry.
- **Clear evaluation boundaries:** fixed seven-step runtime sequence with explicit precedence and terminal decision semantics.
