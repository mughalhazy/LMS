# B2P05 — Capability Registry Service Design

## Purpose
Design a capability registry service that is the **single source of truth** for capability metadata and dependency relationships.

The service stores and serves capability definitions and supports:
- dependency mapping,
- capability lookup,
- registry validation.

It integrates with the entitlement system through read-only registry access contracts and event notifications, while keeping entitlement decision logic out of registry internals.

---

## Scope and Non-Goals (QC Alignment)

### In scope
- Authoritative storage of capability records and dependency graph metadata.
- Read APIs for direct capability lookup and bulk graph retrieval.
- Validation of capability metadata and graph integrity before publish.
- Versioned snapshots for deterministic downstream consumption.
- Read-side integration contract for entitlement consumers.

### Out of scope
- Entitlement resolution, allow/deny decisions, or policy evaluation.
- Config layering, merge precedence, or config payload retrieval.
- Runtime feature execution and service-specific behavior wiring.
- Commercial packaging/pricing authoring.

### Explicit QC guarantees
- **No overlap with entitlement or config logic:** registry only manages capability metadata + dependency topology.
- **No duplication of capability schema:** canonical schema remains `docs/architecture/schemas/capability_registry.schema.json`; service validates against it, never forks it.
- **Single source of truth:** all capability reads resolve from registry snapshots/versions emitted by this service.
- **Supports dynamic expansion:** new capabilities/edges can be added via versioned publish workflow without redesign.
- **Clear capability boundaries:** each capability has immutable key identity, owner domain, dependency contract, and lifecycle metadata.

---

## Service Design (Modules + Responsibilities)

## 1) `CapabilityRegistryAPI`
**Responsibility:** External interface for read/write lifecycle operations.

- `getCapability(key, snapshotVersion?)`
- `listCapabilities(filter?, snapshotVersion?)`
- `getDependencyGraph(snapshotVersion?)`
- `publishDraft(draftId)` (admin/governed write path)
- `getSnapshot(version)`
- Exposes only registry metadata operations.
- Never evaluates tenant entitlement.

## 2) `CapabilityCatalogStore`
**Responsibility:** Persistent storage of capability records.

- Stores normalized capability documents keyed by `capability.key`.
- Keeps immutable historical snapshots and mutable draft workspace.
- Supports optimistic concurrency/version checks for governed updates.
- Retains provenance (`createdBy`, `updatedBy`, `changeReason`, timestamps).

## 3) `DependencyGraphIndex`
**Responsibility:** Query-optimized dependency mapping.

- Materializes adjacency lists and reverse edges from canonical capability documents.
- Supports:
  - direct dependencies (`A -> B`),
  - transitive closure lookup,
  - reverse-impact queries (`who depends on X`).
- Rebuilds atomically per published snapshot to avoid partial graph states.

## 4) `RegistryValidator`
**Responsibility:** Pre-publish validation gate.

Validation layers:
1. **Schema validation** against canonical capability registry schema.
2. **Identity validation** (unique keys, stable naming pattern, no shadow aliases).
3. **Dependency validation**:
   - all dependency keys must exist,
   - no self-dependency,
   - cycle detection and rejection,
   - optional max-depth policy checks.
4. **Boundary validation**:
   - required domain ownership metadata present,
   - activation metadata complete,
   - add-on compatibility references valid.
5. **MS-CAP-01 completeness check** (MS§2.2): all six required fields (`unique_key`, `domain`, `dependencies`, `usage_metrics`, `billing_type`, `required_adapters`) must be present and non-null. See `capability_registry_service_spec.md` MS-CAP-01 for the full field contract.
6. **MS-CAP-02 validity check** (MS§2.3): capability must satisfy all three validity conditions: independently enable/disable, independently measurable, reusable. Constructs failing this check must be rejected with a descriptive error. See `capability_registry_service_spec.md` MS-CAP-02 for the full rule.

Publish is blocked on any failed validation.

## 5) `SnapshotManager`
**Responsibility:** Deterministic, versioned registry release.

- Creates immutable snapshot IDs (e.g., `registry-v2026.03.30.001`).
- Produces reproducible canonical serialization (stable key ordering).
- Supports snapshot pinning for consumers that require deterministic replay.
- Maintains `current` pointer and previous-pointer rollback target.

## 6) `EntitlementRegistryReaderPort` (integration boundary)
**Responsibility:** Read-only contract for entitlement system integration.

