# DOC_07 Billing and Usage Model

## 1) Usage metric definitions

| Metric | Unit | Measurement window | Source of truth | Deduplication key | Notes |
|---|---|---|---|---|---|
| `ai_calls` | successful model invocation count | hourly rollup, monthly invoice | AI Gateway usage event stream | `tenant_id + request_id + model + event_ts_bucket` | Count only billable responses (HTTP 2xx/3xx and non-cached completion). Retries are non-billable when `retry_of_request_id` is set. |
| `api_calls` | billable API request count | hourly rollup, monthly invoice | API Gateway access log topic | `tenant_id + request_id + route + method` | Count externally initiated API requests. Exclude health checks, auth token refresh, and internal service-to-service calls with `internal=true`. |
| `active_learners` | monthly active unique learners (MAU) | calendar month | Identity + activity events | `tenant_id + learner_id + month` | Learner is active if they generate at least one qualifying learning event (lesson start, assessment submit, content completion) in month. |
| `content_storage_gb` | GB-month (binary GiB normalized to GB billable unit) | daily snapshot averaged across month | Object storage inventory + metadata DB | `tenant_id + object_id + snapshot_date` | Billable bytes include primary objects + versioned artifacts retained beyond grace window; exclude transient processing artifacts under 24h TTL. |
| `analytics_processing_credits` | compute credits | near-real-time event tally, monthly invoice | Analytics job orchestrator + warehouse query logs | `tenant_id + job_run_id + pipeline_stage` | 1 credit = standardized compute slice (e.g., 1 vCPU-minute equivalent). Includes scheduled dashboards and ad hoc heavy queries above free threshold. |

### Capability gating linkage

Each metered metric maps to entitlement gates used at request time:

- `ai_calls` -> `capability.ai_assistant` and plan quota `quota.ai_calls_monthly`.
- `api_calls` -> `capability.public_api` and `rate_limit.api_rps`.
- `active_learners` -> `capability.learner_seats` and overage policy.
- `content_storage_gb` -> `capability.content_repo` and storage tier limit.
- `analytics_processing_credits` -> `capability.advanced_analytics` and compute budget.

If capability is disabled, events are still recorded with `billable=false` and `blocked_reason`, enabling auditability and upsell analytics.

## 2) Billing architecture

### 2.1 Usage tracking

1. **Emit meter events** from AI gateway, API gateway, LMS activity service, storage inventory scanner, and analytics orchestrator.
2. **Normalize** events through a metering ingestion service (schema validation, timestamp normalization to UTC, tenant enforcement).
3. **Idempotency guard** writes events into an append-only ledger with dedupe key hash.
4. **Late-arrival handling** allows corrections up to `T+7 days` with adjustment entries (never hard-update original records).

### 2.2 Billing aggregation

1. Hourly streaming aggregates per tenant + metric for operational dashboards.
2. Daily reconciliation compares stream aggregates against source-of-truth batch extracts.
3. Monthly rating engine applies pricing rules, free tiers, committed-use credits, and discounts.
4. Final invoice line items are generated from immutable rated usage snapshots.

### 2.3 Tenant billing records

Per tenant, maintain:

- `billing_account` (currency, tax profile, payment terms).
- `plan_subscription` (effective dates, included units, negotiated rates).
- `usage_ledger` (raw + adjusted events).
- `rated_usage` (unit price applied per metric, pre-tax subtotal).
- `invoice` and `invoice_line_item` records with trace links back to usage ledger IDs.

### 2.4 Pay-as-you-go pricing model

