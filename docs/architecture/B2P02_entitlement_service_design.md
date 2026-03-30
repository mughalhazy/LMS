# B2P02 — Entitlement Service Design

## Purpose
Design a deterministic entitlement service that resolves which capabilities are enabled for a tenant context based on:
- `segment`
- `plan`
- `country`
- `add-ons`

The service provides entitlement decisions only. It does not resolve configuration values and does not redefine capability registry data structures.

---

## Scope and Non-Goals (QC Alignment)

### In scope
- Deterministic capability entitlement resolution from commercial inputs.
- Add-on-aware enablement and denial handling.
- Capability dependency enforcement using capability registry metadata.
- Activation rule enforcement (segment/plan/country/add-on policies).
- Read-only integration with capability registry.
- Traceable outputs with decision reasons.

### Out of scope
- Config key/value layering or config precedence (owned by config service).
- Capability registry schema ownership or lifecycle authoring.
- Pricing catalog authoring and commercial packaging management.
- Runtime feature execution (owned by consuming services).

### Explicit QC guarantees
- **No overlap with config service:** no config merge APIs, no config payload processing.
- **No duplication of capability registry:** registry is read-only source of capability metadata/dependencies.
- **Deterministic:** fixed evaluation order, normalized inputs, stable conflict rules.
- **Supports add-on enablement:** add-ons are first-class, composable policy contributors.
- **Separation of concerns:** clear ports for policy, registry, and resolution orchestration.

---

## Service Design (Modules + Responsibilities)

## 1) `EntitlementAPI`
**Responsibility:** External read interface for entitlement decisions.

- `resolve(context)` returns full evaluated capability map.
- `isEnabled(context, capabilityKey)` returns single capability decision based on full deterministic evaluation.
- Accepts only entitlement context dimensions (`tenantId`, `segment`, `plan`, `country`, `addOns`, optional snapshot pins).
- Returns decision metadata (`reasons`, dependency status, revisions).

## 2) `InputNormalizer`
**Responsibility:** Canonicalize request input for deterministic evaluation.

- Validates required fields (`segment`, `plan`, `country`).
- Sorts and deduplicates `addOns` lexicographically.
- Normalizes casing/format for keys based on platform conventions.
- Produces immutable normalized context envelope.

## 3) `PolicyAggregationEngine`
**Responsibility:** Build candidate capability grants/denials from commercial policy.

- Reads base plan policy using `{segment, plan, country}`.
- Reads add-on policy per normalized add-on key in lexical order.
- Aggregates grants and denials into intermediate sets.
- Applies deterministic conflict policy: **denial wins over grant**.
- Does not inspect capability dependency graph.

## 4) `ActivationRuleEvaluator`
**Responsibility:** Enforce capability activation rules.

- Applies policy rule outcomes such as country restrictions, segment gating, plan exclusions, and add-on preconditions.
- Consumes rule results from policy provider contract (no embedded pricing logic).
- Produces per-capability activation status before dependency checks.

## 5) `DependencyResolver`
**Responsibility:** Enforce dependency completeness using capability registry.

- Queries capability dependency metadata from capability registry reader.
- Validates that every candidate-enabled capability has all required dependencies enabled.
- Marks capabilities with missing dependencies as disabled.
- Annotates missing dependency reasons for observability and caller transparency.

## 6) `CapabilityRegistryReaderPort` (read-only integration)
**Responsibility:** Provide registry metadata required by resolver.

- Resolves capability keys to dependency lists and lifecycle status.
- Optional registry snapshot/version pin for deterministic replay.
- Never writes, mutates, or redefines registry entities.

## 7) `EntitlementPolicyProviderPort`
**Responsibility:** Provide commercial entitlement inputs.

- Base entitlement inputs by `segment + plan + country`.
- Add-on entitlement inputs by `addOn + segment + plan + country`.
- Optional revision/snapshot metadata per response.
- Keeps commercial logic outside resolver core.

## 8) `DecisionAssembler`
**Responsibility:** Produce final deterministic output envelope.

- Emits full capability decision map (`enabled|disabled`).
- Attaches reasons (`base_plan`, `addon:<key>`, `denied_by_policy`, `missing_dependency:<key>`).
- Returns evaluation order, policy revisions, registry version, normalized context.
- Emits stable ordering of capabilities in output for deterministic diffs.

## 9) `EntitlementAuditEmitter`
**Responsibility:** Observability and replay support.

- Emits evaluation trace with step timings and snapshot IDs.
- Emits deterministic hash/fingerprint of normalized inputs + policy/registry versions.
- Supports incident replay and audit without exposing sensitive business payloads.

