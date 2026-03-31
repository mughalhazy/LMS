# Capability Resolution Anchor (Canonical)

## Purpose
This anchor defines one unambiguous capability resolution flow across:
- `docs/architecture/B2P05_capability_registry_service_design.md` (capability definition source)
- `docs/architecture/B2P01_config_service_design.md` (config override resolution)
- `docs/architecture/B2P02_entitlement_service_design.md` (entitlement decisioning)

It standardizes terms, read responsibilities, evaluation timing, and final-state assembly.

---

## Canonical Terms

### 1) capability = definition
A **capability** is the canonical metadata definition of a platform feature unit, including identity and dependency contract.

Source of truth:
- Capability Registry snapshot (`B2P05`)

Includes:
- immutable key identity
- lifecycle metadata
- dependency references
- ownership metadata

Does **not** include:
- tenant allow/deny decisions
- resolved config values

### 2) config = overrides
A **config** is the effective runtime value set produced by deterministic hierarchy merge:

`global → country → segment → plan → tenant → runtime_override(optional)`

Source of truth:
- Config Service resolution output (`B2P01`)

Includes:
- key/value outcomes for runtime behavior tuning
- provenance (which layer won per key)

Does **not** include:
- capability identity authoring
- entitlement allow/deny rights

### 3) entitlement = decision
An **entitlement** is the deterministic allow/deny outcome for a tenant context over capability keys.

Source of truth:
- Entitlement Service decision output (`B2P02`)

Includes:
- capability state (`enabled|disabled`)
- reasons (policy/dependency/denial)
- snapshot references

Does **not** include:
- config merge logic
- capability schema/definition ownership

---

## Canonical Resolution Sequence

Required sequence:

`capability → config → entitlement → final_state`

### Step 1: capability (definition read)
- Reader: integration/orchestration layer or calling runtime service.
- Read target: Capability Registry (read-only, optionally snapshot pinned).
- Output: authoritative capability metadata and dependencies.
- Purpose: establish **what the capability is** and validate key existence.

### Step 2: config (override resolution)
- Reader: same request orchestrator/runtime service.
- Read target: Config Service `resolve*` APIs with tenant context.
- Output: effective config payload + provenance.
- Purpose: establish **how capability behavior should be parameterized**.

### Step 3: entitlement (decision)
- Reader: same request orchestrator/runtime service.
- Read target: Entitlement Service `resolve/isEnabled` APIs with normalized commercial context.
- Output: deterministic decision map and reasons.
- Purpose: establish **whether capability is allowed for this tenant context**.

### Step 4: final_state (assembly)
- Assembler: request orchestrator/runtime boundary (not registry/config/entitlement internals).
- Rule:
  - `final_state = ENABLED` only when:
    1. capability exists and is active in registry view,
    2. entitlement decision is `enabled`,
    3. required config for execution is resolvable (if capability is strict-config).
  - Otherwise `final_state = DISABLED` (or deterministic fail-closed outcome per caller policy).

---

## Who Reads What (Ownership Matrix)

| Concern | Owner system | Who reads it | Why |
|---|---|---|---|
| Capability identity + dependencies | Capability Registry (`B2P05`) | Entitlement service and runtime orchestrators | dependency checks + capability existence/lifecycle |
| Effective config overrides/provenance | Config Service (`B2P01`) | Runtime orchestrators/domain services | runtime parameterization |
| Allow/deny decision | Entitlement Service (`B2P02`) | Runtime orchestrators/domain services | access gating |
| Final execution state | Runtime orchestrator/domain boundary | Downstream executors | enforce behavior at call time |

Non-overlap rule:
- Registry never returns tenant decisions.
- Config never returns allow/deny decisions.
- Entitlement never resolves config layers.

---

## When Evaluation Happens

### Evaluation timing model
Evaluation happens at **runtime request/job/event boundary** for the active tenant context.

1. Normalize input context (`tenantId`, `country`, `segment`, `plan`, `addOns`, optional snapshot pins).
2. Read capability definition (registry).
3. Resolve effective config (config service).
4. Evaluate entitlement decision (entitlement service).
5. Assemble and enforce final state.

### Determinism requirements
- Fixed evaluation order is mandatory: capability → config → entitlement → final_state.
- Optional snapshot pins should be used for replay/debug parity.
- Output must carry versions/revisions sufficient for traceability.

### Re-evaluation triggers
Re-run full resolution when any of the following changes:
- tenant commercial context (plan/segment/country/add-ons)
- config revisions in applicable hierarchy layers
- capability registry snapshot/version
- policy snapshot/version for entitlement

---

## Final State Contract

```json
{
  "capability_key": "string",
  "capability_snapshot": "string",
  "config_revision_set": ["string"],
  "entitlement_snapshot": "string",
  "entitlement_state": "enabled|disabled",
  "final_state": "enabled|disabled",
  "reasons": ["string"],
  "evaluated_at": "ISO-8601 UTC"
}
```

Interpretation:
- `entitlement_state` communicates the entitlement engine result.
- `final_state` communicates enforceable runtime state after capability+config+entitlement assembly.

---

## QC + AUTO-FIX (Mandatory)

### Validation checklist
- [x] No overlap between systems.
- [x] Clear ownership for capability/config/entitlement/final assembly.
- [x] No ambiguity in term definitions.
- [x] Fixed and explicit evaluation timing + sequence.

### Score
**10/10**
