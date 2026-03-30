# B3P06 — Revenue Service (Tracking & Reporting)

## 1) Purpose and Scope

The Revenue Service provides a **read-optimized revenue tracking and reporting layer** for commerce operations.

It is explicitly limited to:

- revenue aggregation
- financial analytics (revenue-focused only)
- reporting

It is explicitly **not** responsible for:

- transaction execution (invoice creation, payment capture, refunds execution)
- billing data authoring or mutation
- generalized product analytics workloads

This service consumes authoritative billing + usage signals and builds derived revenue read models for fast reporting.

---

## 2) Design Principles (QC FIX RE QC 10/10)

1. **No overlap with analytics core**
   - Revenue Service covers finance-domain revenue reporting only.
   - Behavioral/product analytics stays in Analytics Core.

2. **No duplication of billing data**
   - Billing remains system of record for invoices, lines, taxes, adjustments, and payment state.
   - Revenue Service stores only projection keys and derived aggregates; no canonical billing copies.

3. **Read-optimized architecture**
   - Pre-aggregated tables/materialized views by tenant/capability/time.
   - Query APIs avoid expensive on-demand joins across transactional stores.

4. **Clear aggregation logic**
   - Deterministic pipeline from normalized revenue facts -> windowed aggregates.
   - Versioned formulas and rerunnable backfill jobs.

5. **Separation of reporting vs transactions**
   - Write path is event-driven ingestion only.
   - Transaction lifecycle remains in Billing and Payment services.

---

## 3) Bounded Context and Integrations

### 3.1 Upstream Integrations (Required)

1. **Billing (required)**
   - Source of financial transaction facts (invoice issued, credit memo, refund posted, write-off, payment settlement references).

2. **Usage Metering (required)**
   - Source of usage dimensions used for capability-level revenue allocation and earned-vs-deferred recognition drivers.

### 3.2 Downstream Consumers

- Finance dashboards
- Tenant admin reporting APIs
- Data warehouse export jobs
- Compliance/audit read pipelines

### 3.3 Ownership Boundaries

- **Billing owns:** transactional truth and mutation.
- **Usage Metering owns:** usage fact capture/aggregation.
- **Revenue Service owns:** derived revenue projections and reporting contracts.

---

## 4) High-Level Architecture

1. **Revenue Ingestion Gateway**
   - Consumes versioned events from Billing and Usage Metering.
   - Validates schema + idempotency keys.

2. **Revenue Fact Normalizer**
   - Converts upstream events into canonical `revenue_fact` records.
   - Resolves tenant and capability keys via references (no metadata duplication).

3. **Aggregation Engine**
   - Computes incremental rollups for hourly/daily/monthly windows.
   - Maintains both per-tenant and per-capability views.

4. **Reporting Store (Read Model DB)**
   - Columnar/OLAP-optimized projections and materialized summaries.

5. **Revenue Query API**
   - Read-only endpoints with filters by tenant, capability, period, and currency.

6. **Reporting Publisher**
   - Emits curated snapshots for warehouse and scheduled reports.

---

## 5) Canonical Revenue Fact Model

```json
{
  "fact_id": "uuid",
  "fact_type": "invoice_line_recognized|credit_applied|refund_recognized|deferred_revenue_change",
  "source": {
    "service": "billing-service|usage-metering-service",
    "event_id": "uuid",
    "event_version": "v1"
  },
  "tenant_id": "tenant_123",
  "capability_key": "ai.learning_copilot.chat_session",
  "billing_ref": {
    "invoice_id": "inv_001",
    "invoice_line_id": "line_01",
    "subscription_id": "sub_42"
  },
  "amount": {
    "currency": "USD",
    "gross": 100.00,
    "discount": 10.00,
    "net": 90.00
  },
  "recognition_window": {
    "start_at": "2026-03-01T00:00:00Z",
    "end_at": "2026-03-31T23:59:59Z"
  },
  "recognized_at": "2026-03-30T10:15:00Z",
  "allocation_basis": {
    "method": "usage_weighted|fixed_split|direct_mapping",
    "usage_metric_key": "request_count",
    "usage_quantity": 540
  },
  "ingested_at": "2026-03-30T10:16:00Z"
}
```

### Modeling Rules

- `invoice_id`/`invoice_line_id` are references only (no invoice payload copy).
- `capability_key` is required for capability reporting; unresolved facts are quarantined.
- Every fact carries formula version and source lineage for audit/replay.

---

## 6) Aggregation Logic (Clear + Deterministic)

### 6.1 Inputs