- **Base subscription** includes platform access + included usage buckets.
- **Overage** billed per measured unit above included usage.
- **Pure PAYG tenants** skip included buckets and pay unit price from first unit.
- **Volume tiers** evaluated monthly by total units per metric and applied progressively.
- **Regional pricing** derived from tenant billing country and contract currency. *(Implementation note: regional pricing rules are stored in the config service's country_profile layer and resolved via the config resolution chain — they are not hardcoded inside the billing service. See `docs/architecture/B2P01_config_service_design.md` and Master Spec §1.5.)*

## 3) Billing calculation rules

For tenant `T` and metric `M` in billing month `B`:

1. `gross_units(T,M,B) = sum(billable usage ledger units)`.
2. `included_units(T,M,B) = plan allowance prorated by active subscription days`.
3. `net_units(T,M,B) = max(0, gross_units - included_units - promotional_credits_units)`.
4. Apply tiered rating:
   - `tier_charge = sum_over_tiers(units_in_tier * tier_unit_price)`.
5. Apply committed-use discount (if contract exists):
   - `discounted_charge = tier_charge - committed_discount_amount`.
6. Apply minimum monthly spend floor:
   - `final_metric_charge = max(discounted_charge, metric_minimum_charge)`.
7. Invoice subtotal:
   - `invoice_subtotal = sum(final_metric_charge for all metrics) + base_subscription_fee`.
8. Taxes and final total:
   - `invoice_total = invoice_subtotal + tax(invoice_subtotal, tenant_tax_profile)`.

### Financial accuracy controls

- Monetary values stored as integer minor units (e.g., cents) to avoid floating-point drift.
- Every adjustment is a compensating entry with reference to original ledger event.
- Month-close process locks rated usage snapshot via checksum and version ID.
- Re-rating requires explicit `rerate_run_id` and creates delta line items only.

## 4) Billing event schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BillingUsageEvent",
  "type": "object",
  "required": [
    "event_id",
    "event_version",
    "event_ts",
    "tenant_id",
    "metric",
    "units",
    "unit_type",
    "source_service",
    "billable",
    "idempotency_key"
  ],
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_version": { "type": "integer", "minimum": 1 },
    "event_ts": { "type": "string", "format": "date-time" },
    "ingested_ts": { "type": "string", "format": "date-time" },
    "tenant_id": { "type": "string", "minLength": 1 },
    "account_id": { "type": "string" },
    "metric": {
      "type": "string",
      "enum": [
        "ai_calls",
        "api_calls",
        "active_learners",
        "content_storage_gb",
        "analytics_processing_credits"
      ]
    },
    "units": { "type": "number", "minimum": 0 },
    "unit_type": {
      "type": "string",
      "enum": ["count", "gb_month", "credits", "mau"]
    },
    "billable": { "type": "boolean" },
    "blocked_reason": { "type": "string" },
    "capability_key": { "type": "string" },
    "source_service": { "type": "string" },
    "resource_id": { "type": "string" },
    "request_id": { "type": "string" },
    "retry_of_request_id": { "type": "string" },
    "idempotency_key": { "type": "string", "minLength": 8 },
    "cost_hint_minor": { "type": "integer", "minimum": 0 },
    "currency": { "type": "string", "pattern": "^[A-Z]{3}$" },
    "tags": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

## 5) QC loop

### QC iteration 1

| Category | Score (1-10) | Finding |
|---|---:|---|
| Billing measurability | 10 | All metrics have units, source, and dedupe strategy. |
| Integration with capability gating | 8 | Gating linkage defined, but blocked usage treatment not explicit in invoice logic. |
| Financial accuracy | 9 | Accuracy controls exist, but rerating delta handling needed in formula section. |
| Platform scalability | 9 | Streaming + batch present, but late-arrival handling lacked explicit correction window policy. |

**Flaws identified**

1. Missing explicit treatment for `billable=false` gated events in rated usage.
2. Rerating delta behavior insufficiently formalized.
3. Late-arrival correction window not clearly codified.

**Corrections applied**

- Added capability-gating rule: blocked events recorded but excluded from `gross_units`.
- Added explicit `rerate_run_id` delta-only re-rating control.
- Added `T+7 days` late-arrival correction policy with compensating entries.

### QC iteration 2 (post-correction)

| Category | Score (1-10) | Validation outcome |
|---|---:|---|
| Billing measurability | 10 | Deterministic meter definitions and idempotent event design ensure precise measurement. |
| Integration with capability gating | 10 | Capability checks now integrated with billable flag semantics and auditability. |
| Financial accuracy | 10 | Integer money handling, immutable snapshots, and controlled rerating ensure accounting integrity. |
| Platform scalability | 10 | Stream + batch hybrid with correction window and append-only ledger supports scale and resilience. |

**QC status: all categories = 10/10.**

---

## 5) Free Entry Tier (Normalisation Addition — 2026-04-04)

Per Master Spec §9: the system must support free entry as the base monetization tier.

### Definition

**Free Entry** = `plan_type: free`

- Zero commercial entitlements — only core platform capabilities enabled
- No payment required to access the platform
- Upgrade path: entitlement change from `plan_type: free` to a paid plan — no re-deployment or migration required

### Free Tier Capability Bundle

The free tier activates the minimum capability set required to demonstrate platform value:

| Capability | Free tier limit |
|---|---|
| `CAP-COURSE-LESSON` | Enabled (read-only catalog) |
| `CAP-ENROLL-PROGRESS` | Enabled (up to config-defined learner cap) |
| `CAP-NOTIFICATIONS-GENERIC` | Enabled (in-app only) |
| `CAP-ANALYTICS-BASIC` | Disabled |
| All commerce capabilities | Disabled |
| All AI capabilities | Disabled |

Exact capability bundle for `plan_type: free` is defined in the capability registry and config store — not hardcoded here.

### Upgrade Trigger

When a tenant upgrades from free to a paid plan:
1. `plan_type` is updated on the Tenant record
2. Entitlement service re-evaluates all capabilities for the new plan
3. New capabilities become active without service restart or data migration
4. Usage metering begins from the upgrade timestamp

### References

- Master Spec §9
- `docs/architecture/B2P02_entitlement_service_design.md`
- `docs/architecture/B2P05_capability_registry_service_design.md`

---

---

## Architectural Contract: MS-MONETIZE-01 — Free Entry + Capability Upgrade (MS§9)

**Contract name:** MS-MONETIZE-01
**Source authority:** Master Spec §9: free entry must be possible; upgrades are capability-based; revenue scales with capability usage.

**Rule — three mandatory requirements:**

1. **The platform MUST always have a zero-cost entry point.** A `plan_type: free` tier must exist at all times. It must be possible to create a fully functional tenant (able to enroll learners and deliver content) without any payment. The free tier may be limited in capacity but must never be removed or gated behind registration fees.

2. **No capability may be gated by geography.** A capability available to one country's tenants must be available to all countries' tenants who activate the same plan/add-on. Country code is a config discriminator (per MS-CONFIG-01), not an entitlement denial condition. A tenant in one market must not be offered a capability that a same-tier tenant in another market cannot access.

3. **All commercial growth paths MUST flow through capability activation.** Upgrades are achieved by: changing `plan_type` on the Tenant record, or activating an `add_on` capability. No upgrade path may require: a geography-based unlock, a re-deployment, a data migration, or a manual configuration step outside the entitlement system. A tenant that upgrades from free to paid must have new capabilities active without any intervention beyond plan change.

**Upgrade flow (required mechanics):**
1. `plan_type` updated on Tenant record.
2. Entitlement service re-evaluates all capabilities for the new plan.
3. New capabilities become active without service restart or data migration.
4. Usage metering begins from the upgrade timestamp.

**What a violation looks like:**
- Removing the free tier to force all tenants onto paid plans.
- Offering a capability to UK tenants but blocking it for Pakistani tenants on the same plan.
- Requiring a support ticket or manual step to activate a capability that should activate on plan upgrade.

**Why this rule exists:** MS§9 states the platform must support free entry and capability-based upgrades. Without a named contract, commercial pressure can erode the free tier, geographic discrimination can emerge in capability access, and upgrade paths can drift toward manual processes.

---

## 6) Behavioral Contract — Contextual Upsell (BOS Overlay — 2026-04-04)

### BC-BILLING-01 — Contextual Upsell Behavioral Rule (BOS§8.2 / GAP-014)

**Rule:** Upgrade prompts MUST appear precisely when a user's action reveals a natural need for a higher-tier capability — not on a schedule, not on login, and not as unsolicited banners.

**Specification:**
- The `billable=false` gated-usage events already recorded by this service (Section 1, capability gating linkage) must serve as the trigger mechanism for contextual upsell — the data already exists; this contract defines the behavioral rule for when to act on it.
- Upsell triggers are defined per capability:

| Capability Hit | Upsell Trigger Condition | Upsell Message Example |
|---|---|---|
| `capability.ai_assistant` (quota exceeded) | User attempts AI action, blocked by quota | "Enable more AI sessions to keep pace → Upgrade AI Add-on" |
| `capability.advanced_analytics` (gated) | Admin tries to access a report, capability disabled | "This report requires Analytics Pro → Upgrade to unlock" |
| `capability.learner_seats` (at 90% of limit) | Admin enrolls learner, approaching seat cap | "You've used 90% of your learner seats → Expand your plan before enrolment stops" |
| Any automation capability (gated) | Admin manually performs a task that could be automated | "Enable auto-reminders to automate this → [Upgrade]" |

**Behavioral rules:**
- Upsell messages must appear in the same surface where the user hit the limit — not redirect them elsewhere.
- Upsell messages must be dismissable with one action — they must never block the current workflow.
- The same upsell trigger must not fire more than once per 24 hours for the same user and capability (de-duplication required).
- Upsell triggers are config-driven — thresholds and messages are stored in config service, not hardcoded.