---

## Canonical Separation of Concerns

- **Entitlement service owns:** capability access state resolution and dependency enforcement.
- **Config service owns:** config value retrieval/merging and provenance of config keys.
- **Capability registry owns:** capability identity, dependency graph, lifecycle metadata.
- **Policy systems own:** commercial packaging rules, country/segment/plan/add-on policy definitions.
- **Runtime domain services own:** execution of behavior gated by entitlement decisions.

This separation prevents cross-service duplication and keeps the entitlement service a pure decision engine.

---

## Entitlement Resolution Flow (Deterministic)

## Input contract
Required:
- `tenantId`
- `segment`
- `plan`
- `country`
- `addOns[]` (can be empty)

Optional deterministic pins:
- `policySnapshotVersion`
- `registrySnapshotVersion`

## Fixed evaluation order
1. **Normalize inputs**
   - Validate required dimensions.
   - Deduplicate/sort add-ons.
   - Build immutable normalized context.

2. **Load base policy grants/denials**
   - Query policy provider with `{segment, plan, country}`.

3. **Load add-on policy grants/denials in lexical order**
   - For each normalized add-on key, query policy provider.

4. **Aggregate candidate states**
   - Union all grants.
   - Apply all denials as hard removals.
   - Track reasons (`base_plan`, `addon:<key>`, `denied_by_policy`).

5. **Apply activation rules**
   - Enforce country/segment/plan/add-on activation constraints from policy snapshots.
   - Ineligible capabilities become disabled with explicit rule reasons.

6. **Resolve dependencies via capability registry**
   - For each candidate-enabled capability, read required dependencies.
   - If any dependency is not enabled, mark capability disabled.
   - Record missing dependencies in decision reasons.

7. **Assemble final result**
   - Emit complete evaluated map with enabled/disabled states.
   - Include normalized context, evaluation order, policy revisions, registry version, timestamp.

8. **Emit audit trace**
   - Write deterministic fingerprint and execution trace for replay/debug.

## Determinism rules
- Add-ons are always processed in sorted lexical order.
- Conflict policy is fixed globally: `deny > grant`.
- Dependency checks run after grants/denials and activation rules.
- Output capability map is serialized in stable key order.
- With identical normalized inputs and pinned policy/registry snapshots, results are byte-for-byte equivalent except `resolvedAt`.

---

## Pseudocode
```text
context = normalize(input)

base = policy.getBase(context.segment, context.plan, context.country, context.policySnapshotVersion)
addons = []
for addon in sort(unique(context.addOns)):
  addons.append(policy.getAddOn(addon, context.segment, context.plan, context.country, context.policySnapshotVersion))

candidate = {}        # capability -> {state, reasons}
apply_grants(candidate, base.granted, "base_plan")
apply_denials(candidate, base.denied, "denied_by_policy")

for addonResult in addons:
  apply_grants(candidate, addonResult.granted, "addon:" + addonResult.addOn)
  apply_denials(candidate, addonResult.denied, "denied_by_policy")

apply_activation_rules(candidate, base.rules, addons.rules)

for capability in stable_keys(candidate where state == enabled):
  deps = registry.dependencies(capability, context.registrySnapshotVersion)
  missing = [d for d in deps if candidate[d].state != enabled]
  if missing not empty:
    candidate[capability].state = disabled
    candidate[capability].reasons += map(missing, "missing_dependency:" + d)

return assemble_result(context, candidate, revisions, registryVersion, evaluationOrder)
```

---

## Failure and Edge-Case Handling
- **Unknown add-on key:** treated as no-op or explicit policy error per caller contract; behavior must be configured and documented once globally.
- **Unknown capability in policy payload:** mark disabled with reason `unknown_capability` and include validation event; do not auto-create metadata.
- **Dependency cycle in registry:** fail closed for involved capabilities and emit `dependency_cycle_detected` diagnostics.
- **Partial provider outage:** if policy or registry snapshots cannot be loaded, return deterministic failure (no partial silent success).

---

## QC FIX Mapping (Requested)
- **No overlap with config service:** design contains no config-layer merge/value APIs; only capability access resolution.
- **No duplication of capability registry:** registry accessed only through read-only port for dependencies/metadata.
- **Must be deterministic:** strict step order, sorted add-ons/capabilities, fixed precedence rules, snapshot pins.
- **Must support add-on enablement:** add-on policies loaded and merged as first-class inputs.
- **Clear separation of concerns:** API, policy input, registry read, rule evaluation, dependency enforcement, and output assembly are isolated modules.
