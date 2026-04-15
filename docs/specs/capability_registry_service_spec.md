# Capability Registry Service Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §2 | **Service:** `services/capability-registry/`

---

## Service Boundary

The capability registry service is the single source of truth for all capability metadata and dependency relationships. Full design in `docs/architecture/B2P05_capability_registry_service_design.md`. This spec documents the deployable service.

---

## What This Service Does

- Stores authoritative capability records (key, domain, dependencies, billing type, lifecycle metadata)
- Serves capability lookups and dependency graph queries
- Validates capability definitions before publish
- Manages versioned snapshots for deterministic downstream consumption
- Emits events on registry changes

## What This Service Does NOT Do

- Does not resolve entitlements (owned by entitlement service)
- Does not resolve config values (owned by config service)
- Does not execute capabilities (owned by domain services)

---

## Core Modules (from B2P05)

| Module | Responsibility |
|---|---|
| `CapabilityRegistryAPI` | Read/write lifecycle operations |
| `CapabilityCatalogStore` | Persistent storage of capability records |
| `DependencyGraphIndex` | Query-optimised dependency mapping |
| `RegistryValidator` | Pre-publish validation gate |
| `SnapshotManager` | Versioned registry release |
| `EntitlementRegistryReaderPort` | Read-only contract for entitlement system |
| `RegistryChangeEmitter` | Event emission on registry changes |

---

## Canonical Schema

`docs/architecture/schemas/capability_registry.schema.json`

---

---

## Architectural Contract: MS-CAP-01 — Capability Definition Completeness (MS§2.2)

**Contract name:** MS-CAP-01
**Source authority:** Master Spec §2.2
**Enforcement point:** `RegistryValidator` pre-publish gate (module 4, B2P05). Publish MUST be blocked if any required field is absent.

**Rule:** Every capability registration MUST provide all of the following fields. A definition missing any required field MUST be rejected at the validation gate and MUST NOT appear in any published snapshot.

| Required field | Constraint |
|---|---|
| `unique_key` | Immutable, globally unique. Stable naming pattern enforced. No shadow aliases. |
| `domain` | Owner domain declaring the capability. Required for governance and dependency resolution. |
| `dependencies` | Explicit list (empty `[]` is valid). All referenced keys must exist in the same or prior snapshot. |
| `usage_metrics` | At least one metric definition. Required for billing, quota, and operational observability. |
| `billing_type` | One of: `metered`, `included`, `add_on`, `non_monetizable`. Required for billing system integration. |
| `required_adapters` | Explicit adapter key list. May be `[]` only for capabilities with no external dependencies. |

**Why this rule exists:** Without complete definitions, the dependency graph becomes unreliable, billing integration fails silently, and adapter requirements are unknown at entitlement resolution time.

---

## Architectural Contract: MS-CAP-02 — Capability Validity Rule (MS§2.3)

**Contract name:** MS-CAP-02
**Source authority:** Master Spec §2.3
**Enforcement point:** `RegistryValidator` boundary validation layer (step 4 of the validation pipeline in B2P05). Constructs failing this test MUST be rejected with a descriptive error before any draft reaches snapshot state.

**Rule:** A construct is a valid capability if and only if ALL THREE conditions hold:

1. **Independently enable/disable** — activating or deactivating it does not force-activate or force-deactivate another capability as a side effect. (Declared dependencies are permitted; hard coupling is not.)
2. **Independently measurable** — it has at least one defined usage metric attributable solely to that capability.
3. **Reusable** — it is available to any eligible tenant; it is not a one-off configuration for a specific tenant.

**If any condition is false, the construct is NOT a valid capability.** It must instead be:
- a config parameter (behavioral variant of an existing capability), or
- an internal service concern (non-reusable implementation detail).

**Why this rule exists:** MS§2.3 defines this as the gatekeeping rule that prevents non-capability constructs from polluting the registry. Without it, one-off tenant configurations, inseparable feature bundles, and internal service details accumulate in the registry — undermining dependency graph integrity and billing traceability.

---

## References

- Master Spec §2
- `docs/architecture/B2P05_capability_registry_service_design.md` (full design — canonical)
- `docs/anchors/capability_resolution.md`
- `docs/qc/B7P01_capability_registry_validation_report.md` — PASS 10/10