- Billing financial events (net positive/negative deltas).
- Usage aggregates used for allocation where invoice lines span multiple capabilities.

### 6.2 Allocation Methods

1. **Direct mapping**
   - Invoice line has explicit capability key -> 100% assigned.

2. **Fixed split**
   - Contracted ratios per capability (e.g., 70/30).

3. **Usage weighted**
   - Revenue distributed by capability usage share for the recognition window.

### 6.3 Core Formulas

- `recognized_revenue = Σ(net_amount_deltas recognized within window)`
- `deferred_revenue = billed_not_yet_recognized_balance`
- `tenant_revenue_daily = Σ recognized_revenue by tenant_id, day`
- `capability_revenue_daily = Σ recognized_revenue by capability_key, day`
- `tenant_capability_revenue_daily = Σ recognized_revenue by tenant_id + capability_key, day`

### 6.4 Correction Strategy

- Late events are ingested with event-time semantics.
- Affected windows are recomputed incrementally.
- All recomputations are idempotent and versioned (`aggregation_version`).

---

## 7) Reporting Model (Output)

### 7.1 Read-Optimized Tables

1. `revenue_tenant_daily`
   - dims: `tenant_id`, `date`, `currency`
   - measures: `recognized_revenue`, `deferred_revenue_delta`, `refund_delta`, `credit_delta`

2. `revenue_capability_daily`
   - dims: `capability_key`, `date`, `currency`
   - measures: `recognized_revenue`, `allocated_share_pct`, `refund_delta`

3. `revenue_tenant_capability_daily`
   - dims: `tenant_id`, `capability_key`, `date`, `currency`
   - measures: `recognized_revenue`, `usage_quantity_basis`, `allocation_method`

4. `revenue_tenant_monthly`
   - dims: `tenant_id`, `month`, `currency`
   - measures: `recognized_revenue`, `arr_proxy`, `mrr_proxy`, `net_retention_inputs`

5. `revenue_reporting_snapshot`
   - report-ready immutable snapshot by `as_of_date` for finance close processes.

### 7.2 Query Patterns Supported

- Per-tenant revenue trend (daily/monthly)
- Per-capability revenue contribution
- Tenant x capability matrix
- Revenue deltas (new, expansion, contraction, refunds)
- Deferred-to-recognized movement over time

### 7.3 Reporting API (Read-only)

- `GET /v1/revenue/tenants/{tenant_id}?from=&to=&granularity=day|month`
- `GET /v1/revenue/capabilities/{capability_key}?from=&to=&granularity=day|month`
- `GET /v1/revenue/tenant-capability?tenant_id=&capability_key=&from=&to=`
- `GET /v1/revenue/snapshots/{as_of_date}`

---

## 8) Data Storage and Performance

- Partition by date/month and optionally currency.
- Cluster/sort keys: (`tenant_id`, `date`) and (`capability_key`, `date`).
- Precompute top-N and period-to-date metrics.
- Cache hot tenant/capability queries.
- SLA target: < 500 ms p95 for common dashboard reads.

---

## 9) Separation from Analytics Core

To prevent overlap:

- Revenue Service publishes finance-specific curated datasets only.
- Analytics Core may consume those datasets but does not own revenue recognition logic.
- Cross-domain funnels/cohorts/behavior analytics remain outside this service.

---

## 10) Governance, Auditability, and Controls

- Full lineage: each aggregate row links to source fact IDs and aggregation version.
- Close-safe snapshots: immutable monthly close outputs.
- Reconciliation jobs:
  - Revenue aggregates vs billing ledger totals (by period/currency/tenant).
  - Allocation totals must equal source net revenue (within precision tolerance).
- Tenant isolation enforced in APIs and row-level security.

---

## 11) QC FIX Mapping (Requested)

1. **No overlap with analytics core**
   - Section 9 defines strict finance-only boundary and delegation of generic analytics.

2. **No duplication of billing data**
   - Sections 3 and 5 keep billing as source of truth; Revenue stores references + derived facts only.

3. **Read-optimized**
   - Sections 4, 7, and 8 provide pre-aggregated read models and performance-focused storage.

4. **Clear aggregation logic**
   - Section 6 specifies allocation methods, formulas, correction semantics, and versioning.

5. **Separation of reporting vs transactions**
   - Sections 1, 2, and 3 isolate reporting from transaction processing/mutations.

---

## Summary

The B3P06 Revenue Service is a dedicated, read-optimized finance reporting component that integrates with Billing and Usage Metering, supports per-tenant and per-capability revenue views, avoids transactional ownership overlap, and provides deterministic, auditable aggregation logic for operational and financial reporting.
