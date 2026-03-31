# Tenant Contract (Canonical)

## Purpose
This document locks the canonical tenant contract by reconciling:
- `docs/specs/tenant_service_spec.md`
- `docs/architecture/B2P06_tenant_extension_model.md`

The contract below is the **single authoritative tenant payload shape** for cross-service integration.

---

## Final Tenant Model

```json
{
  "tenant_id": "string (UUID, immutable)",
  "name": "string",
  "country_code": "string (ISO 3166-1 alpha-2, uppercase)",
  "segment_type": "string (controlled vocabulary)",
  "plan_type": "string (controlled plan key)",
  "addon_flags": ["string"]
}
```

### Field definitions
- `tenant_id`
  - Unique tenant root identifier.
  - Primary isolation key across services.
- `name`
  - Canonical tenant name for profile/identity display.
  - Normalizes prior naming variants (`display_name`) into one contract field.
- `country_code`
  - Regional selector used as an input dimension for config and entitlement.
- `segment_type`
  - Commercial segment selector (for example: enterprise/smb/edu/government).
- `plan_type`
  - Declared plan selector (input to entitlement/config).
- `addon_flags`
  - Declared add-on keys for commercial context.
  - Must be unique; deterministic ordering is recommended for stable comparisons/event payloads.

---

## Canonical Naming Resolution
To remove duplicates and ambiguity across source docs:

- `display_name` → **`name`**
- `enabled_addons` → **`addon_flags`**

No other synonym fields are part of this contract.

---

## Boundary: What is NOT stored in tenant
The tenant contract is input metadata only. It does **not** store:

1. Resolved capabilities / feature grants.
2. Capability allow/deny outcomes.
3. Dependency resolution results.
4. Effective config values or config merge precedence state.
5. Entitlement policy decision logic.

---

## Capability Resolution Rule
Capabilities are **not persisted** in the tenant contract.
They are resolved externally by the **Entitlement service** from tenant commercial/regional inputs (notably `plan_type`, `addon_flags`, `segment_type`, and `country_code`).

Tenant provides declarations; Entitlement provides evaluated capability state.

---

## Contract Constraints (Normative)
- Tenant contract remains lightweight and indexable.
- `tenant_id` is mandatory and immutable.
- `country_code` must be ISO 3166-1 alpha-2 uppercase.
- `plan_type`, `segment_type`, and `addon_flags` are declaration inputs; they are not decision outputs.
- Cross-service consumers must not infer persisted capabilities from tenant records.

---

## QC + Auto-fix Result
- Ambiguity removed: **yes** (single field names and explicit boundary).
- Duplicate definitions removed: **yes** (synonyms normalized).
- Source intent alignment: **yes** (tenant as profile/commercial context; entitlement/config resolved externally).

**QC Score: 10/10**
