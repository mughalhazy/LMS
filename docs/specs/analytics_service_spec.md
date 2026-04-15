# Analytics Service Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.16 | **Service:** `services/analytics-service/`

---

## Capability Domain: §5.16 Data & Analytics Capabilities

Covers: performance analytics | benchmarking | ranking systems | optimisation insights

---

## Service Boundary

The analytics service is the platform's primary intelligence layer for learning and operational performance. It consumes events from all domain services and produces read-optimised projections for dashboards, reports, and AI feature inputs.

---

## Capabilities Defined

### CAP-LEARNING-ANALYTICS
- Learner progress, engagement, completion rate, and assessment performance analytics
- Inputs: progress events, assessment events, enrollment events
- Outputs: learner dashboards, cohort reports, at-risk signals
- Spec ref: `docs/specs/learning_analytics_spec.md`

### CAP-PERFORMANCE-BENCHMARKING
- Cross-cohort and cross-tenant benchmarking (within entitlement scope)
- Ranking of learners, instructors, courses by configurable KPIs
- Shared model: `shared/models/network_analytics.py`

### CAP-OPTIMISATION-INSIGHTS
- AI-assisted insights: content quality signals, learning path optimisation, intervention recommendations
- Integrates with: `B6P03` (recommendation engine), `B6P04` (learner risk)

### CAP-EXECUTIVE-REPORTING
- Tenant-level, academy-level, and cohort-level reporting
- Export and BI connector support
- Spec ref: `docs/specs/reporting_spec.md`

---

## Service Files

- `services/analytics-service/service.py`
- `services/analytics-service/models.py`
- `services/analytics-service/test_learning_optimization_insights.py`
- `services/analytics-service/test_models_integration.py`

---

## References

- Master Spec §5.16
- `docs/architecture/B6P01`–`B6P05`
- `docs/specs/learning_analytics_spec.md`
- `docs/specs/reporting_spec.md`
- `docs/data/analytics_data_model.md`

---

## Behavioral Contracts (BOS Overlay — 2026-04-04)

### BC-ANALYTICS-01 — Insights Over Reports (BOS§13.1 / GAP-012)

**Rule:** The analytics service MUST produce insights as its primary output — not raw data or static reports. Every analytics output must be actionable, contextualized, and directly linked to a suggested next step.

**Specification:**
- The distinction between a report and an insight:
  - **Report:** "Completion rate this month: 62%"
  - **Insight:** "Completion rate dropped 14% vs last month. 3 courses account for 80% of dropoffs → Review content quality on those courses?"
- All CAP-LEARNING-ANALYTICS and CAP-EXECUTIVE-REPORTING outputs must be wrapped in an insight envelope that includes: trend context, comparative context, and at least one suggested action.
- The analytics service must not expose raw metric values to operator-facing surfaces without contextualization.
- Raw data export (BI feeds, CSV exports) is permitted for data warehouse / finance use cases and is exempt from this rule — it is not an operator-facing surface.

**Required insight envelope:**
```json
{
  "metric": "completion_rate",
  "current_value": 0.62,
  "trend": "down_14pct_vs_last_month",
  "context": "3 courses account for 80% of dropoffs",
  "suggested_action": "Review content quality on: [course list]",
  "action_link": "/courses?filter=high_dropoff"
}
```

---

### BC-ANALYTICS-02 — Comparative Context as Default Framing (BOS§13.2 / GAP-013)

**Rule:** Every metric surfaced to users by the analytics service MUST include a comparative reference by default. Metrics without comparative context MUST NOT be surfaced to operator-facing views.

**Specification:**
- Every metric value must be accompanied by at least one of:
  - Trend comparison: vs prior period (week/month/quarter)
  - Cohort comparison: vs other batches/courses in the same tenant
  - Benchmark: vs platform average (where tenant-scoped anonymised benchmarking is enabled)
- CAP-PERFORMANCE-BENCHMARKING (currently defined as an opt-in capability) must be the DEFAULT comparative reference for all dashboard metrics — not a separate capability that requires activation.
- The absence of comparative data is itself surfaced: "No prior period data available — first month of operation."
- Absolute numbers alone (e.g., "47 completions") must not appear in operator dashboards without relative context (e.g., "+12% vs last month, 47/80 enrolled").
