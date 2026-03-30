# B1P02 — Config Resolution Interface Contract

## Purpose
Define a storage-agnostic runtime contract for resolving effective configuration values across the required hierarchy:

`global → country → segment → plan → tenant`

This document describes **resolution behavior only**. It does **not** define persistence, data schema ownership, or capability runtime lifecycle APIs.

---

## Scope Boundaries (QC)
- **No overlap with capability interface:** this contract resolves config values only; it does not include capability enable/disable, dependency validation, or usage metering concerns.
- **No config schema duplication:** keys and value schemas remain owned by domain/config schema docs; this interface treats config as opaque key/value payloads.
- **Runtime dynamic decisions:** resolver accepts runtime context and optional selectors/overrides per call.
- **No persistence assumptions:** values are supplied by caller-provided providers/adapters.
- **Clear hierarchy enforcement:** merge order is fixed and deterministic.

---

## Interface Definition (TypeScript-style, implementation-agnostic)

```ts
export type ConfigKey = string;
export type ConfigMap = Record<string, unknown>;

/** Required hierarchy dimensions for this contract. */
export interface ResolutionContext {
  tenantId: string;
  countryCode: string; // ISO-ish country marker used by caller policy
  segmentKey: string;
  planKey: string;

  /** Optional runtime selectors for dynamic decisions (request/user/workload/experiment/etc.). */
  runtimeSelectors?: Record<string, string | number | boolean>;
}

/**
 * A configuration layer payload. The interface does not dictate where/how this payload is stored.
 */
export interface ConfigLayer {
  level: "global" | "country" | "segment" | "plan" | "tenant";
  values: ConfigMap;
  revision?: string;
}

/** Explicit overrides applied after hierarchy merge. */
export interface ResolutionOverrides {
  values: ConfigMap;
  reason?: string; // e.g., emergency_hotfix | request_scope | experiment
  expiresAt?: string; // ISO-8601 optional guard
}

/** Source adapter contract (DB/cache/file/service can implement this externally). */
export interface ConfigLayerProvider {
  getGlobalLayer(keys?: ConfigKey[]): Promise<ConfigLayer | undefined>;
  getCountryLayer(countryCode: string, keys?: ConfigKey[]): Promise<ConfigLayer | undefined>;
  getSegmentLayer(segmentKey: string, keys?: ConfigKey[]): Promise<ConfigLayer | undefined>;
  getPlanLayer(planKey: string, keys?: ConfigKey[]): Promise<ConfigLayer | undefined>;
  getTenantLayer(tenantId: string, keys?: ConfigKey[]): Promise<ConfigLayer | undefined>;
}

/** Deterministic output for observability/debugging without leaking storage concerns. */
export interface ResolutionResult {
  values: ConfigMap;
  appliedLevels: Array<"global" | "country" | "segment" | "plan" | "tenant" | "override">;
  provenance: Record<ConfigKey, "global" | "country" | "segment" | "plan" | "tenant" | "override">;
  timestamp: string; // resolver clock time
}

/** Main runtime resolver interface. */
export interface ConfigResolver {
  /** Resolve one key using enforced hierarchy and optional runtime overrides. */
  resolveKey(
    key: ConfigKey,
    context: ResolutionContext,
    options?: { overrides?: ResolutionOverrides },
  ): Promise<{ value: unknown; source: ResolutionResult["provenance"][ConfigKey]; result: ResolutionResult }>;

  /** Resolve a filtered key set. */
  resolveKeys(
    keys: ConfigKey[],
    context: ResolutionContext,
    options?: { overrides?: ResolutionOverrides },
  ): Promise<ResolutionResult>;

  /** Resolve all available values for a context (bounded by provider behavior). */
  resolveAll(
    context: ResolutionContext,
    options?: { overrides?: ResolutionOverrides },
  ): Promise<ResolutionResult>;
}
```

---

## Hierarchy Enforcement Rules
Given a context, the resolver must apply layers in this exact order:

1. `global`
2. `country`
3. `segment`
4. `plan`
5. `tenant`
6. `override` (if present)

Conflict rule: for duplicate keys, **later level wins**.

Pseudo-flow:

```text
effective = {}
for level in [global, country, segment, plan, tenant]:
  effective = merge(effective, level.values)
if overrides present:
  effective = merge(effective, overrides.values)
return effective + provenance
```

---

## Resolution Flow Example

### Input
- Context:
  - tenantId: `tenant_acme_42`
  - countryCode: `US`
  - segmentKey: `enterprise`
  - planKey: `pro`
  - runtimeSelectors: `{ rolloutRing: "ring2", channel: "web" }`
- Target key: `runtime.rate_limit.requests_per_minute`

### Layer values returned by provider
- global: `100`
- country (US): `120`
- segment (enterprise): `150`
- plan (pro): `180`
- tenant (tenant_acme_42): _not set_
- override (request-scope experiment): `220`

### Runtime result
- Effective value: `220`
- Source/provenance: `override`
- Applied levels: `[global, country, segment, plan, override]`

If override is omitted, effective value becomes `180` from `plan`.

---

## Notes for Implementers
- Keep provider and resolver decoupled: resolver orchestrates merge logic only.
- Runtime selectors are caller-defined and can drive dynamic provider behavior (for example, A/B rollout partitions) without changing this interface.
- Avoid embedding schema validation here; perform schema checks in dedicated config-schema modules.
