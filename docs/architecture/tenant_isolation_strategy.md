# Multi-Tenant Isolation Strategy

## 1) Shared DB (shared schema, tenant_id per row)

**strategy**
Use a single database and shared tables for all tenants, with every tenant-owned row tagged by `tenant_id` and filtered in every query.

**pros**
- Lowest infrastructure and operations cost.
- Simplest provisioning/onboarding for new tenants.
- Easier cross-tenant analytics and reporting.
- High resource utilization (pooled compute/storage).

**cons**
- Weakest isolation model; application bugs can cause tenant data leakage.
- More complex access-control discipline (strict row-level filtering everywhere).
- Noisy-neighbor risk under uneven workloads.
- Harder to satisfy strict compliance/isolation requirements.

**recommended_use**
Best for early-stage SaaS, many small tenants, cost-sensitive products, and workloads with moderate compliance requirements when strong application-level isolation controls exist.

---

## 2) Schema per Tenant (shared DB instance, separate schemas)

**strategy**
Use one database instance, but create a dedicated schema per tenant. Tables are duplicated per schema, and application routing selects the tenant schema.

**pros**
- Stronger logical isolation than shared-schema.
- Lower leakage risk from accidental cross-tenant queries.
- Tenant-level backup/restore and migrations are more targeted.
- Better balance of cost vs. isolation.

**cons**
- Operational complexity grows with tenant count (migrations across many schemas).
- Connection pooling and schema routing require careful engineering.
- Still shares underlying compute/storage, so noisy neighbors remain possible.
- Harder at very high tenant scale (schema sprawl).

**recommended_use**
Best for mid-scale B2B SaaS where moderate-to-strong isolation is needed without paying full cost of per-database tenancy.

---

## 3) Database per Tenant

**strategy**
Provision a separate database (or cluster) for each tenant; application routes tenant traffic to the tenant-specific database.

**pros**
- Strongest isolation for security and compliance.
- Minimal blast radius for failures or performance spikes.
- Clear tenant-level backup, restore, encryption, and lifecycle controls.
- Supports tenant-specific customizations and upgrade cadence.

**cons**
- Highest infrastructure cost.
- Significant operational overhead (provisioning, patching, monitoring, migrations).
- More complex fleet automation and observability.
- Cross-tenant analytics require ETL/federation.

**recommended_use**
Best for enterprise/high-compliance tenants (e.g., regulated industries), large contracts, strict data residency demands, or high-value tenants requiring dedicated performance/isolation.

---

## Practical Recommendation

Adopt a **tiered model**:
- Default to **schema-per-tenant** for most customers.
- Offer **database-per-tenant** for premium/regulatory tiers.
- Reserve **shared-schema** only for low-risk, low-sensitivity, cost-focused segments.

This hybrid approach optimizes cost while preserving a clear path to stronger isolation as tenant requirements mature.
