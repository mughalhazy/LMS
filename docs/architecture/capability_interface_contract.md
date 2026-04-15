# B1P01 — Capability Interface Contract

## Purpose
Define a reusable, implementation-agnostic runtime interface for capability modules in LMS backend services.

This contract is intentionally **separate from the Batch 0 capability registry schema** (`docs/architecture/schemas/capability_registry.schema.json`).
The registry remains the source of truth for capability metadata (keys, domains, dependencies, billing/activation metadata), while this document defines runtime behavior expected from any capability plug-in.

---

## Alignment with Batch 0 Registry

### Registry contract (already defined)
- Capability identity, domain, dependency keys, activation metadata, usage meter metadata, segment/country constraints.

### Runtime contract (this document)
- Standard lifecycle methods (`enable` / `disable`)
- Dependency validation hook (against resolved capability graph)
- Usage tracking hook (delegated to telemetry/billing adapters)
- Config injection hook (service/tenant/runtime scoped)

> Separation rule: runtime modules **consume** registry definitions; they do not redefine registry schema fields.

---

## TypeScript-style Interface Definition (implementation-agnostic)

```ts
/**
 * Opaque references from Batch 0 registry. Shape is defined by registry schema,
 * not duplicated in this runtime interface contract.
 */
export type CapabilityKey = string;
export type CapabilityDomain = string; // e.g., learning | commerce | communication | delivery

/** Capability descriptor resolved from registry + activation context. */
export interface CapabilityDescriptorRef {
  key: CapabilityKey;
  domain: CapabilityDomain;
  registryVersion: string;
}

/** Dependency status resolved by a dependency resolver, not by business logic here. */
export interface CapabilityDependencyStatus {
  required: CapabilityKey[];
  satisfied: CapabilityKey[];
  missing: CapabilityKey[];
}

/**
 * Pluggable usage event envelope. Concrete sinks (billing, analytics, audit) are injected.
 */
export interface CapabilityUsageEvent {
  capabilityKey: CapabilityKey;
  tenantId: string;
  actorId?: string;
  action: string;
  quantity?: number;
  unit?: string;
  timestamp: string; // ISO-8601
  attributes?: Record<string, unknown>;
}

/**
 * Runtime config container injected by host service (global/service/tenant/request layers).
 */
export interface CapabilityConfig {
  values: Record<string, unknown>;
  source: "global" | "service" | "tenant" | "request";
  version?: string;
}

/** Host-provided adapters to keep capability implementation-agnostic. */
export interface CapabilityRuntimeAdapters {
  trackUsage(event: CapabilityUsageEvent): Promise<void>;
  now(): string;
}

/** Standard runtime interface every capability module must implement. */
export interface CapabilityModule {
  /** Stable identity mapped to Batch 0 registry capability key. */
  readonly capability: CapabilityDescriptorRef;

  /** Enable/activate capability runtime within host service context. */
  enable(context: CapabilityContext): Promise<void>;

  /** Disable/deactivate capability runtime within host service context. */
  disable(context: CapabilityContext): Promise<void>;

  /** Validate dependencies against resolved registry state before activation. */
  validateDependencies(context: CapabilityContext): Promise<CapabilityDependencyStatus>;

  /** Hook invoked by host/service when capability usage must be metered. */
  onUsage(context: CapabilityContext, event: Omit<CapabilityUsageEvent, "timestamp" | "capabilityKey">): Promise<void>;

  /** Inject or refresh configuration without requiring implementation coupling. */
  injectConfig(context: CapabilityContext, config: CapabilityConfig): Promise<void>;
}

/**
 * Shared execution context passed by host service across domains/services.
 * No domain business rules are encoded in this interface.
 */
export interface CapabilityContext {
  tenantId: string;
  serviceName: string;
  environment: "dev" | "staging" | "prod" | string;
  adapters: CapabilityRuntimeAdapters;

  /** Lookup only (read-side) to avoid duplicating registry schema. */
  getCapabilityState(key: CapabilityKey): Promise<"active" | "inactive" | "paused" | "unknown">;
}

/**
 * Optional plugin registry contract to support modular architecture.
 */
export interface CapabilityPluginRegistry {
  register(module: CapabilityModule): void;
  resolve(key: CapabilityKey): CapabilityModule | undefined;
  list(): CapabilityModule[];
}
```

---

## Language-neutral equivalent (behavioral contract)

A capability plug-in must:
1. Expose stable identity mapped to a registry capability key.
2. Provide `enable` and `disable` lifecycle operations.
3. Provide `validateDependencies` that returns required/satisfied/missing keys using host-provided capability state.
4. Provide a usage hook that emits normalized usage events via injected telemetry adapter.
5. Accept runtime config injection/refetch independent of implementation details.
6. Operate via host adapters/context so the same contract can be reused in any service or language.

---

## Example Usage (host service wiring)

```ts
async function activateCapability(
  key: string,
  context: CapabilityContext,
  pluginRegistry: CapabilityPluginRegistry,
  config: CapabilityConfig,
) {
  const module = pluginRegistry.resolve(key);
  if (!module) throw new Error(`Capability module not registered: ${key}`);

  const depStatus = await module.validateDependencies(context);
  if (depStatus.missing.length > 0) {
    throw new Error(`Dependency validation failed for ${key}: ${depStatus.missing.join(",")}`);
  }

  await module.injectConfig(context, config);
  await module.enable(context);
}

async function recordCapabilityAction(
  key: string,
  context: CapabilityContext,
  pluginRegistry: CapabilityPluginRegistry,
  action: string,
) {
  const module = pluginRegistry.resolve(key);
  if (!module) return;

  await module.onUsage(context, {
    tenantId: context.tenantId,
    action,
    attributes: { service: context.serviceName },
  });
}
```

This example shows interface usage only (registration, dependency check, config injection, enablement, usage hook) and intentionally omits business/domain logic.
