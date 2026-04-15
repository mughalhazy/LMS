# B2P08 — Platform Integration Layer

## Purpose
Define a **stateless orchestration layer** that coordinates runtime platform decisions across:
- config service,
- entitlement system,
- feature flags,
- capability registry,
- usage metering.

This layer does **not** duplicate domain or platform service logic. It only orchestrates, enforces execution order, and returns a deterministic decision envelope.

---

## Scope and QC Alignment

### In scope
- Runtime orchestration for capability access and execution eligibility checks.
- Deterministic, consistent evaluation order.
- Stateless request-time decision computation.
- Standardized interaction contracts to platform services.
- Post-decision usage metering emission.

### Out of scope
- Owning entitlement rules/plan math.
- Owning feature targeting rule definitions.
- Owning capability metadata authoring.
- Owning configuration merge/inheritance logic.
- Owning usage aggregation, billing, or reporting.
- Owning any business-domain workflow (course, assessment, HR, etc.).

### Explicit QC guarantees
- **No duplication of individual services:** all source-of-truth logic remains in the owning service.
- **Only orchestration:** integration layer composes read/write calls and decision results.
- **Correct execution order enforced:** fixed evaluation pipeline with deterministic precedence.
- **Scalable by design:** horizontally scalable stateless workers + cache + async metering.
- **Clear separation from business domains:** only platform contracts are touched.

---

## Integration Architecture

## 1) `PlatformIntegrationAPI` (entrypoint)
**Responsibility:** receive decision requests from gateway/domain services and return a decision envelope.

### Input
- `tenant_id`, `actor_id`, `subject_id`
- `capability_key`
- `resource_context`
- `request_context` (region, channel, client, trace ids)

### Output (decision envelope)
- `decision`: `ALLOW | DENY | CONDITIONAL`
- `effective_capability_version`
- `evaluated_config_snapshot`
- `entitlement_outcome`
- `feature_flag_outcome`
- `reason_codes[]`
- `evaluation_trace_id`
- `metering_event_ref` (if emitted)

## 2) `DecisionOrchestrator` (core stateless engine)
**Responsibility:** enforce the canonical evaluation order and compose upstream outcomes.

- No local durable state.
- Request-scoped in-memory context only.
- Idempotent orchestration using `request_id` / `idempotency_key`.

## 3) `Platform Connectors` (thin clients, no business logic)
- `CapabilityRegistryConnector` (read-only)
- `ConfigServiceConnector` (read-only)
- `EntitlementConnector` (read-only decision query)
- `FeatureFlagConnector` (read-only evaluation query)
- `UsageMeteringConnector` (write-only event emit)

Connectors only translate protocol/schema and apply timeouts/retries/circuit-breaking.

## 4) `Evaluation Order Policy` (hardcoded or declarative pipeline)
A single authoritative policy artifact defines execution order and short-circuit behavior.

## 5) `Decision Cache` (optional, bounded, non-authoritative)
- Cache key: `(tenant_id, actor/subject segment, capability_key, context_hash)`
- Short TTL only.
- Cache accelerates reads but never changes precedence/semantics.
- Safe to evict at any time; no correctness dependence.

## 6) `Observability + Trace` module
- Distributed trace across all connector calls.
- Step-level latency/error metrics.
- Outcome counters by reason code.
- Structured audit log of orchestration path (not domain business events).

---

## Canonical Evaluation Order (Must Be Consistent)

For each request, execution is always:

1. **Capability Registry Resolve**
   - Validate capability exists, status is active, interface version supported.
   - If missing/inactive: hard `DENY` (reason: `CAPABILITY_UNAVAILABLE`).

2. **Config Resolution Fetch**
   - Pull effective config selectors/snapshot required by this capability.
   - If unavailable and capability requires strict config: fail closed (`DENY`).

3. **Entitlement Check**
   - Query entitlement service for allow/deny/scope decision.
   - If deny: hard `DENY` and stop further permissive evaluation.

4. **Feature Flag Evaluation**
   - Evaluate rollout/treatment only after entitlement allow.
   - If off for this context: `DENY` (reason: `FLAG_DISABLED`).

5. **Final Decision Compose**
   - Combine outcomes with deterministic precedence:
     - Any hard deny -> `DENY`
     - Entitlement allow + flag on + capability active -> `ALLOW`
     - Explicit conditional constraints -> `CONDITIONAL`

6. **Usage Metering Emit (post-decision side effect)**
   - Emit standardized usage decision event asynchronously.
   - Metering failure must not mutate access decision; retries handled out-of-band.

This order is immutable per version and explicitly versioned to avoid drift.

---

## Stateless Runtime Decision-Making Model

The integration layer is stateless because it:
- persists no durable domain/platform truth,
- reads current truth from upstream systems every evaluation (optionally cache-assisted),
- treats each request independently,
- externalizes idempotency and retries via request IDs and message keys.

### Stateless scaling pattern
- Deploy N identical orchestrator instances behind load balancer.
- Use shared external cache/message bus only as accelerators/transports.
- Zero sticky-session requirement.
- Horizontal scale via CPU/QPS.

---

## End-to-End Flow

## Flow A: Synchronous runtime access decision
1. Caller sends `EvaluateCapability` request to `PlatformIntegrationAPI`.
2. `DecisionOrchestrator` creates `evaluation_trace_id` and request context.
3. Resolve capability metadata via `CapabilityRegistryConnector`.
4. Fetch effective config via `ConfigServiceConnector`.
5. Check entitlement via `EntitlementConnector`.
6. If entitlement allows, evaluate flags via `FeatureFlagConnector`.
7. Compose final decision using fixed precedence matrix.
8. Return decision envelope to caller.
9. Emit `usage.decision.evaluated` event through `UsageMeteringConnector` (async).

## Flow B: Degraded dependency handling (deterministic)
1. If capability registry unavailable -> fail closed (`DENY`) for unknown capabilities.
2. If config unavailable and capability is strict-config -> fail closed.
3. If entitlement unavailable -> fail closed (`DENY`) unless explicit break-glass policy exists.
4. If feature flag unavailable -> use last-known-good within TTL; otherwise fail closed.
5. Metering unavailable -> enqueue retry, keep user-facing decision unchanged.

---

## Separation from Business Domains

- Domain services call the integration layer as a platform gate, then continue domain workflows independently.
- Integration layer never interprets course content, assessment logic, org hierarchy, or learner progression rules.
- Only platform-level context is evaluated (capability, config, entitlement, rollout, usage emission).

---

## Scalability and Reliability Controls

- Strict connector SLAs (timeouts, retries with backoff, circuit breakers).
- Bulkhead isolation per connector to prevent cascading failures.
- Async metering pipeline with durable queue.
- Read-through cache for high-frequency checks.
- Versioned decision pipeline to support safe rollout/canary.
- Deterministic conformance tests validating order and precedence.

---

## Minimal Decision Precedence Matrix

| Capability | Entitlement | Feature Flag | Final |
|---|---|---|---|
| inactive/missing | any | any | DENY |
| active | deny | any | DENY |
| active | allow | off | DENY |
| active | allow | on | ALLOW |
| active | allow (conditional) | on | CONDITIONAL |

This matrix prevents conflicting outcomes and guarantees consistent orchestration behavior.

---

## Deliverables Produced by This Design
- **Integration architecture:** stateless orchestrator + connectors + fixed-order policy + observability.
- **End-to-end flow:** synchronous decision path and asynchronous metering side effect with deterministic degradation.
