# B1P03 — Entitlement Interface Contract

## Purpose
Define a deterministic, implementation-agnostic interface for resolving which capabilities are entitled for a tenant.

This contract is intentionally **separate from configuration resolution** (`docs/architecture/config_resolution_interface_contract.md`).
- Config resolution decides **values** for config keys.
- Entitlement resolution decides **capability access states**.

This contract also remains **separate from business policy ownership** (pricing, commercial packaging, legal terms). It specifies runtime interface and evaluation order only.

---

## Scope Boundaries (QC)
- **No overlap with config system:** no config key merges, no value schema handling, no config hierarchy APIs.
- **No business logic in interface:** plan packaging rules and commercial policy are external inputs.
- **Deterministic behavior required:** same input snapshot must always produce the same output snapshot.
- **Add-on architecture support:** add-ons are first-class input units and can contribute grants/revocations.
- **Clear separation of responsibility:**
  - Capability Registry = capability metadata and dependency graph source.
  - Entitlement Resolver = state resolution orchestration only.
  - Policy/Packaging Provider = supplies plan/add-on/segment/country entitlements.

---

## Input Model

```ts
export type CapabilityKey = string;
export type SegmentKey = string;
export type PlanKey = string;
export type CountryCode = string;
export type AddOnKey = string;

export interface EntitlementContext {
  tenantId: string;
  segment: SegmentKey;
  plan: PlanKey;
  country: CountryCode;
  addOns: AddOnKey[];

  /** Optional snapshot/version pin to guarantee deterministic replay. */
  policySnapshotVersion?: string;
}
```

---

## Dependency and Registry Contracts

```ts
/** Read-only reference to capability registry (source of dependency metadata). */
export interface CapabilityRegistryReader {
  getCapability(capabilityKey: CapabilityKey): Promise<{
    key: CapabilityKey;
    dependencies: CapabilityKey[];
    status?: "active" | "deprecated" | "sunset";
  } | undefined>;

  listCapabilities(keys?: CapabilityKey[]): Promise<Array<{
    key: CapabilityKey;
    dependencies: CapabilityKey[];
    status?: "active" | "deprecated" | "sunset";
  }>>;
}

/** Policy input adapter; owns commercial/business rules outside this interface. */
export interface EntitlementPolicyProvider {
  getBaseGrants(input: {
    segment: SegmentKey;
    plan: PlanKey;
    country: CountryCode;
    policySnapshotVersion?: string;
  }): Promise<{
    granted: CapabilityKey[];
    denied?: CapabilityKey[];
    revision?: string;
  }>;

  getAddOnGrants(input: {
    addOn: AddOnKey;
    segment: SegmentKey;
    plan: PlanKey;
    country: CountryCode;
    policySnapshotVersion?: string;
  }): Promise<{
    granted: CapabilityKey[];
    denied?: CapabilityKey[];
    revision?: string;
  }>;
}
```

---

## Entitlement Resolution Interface

```ts
export type EntitlementState = "enabled" | "disabled";

export interface CapabilityEntitlement {
  capabilityKey: CapabilityKey;
  state: EntitlementState;
  reasons: string[]; // e.g., ["base_plan", "addon:advanced_analytics"]
  dependencies: {
    required: CapabilityKey[];
    missing: CapabilityKey[];
  };
}

export interface EntitlementResolutionResult {
  tenantId: string;
  context: Pick<EntitlementContext, "segment" | "plan" | "country" | "addOns">;
  capabilities: Record<CapabilityKey, CapabilityEntitlement>;

  /** Determinism and traceability metadata. */
  evaluationOrder: string[]; // fixed order steps executed by resolver
  registryVersion?: string;
  policyRevisions: string[];
  resolvedAt: string; // ISO-8601
}

export interface EntitlementResolver {
  /** Resolve all relevant capability entitlements for a tenant context. */
  resolve(context: EntitlementContext): Promise<EntitlementResolutionResult>;

  /** Fast check for a single capability after full deterministic evaluation. */
  isEnabled(context: EntitlementContext, capabilityKey: CapabilityKey): Promise<boolean>;
}
```

---

## Deterministic Evaluation Rules
Given the same `EntitlementContext` and same registry/policy snapshots, resolvers must execute this exact order:

1. Normalize inputs (sort/deduplicate `addOns`).
2. Load base grants/denials from policy provider (`segment + plan + country`).
3. Load each add-on grant/denial in lexicographic add-on key order.
4. Compute candidate enabled set:
   - Start from base grants.
   - Apply add-on grants.
   - Apply denials as hard removals.
5. Enforce dependencies using capability registry:
   - Any capability with missing required dependencies is marked `disabled`.
6. Return full map with explicit `enabled`/`disabled` state for each evaluated capability and deterministic metadata.

Conflict rule inside step 4: **denial wins over grant**.

---

## Example Entitlement Resolution

### Input
- `tenantId`: `tenant_acme_42`
- `segment`: `enterprise`
- `plan`: `pro`
- `country`: `US`
- `addOns`: `["advanced_analytics", "ai_tutor_pack"]`

### External snapshots (provided inputs)
- Base policy grants: `course.catalog`, `reporting.core`, `ai.tutor.basic`
- Add-on `advanced_analytics` grants: `reporting.advanced`
- Add-on `ai_tutor_pack` grants: `ai.tutor.pro`
- No explicit denials
- Capability registry dependencies:
  - `reporting.advanced` depends on `reporting.core`
  - `ai.tutor.pro` depends on `ai.tutor.basic`

### Deterministic result
- `course.catalog`: **enabled** (base_plan)
- `reporting.core`: **enabled** (base_plan)
- `reporting.advanced`: **enabled** (addon:advanced_analytics; dependency satisfied)
- `ai.tutor.basic`: **enabled** (base_plan)
- `ai.tutor.pro`: **enabled** (addon:ai_tutor_pack; dependency satisfied)

If `ai.tutor.basic` were denied by policy snapshot, `ai.tutor.pro` would be **disabled** with missing dependency `["ai.tutor.basic"]`.

---

## Responsibility Split (for implementation teams)
- **Entitlement interface (this document):** defines deterministic resolution contract and outputs.
- **Capability registry:** defines capability identity/dependencies and lifecycle metadata.
- **Policy provider(s):** define commercial/business entitlements and add-on packaging.
- **Runtime services:** consume resolved entitlements to allow/deny capability execution.

This preserves strict boundaries while supporting pluggable add-on growth and deterministic entitlement checks.
