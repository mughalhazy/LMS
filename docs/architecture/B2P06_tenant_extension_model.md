# B2P06 — Tenant Extension Model

## Purpose
Define a lightweight tenant domain extension model that adds commercial and regional context fields while preserving strict separation from Config and Entitlement responsibilities.

This model extends tenant identity/profile metadata and provides stable inputs to downstream services.

---

## Design Principles (QC FIX RE QC 10/10)

1. **No overlap with Config Service**
   - Tenant model stores only tenant descriptors and selection inputs.
   - It does **not** store resolved configuration values, merge precedence state, or config decision logic.

2. **No duplication of Entitlement logic**
   - Tenant model stores plan/add-on declarations only.
   - It does **not** compute capability grants, dependency resolution, or allow/deny outcomes.

3. **Lightweight by default**
   - Keep extension fields compact and indexable.
   - Avoid embedding large policy/config blobs in tenant records.

4. **Scalable + isolated**
   - Tenant is partition key for reads/writes across services.
   - Tenant extension fields are immutable/slow-changing inputs suitable for caching and eventing.

5. **Clear tenant vs capability boundary**
   - Tenant = “who the customer is + commercial/regional context.”
   - Capability state = resolved externally by Entitlement service.

---

## Canonical Tenant Extension Fields

Required extension fields:
- `segment_type` (string)
- `country_code` (ISO 3166-1 alpha-2 string)
- `plan_type` (string)
- `enabled_addons` (array of string)

### Suggested constraints
- `segment_type`: enum-like controlled vocabulary (for example: `enterprise`, `smb`, `edu`, `government`).
- `country_code`: uppercase 2-letter code.
- `plan_type`: controlled plan key (for example: `starter`, `growth`, `pro`, `enterprise_plus`).
- `enabled_addons`: unique, sorted add-on keys to improve deterministic downstream processing.

---

## Data Model Design

## Logical entity: `Tenant`

```json
{
  "tenant_id": "string",
  "tenant_slug": "string",
  "display_name": "string",
  "status": "active|suspended|archived",
  "segment_type": "string",
  "country_code": "string",
  "plan_type": "string",
  "enabled_addons": ["string"],
  "created_at": "timestamp",
  "updated_at": "timestamp",
  "version": "number"
}
```

## Relational storage sketch

```sql
CREATE TABLE tenants (
  tenant_id        UUID PRIMARY KEY,
  tenant_slug      TEXT UNIQUE NOT NULL,
  display_name     TEXT NOT NULL,
  status           TEXT NOT NULL,
  segment_type     TEXT NOT NULL,
  country_code     CHAR(2) NOT NULL,
  plan_type        TEXT NOT NULL,
  enabled_addons   JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  version          BIGINT NOT NULL DEFAULT 1
);

CREATE INDEX idx_tenants_country_segment_plan
  ON tenants (country_code, segment_type, plan_type);
```

> Note: `enabled_addons` can be normalized into `tenant_addons(tenant_id, addon_key)` for high-cardinality querying. Keep inline JSON/array if query volume is low to remain lightweight.

---

## Multi-Tenant Isolation Model

- **Primary isolation key:** `tenant_id`.
- Every tenant-bound table in domain services must include `tenant_id` and enforce tenant-scoped filtering in repository/access layer.
- Service APIs must require tenant context (header/token/route) and never execute cross-tenant reads without explicit platform-admin path.
- Event contracts must carry `tenant_id` as a required envelope attribute.
- Caches should namespace keys by tenant (`tenant:{tenant_id}:...`).

This makes tenant extension fields portable context, while isolation remains enforced consistently by `tenant_id`.

---

## Integration Contracts

## 1) Integration with Config Service (input-only)

Tenant model provides context dimensions:
- `tenant_id`
- `country_code`
- `segment_type`
- `plan_type`

Config service uses these fields as read-time selectors for hierarchical resolution.

**Boundary:** Tenant service does not resolve or persist effective config values.

## 2) Integration with Entitlement Service (input-only)

Tenant model provides commercial context:
- `segment_type`
- `country_code`
- `plan_type`
- `enabled_addons`

Entitlement service evaluates capability decisions from these inputs.

**Boundary:** Tenant service does not evaluate capability activation, dependency, or policy precedence.

---

## Scalability Notes

- Extension fields are slow-moving dimensions; cache aggressively with short payloads.
- Publish `TenantProfileChanged` events only when extension fields change.
- Use optimistic concurrency (`version`) to prevent concurrent profile drift.
- For large add-on sets, move to normalized `tenant_addons` table to reduce JSON write amplification.

---

## Example Tenant Object

```json
{
  "tenant_id": "9f4a6c4d-8e7f-4f11-aaf9-4c26f1e3b8b2",
  "tenant_slug": "acme-learning-us",
  "display_name": "Acme Learning US",
  "status": "active",
  "segment_type": "enterprise",
  "country_code": "US",
  "plan_type": "growth",
  "enabled_addons": [
    "advanced_analytics",
    "sso_saml",
    "compliance_pack"
  ],
  "created_at": "2026-03-30T00:00:00Z",
  "updated_at": "2026-03-30T00:00:00Z",
  "version": 3
}
```

---

## Final Responsibility Split

- **Tenant extension model owns:** tenant profile + commercial/regional descriptors.
- **Config service owns:** config hierarchy resolution and effective value retrieval.
- **Entitlement service owns:** capability enablement/denial decisioning.

This preserves lightweight tenant records and clean service boundaries at scale.