- `fetchCapability(key, snapshotVersion?)`
- `fetchDependencies(key, snapshotVersion?)`
- `fetchSnapshotMetadata(snapshotVersion?)`
- Guarantees read-only access with explicit snapshot/version semantics.
- Does not expose mutation operations to entitlement service.

## 7) `RegistryChangeEmitter`
**Responsibility:** Notify dependent systems of registry changes.

- Emits events such as:
  - `capability_registry.snapshot_published.v1`
  - `capability_registry.snapshot_rolled_back.v1`
  - `capability_registry.validation_failed.v1`
- Payload includes snapshot version, change scope, and integrity digest.
- Consumers (including entitlement system) rehydrate caches based on events.

## 8) `AccessControlAndGovernance`
**Responsibility:** Separate governance from registry content model.

- Enforces write-role controls for draft edits/publish operations.
- Requires validation + approval workflow before publish.
- Preserves audit trail for compliance and incident analysis.
- Keeps governance metadata outside capability schema fields.

---

## Canonical Boundaries (Registry vs Entitlement vs Config)

- **Capability Registry Service owns:** capability metadata, dependency graph, snapshot/version lifecycle, and registry validation.
- **Entitlement Service owns:** tenant-context capability decisions (`enabled/disabled`) using registry as read-only metadata input.
- **Config Service owns:** runtime config values and hierarchy resolution.

Boundary rule: registry answers **"what is a capability and what it depends on"**.
It does not answer **"is this tenant allowed"** (entitlement) or **"what value should runtime use"** (config).

---

## Data Model Strategy (No Schema Duplication)

- The canonical schema is external and authoritative:  
  `docs/architecture/schemas/capability_registry.schema.json`
- Registry service stores canonical documents that conform to that schema.
- Service-specific operational data is maintained in separate internal tables/collections, for example:
  - `registry_drafts` (workflow state),
  - `registry_snapshots` (version index + digest),
  - `registry_audit_log` (change trail),
  - `dependency_index` (read optimization).

This preserves one capability schema while still enabling operational scale.

---

## Registry Access Flow

## A) Read flow (lookup + dependency mapping)
1. Caller requests capability or graph (`key`, optional `snapshotVersion`).
2. `CapabilityRegistryAPI` resolves effective version:
   - explicit pinned snapshot if provided,
   - otherwise current published snapshot.
3. `CapabilityCatalogStore` returns capability document(s).
4. `DependencyGraphIndex` returns direct/transitive/reverse dependency mapping as requested.
5. API returns payload with:
   - capability metadata,
   - dependency results,
   - `snapshotVersion`,
   - integrity digest/checksum.

## B) Publish flow (validation + dynamic expansion)
1. Registry admin submits draft changes (add/update/deprecate capabilities).
2. `RegistryValidator` executes schema + graph + boundary validation.
3. If validation fails: reject publish and emit `validation_failed` event.
4. If validation passes:
   - `SnapshotManager` generates immutable snapshot,
   - `DependencyGraphIndex` atomically rebuilds for that snapshot,
   - `current` pointer advances.
5. `RegistryChangeEmitter` emits snapshot-published event.
6. Entitlement service receives event and refreshes read cache/pins as needed.

## C) Entitlement integration flow (read-only)
1. Entitlement resolver starts decision evaluation.
2. It calls `EntitlementRegistryReaderPort` with optional `registrySnapshotVersion` pin.
3. Registry returns capability metadata + dependencies for requested keys.
4. Entitlement applies its own decision logic using returned metadata.
5. Registry remains stateless regarding tenant decision outcomes.

---

## Dynamic Expansion Model

The registry supports expansion without schema duplication or boundary drift:
- New capability introduction via draft -> validation -> snapshot publish.
- Dependency graph evolves by adding/removing dependency edges in capability metadata.
- Consumers can adopt new snapshots immediately or remain pinned for deterministic behavior.
- Deprecation handled through lifecycle metadata and governed migration windows.

This allows continuous capability growth while maintaining a single authoritative metadata plane.

---

## QC FIX Mapping (Requested)
- **No overlap with entitlement or config logic:** explicit service boundary limits registry to metadata/graph only.
- **No duplication of capability schema:** canonical external schema is referenced and enforced, not redefined.
- **Single source of truth:** immutable published snapshots serve all consumers.
- **Dynamic expansion:** versioned draft/publish model supports additive growth safely.
- **Clear capability boundaries:** identity, ownership domain, dependency contract, lifecycle metadata are mandatory and validated.
