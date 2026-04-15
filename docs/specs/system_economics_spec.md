# System Economics Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.15

---

## Capability Domain: §5.15 Economic Capabilities (System Level)

Covers: revenue analytics | cost tracking | profitability insights

---

## Scope

System-level economic capabilities provide the platform operator with financial intelligence across all tenants: total revenue, cost of serving each tenant, and profitability by capability/tenant/cohort. B3P06 covers revenue analytics — this spec supplements with cost tracking and profitability.

---

## Capabilities Defined

### CAP-REVENUE-ANALYTICS
- Revenue aggregation and reporting across all tenants, capabilities, and time periods
- **Already documented in:** `docs/architecture/B3P06_revenue_service_design.md`
- Service: `services/analytics-service/`

### CAP-COST-TRACKING
- Tracks infrastructure and operational costs attributable to platform operation:
  - Compute costs per service (from observability + cloud billing)
  - AI model call costs (from usage metering — `ai_calls` metric)
  - Storage costs (from usage metering — `content_storage_gb` metric)
  - Analytics compute costs (from usage metering — `analytics_processing_credits`)
- Owner: `services/analytics-service/` (to be extended)
- Data input: usage metering events, cloud cost exports
- Shared model: `shared/models/usage_record.py`

### CAP-PROFITABILITY-INSIGHTS
- Derived metric: revenue per tenant minus attributable platform costs = tenant profitability
- Supports: capability-level profitability (which capabilities generate the most net value), cohort profitability
- Owner: `services/analytics-service/`
- Visualisation: `services/operations-os/` (admin dashboard layer)

---

## Boundary Rules

- Cost tracking reads from infrastructure and metering systems — it never writes to billing records
- Profitability is a derived analytical metric — it has no transactional authority
- All cost and profitability data is tenant-scoped and requires admin entitlement to access

---

## References

- Master Spec §5.15
- `docs/architecture/B3P06_revenue_service_design.md` (revenue analytics)
- `docs/specs/DOC_07_billing_and_usage_model.md` (metering definitions)
- `docs/architecture/B2P04_usage_metering_service_design.md`

---

## Behavioral Contracts (BOS Overlay — 2026-04-04)

### BC-ECON-01 — Insight-to-Action Conversion for Economics (BOS§10.2 / GAP-016)

**Rule:** Every economic insight surfaced by the system MUST carry an embedded suggested action. Economic metrics must never be presented without a next step.

**Specification:**
- CAP-PROFITABILITY-INSIGHTS, CAP-COST-TRACKING, and CAP-REVENUE-ANALYTICS outputs for operator-facing views must follow the insight envelope format (see BC-ANALYTICS-01 in `analytics_service_spec.md`).
- For economic insights specifically, the suggested action must be executable or navigable:

| Economic Insight | Required Suggested Action |
|---|---|
| Revenue down vs last period | "Review courses with declining enrollment → [link]" |
| High-cost capability with low uptake | "Consider downgrading or removing [capability] → [link]" |
| Profitability below threshold for tenant | "Review pricing or costs for [tenant] → [link]" |
| Instructor payout overdue | "Initiate payout for [N] instructors → [action]" |

- The operations-os service (not the economics service) is responsible for surfacing these insights in operator-facing flows — the economics service provides the data + suggested action payload; operations-os delivers it.
