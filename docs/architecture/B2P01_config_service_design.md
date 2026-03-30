# B2P01 — Config Service Design

## Purpose
Design a storage-agnostic runtime configuration service for LMS that resolves effective configuration across:

`global → country → segment → plan → tenant`

The design focuses on **configuration retrieval and resolution only**. It explicitly excludes entitlement decisions, policy enforcement logic, and UI concerns.

---

## Scope & Non-Goals (QC Alignment)

### In scope
- Hierarchical config resolution with deterministic override precedence.
- Runtime-resolvable reads for service requests/jobs/events.
- Capability-aware config lookup (config keyed/scoped by capability identity).
- Storage-agnostic provider abstraction (DB/cache/file/API can back it).

### Out of scope
- Entitlement evaluation (who is allowed to use capability/feature).
- Capability lifecycle logic (enable/disable/dependency checks).
- Business-rule computation in resolver (no domain decision trees).
- UI schemas/forms, UI fallback behavior, or presentation defaults.

### Batch 0 compatibility guardrails
- The service **references** Batch 0 capability/config registries as upstream authorities and does not redefine their schemas.
- Config values are treated as opaque typed payloads validated by external schema services.

---

## Service Design (Modules + Responsibilities)

## 1) `ConfigResolutionAPI` (read interface)
**Responsibility:** Runtime entrypoint for callers.

- Exposes read methods such as:
  - `resolveKey(context, key, options)`
  - `resolveKeys(context, keys, options)`
  - `resolveNamespace(context, namespace, options)`
- Accepts required hierarchy context (`tenantId`, `country`, `segment`, `plan`) plus optional runtime selectors.
- Returns value + provenance metadata (which layer won).
- Does not expose persistence or schema internals.

## 2) `ResolutionOrchestrator` (core merge engine)
**Responsibility:** Deterministic merge execution.

- Fetches layers in fixed order: `global → country → segment → plan → tenant`.
- Applies optional runtime override layer last (ephemeral/request-scoped).
- Performs last-writer-wins merge for conflicting keys.
- Produces:
  - effective config map,
  - per-key provenance,
  - applied revision set (for audit/trace),
  - resolution timestamp.

## 3) `CapabilityConfigProjector` (capability-aware projection)
**Responsibility:** Capability-based views over resolved config.

- Supports config retrieval by capability identity without implementing entitlement logic.
- Example behavior:
  - Filter resolved map to keys mapped to `capabilityKey`.
  - Return capability-scoped sub-document for runtime modules.
- Consumes capability metadata references from external registry contracts.
- Never decides whether capability is allowed/active for tenant.

## 4) `LayerProviderPort` (storage abstraction)
**Responsibility:** Isolate resolver from storage mechanics.

- Defines provider interface for retrieving each hierarchy layer.
- Implementations may use SQL, KV store, config repo, cache, or remote service.
- Supports partial key fetch for efficiency (`keys[]`/namespace filters).
- Returns normalized layer payload envelope: `{ level, values, revision, fetchedAt }`.

## 5) `SchemaValidationPort` (optional external validation)
**Responsibility:** Keep resolver schema-agnostic while enabling runtime safety.

- Optional adapter invoked to validate resolved payloads against canonical schemas.
- Uses schema references/version IDs from registry systems.
- Validation outcomes returned as metadata (warnings/errors) without embedding schema definitions in resolver.

## 6) `RuntimeOverrideManager`
**Responsibility:** Managed high-precedence temporary overrides.

- Accepts request/job scoped override bundles with TTL and reason.
- Ensures overrides are ephemeral and auditable.
- Applies only at runtime call boundary (not persisted by resolver core).

## 7) `ConfigSnapshotCache` (optional performance layer)
**Responsibility:** Speed up repeated runtime resolution while preserving correctness.

- Caches effective snapshots by resolution context fingerprint.
- Cache key dimensions include hierarchy IDs + capability projection selectors + revision vector.
- Invalidation driven by revision changes/events; never changes merge semantics.

## 8) `ResolutionAuditEmitter`
**Responsibility:** Operational observability.

- Emits resolution traces/metrics:
  - latency,
  - cache hit/miss,
  - layers consulted,
  - override usage,
  - unresolved keys.
- Emits audit-safe payloads (no sensitive values by default).

---

## Canonical Separation: Config vs Logic

- **Config service owns:** retrieval, merge precedence, provenance, projection.
- **Business/domain services own:** interpreting values and executing behavior.
- **Entitlement service owns:** permission/plan rights checks.
- **Capability runtime owns:** lifecycle/dependency/usage handling.

This keeps the config service a pure read/resolve platform primitive.

---

## Config Resolution Flow

## Input contract
Caller provides:
- `tenantId` (required)
- `countryCode` (required)
- `segmentKey` (required)
- `planKey` (required)
- `runtimeSelectors` (optional; e.g., channel, rollout ring)
- `requestedKeys` or `namespace`
- `capabilityKey` (optional projection selector)
- `overrides` (optional ephemeral layer)

## Runtime flow (deterministic)
1. **Normalize context**
   - Validate required hierarchy dimensions exist.
   - Build immutable resolution request envelope.

2. **Fetch hierarchy layers via `LayerProviderPort`**
   - Query global layer.
   - Query country layer.
   - Query segment layer.
   - Query plan layer.
   - Query tenant layer.

3. **Merge layers in fixed order**
   - Start with empty map.
   - Merge each layer sequentially.
   - For key conflict, newest level in hierarchy wins.

4. **Apply runtime overrides (if provided)**
   - Validate TTL/reason format.
   - Merge override values as final highest-precedence layer.

5. **Project by capability (optional)**
   - If `capabilityKey` is present, filter/project resolved map through capability metadata mapping.
   - Do not perform entitlement decision.

6. **Optional external schema validation**
   - Validate resulting payload through `SchemaValidationPort`.
   - Attach validation metadata (non-blocking or blocking per caller policy).

7. **Return result envelope**
   - `values`: effective map (or projected map)
   - `provenance`: per-key winner layer
   - `appliedLevels`: ordered set actually used
   - `revisions`: revision identifiers for traceability
   - `resolvedAt`: timestamp
   - `validation`: optional schema validation summary

## Pseudocode
```text
effective = {}
provenance = {}
for layer in [global, country, segment, plan, tenant]:
  for (k, v) in layer.values:
    effective[k] = v
    provenance[k] = layer.level

if overrides:
  for (k, v) in overrides.values:
    effective[k] = v
    provenance[k] = "override"

if capabilityKey:
  effective = project_to_capability(effective, capabilityKey)
  provenance = filter_provenance(provenance, keys(effective))

return envelope(effective, provenance, appliedLevels, revisions, resolvedAt)
```

---

## Dynamic Runtime Behavior Support

The design supports dynamic behavior by:
- Resolving on-demand per request/job/event context.
- Accepting runtime selectors for channel/ring/workload variations.
- Supporting ephemeral overrides with TTL for incident mitigation and experiments.
- Allowing projection by capability key at read time.
- Exposing revision metadata so callers can re-resolve on change signals.

No deployment-time compile step is required for effective reads.

---

## Storage-Agnostic Guarantees

- Resolver core depends only on `LayerProviderPort` contract.
- Storage-specific concerns (indexes, table layout, caching backend) remain in provider implementations.
- Multiple providers can coexist (e.g., primary DB + edge cache) without changing API/merge semantics.

---

## QC Checklist Mapping

- **No overlap with entitlement system:** capability projection only; no allow/deny decisions.
- **No duplication of Batch 0 schema:** external references only; no schema redefinition.
- **Clear config vs logic separation:** resolver returns values; business services interpret behavior.
- **Dynamic runtime behavior:** selectors + overrides + on-demand resolution.
- **Storage-agnostic:** provider port abstraction with pluggable adapters.
