from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import AnalyticsEvent, BenchmarkEntry, InsightEnvelope
from .store import InMemoryAnalyticsStore


def _trend_label(current: float, prior: Optional[float]) -> str:
    if prior is None or prior == 0:
        return "no_prior_period_data"
    delta_pct = ((current - prior) / prior) * 100
    if abs(delta_pct) < 2:
        return "stable"
    direction = "up" if delta_pct > 0 else "down"
    return f"{direction}_{abs(delta_pct):.0f}pct_vs_last_period"


def _comparative_context(current: float, prior: Optional[float], entity_id: str) -> str:
    if prior is None:
        return "No prior period data available — first period of operation."
    delta = current - prior
    direction = "increased" if delta >= 0 else "decreased"
    return f"{entity_id}: metric {direction} by {abs(delta):.1f} vs prior period ({prior:.1f} → {current:.1f})"


class AnalyticsService:
    def __init__(self, store: InMemoryAnalyticsStore) -> None:
        self.store = store

    def ingest(self, events: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        accepted = 0
        for raw in events:
            if not all(raw.get(f) for f in ("event_id", "tenant_id", "entity_id", "metric_key")):
                continue
            if raw["event_id"] in self.store._events:
                continue
            ts_raw = raw.get("recorded_at")
            ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(timezone.utc)
            event = AnalyticsEvent(
                event_id=raw["event_id"],
                tenant_id=raw["tenant_id"],
                event_type=raw.get("event_type", "generic"),
                entity_id=raw["entity_id"],
                entity_type=raw.get("entity_type", "learner"),
                metric_key=raw["metric_key"],
                value=float(raw.get("value", 1.0)),
                period=raw.get("period", ts.strftime("%Y-%m-%d")),
                recorded_at=ts,
            )
            self.store.save_event(event)
            accepted += 1
        return 202, {"accepted": accepted, "total": len(events)}

    def learner_insights(self, tenant_id: str, learner_id: str,
                          metric_key: str, current_period: str,
                          prior_period: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        values = self.store.get_values(tenant_id, learner_id, metric_key)
        current = values.get(current_period, 0.0)
        prior = values.get(prior_period) if prior_period else None

        insight = InsightEnvelope(
            metric=metric_key,
            current_value=current,
            prior_value=prior,
            trend=_trend_label(current, prior),
            context=_comparative_context(current, prior, learner_id),
            suggested_action=self._learner_action(metric_key, current, prior),
            action_link=f"/learners/{learner_id}?metric={metric_key}",
            comparative_ref="prior_period" if prior is not None else "none",
            tenant_id=tenant_id,
            entity_id=learner_id,
            period=current_period,
        )
        return 200, self._serialize_insight(insight)

    def tenant_insights(self, tenant_id: str, metric_key: str,
                         current_period: str, prior_period: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        current_entries = self.store.all_values_for_metric(tenant_id, metric_key, current_period)
        current_total = sum(v for _, v in current_entries)
        prior_total: Optional[float] = None
        if prior_period:
            prior_entries = self.store.all_values_for_metric(tenant_id, metric_key, prior_period)
            prior_total = sum(v for _, v in prior_entries) if prior_entries else None

        insight = InsightEnvelope(
            metric=metric_key,
            current_value=current_total,
            prior_value=prior_total,
            trend=_trend_label(current_total, prior_total),
            context=_comparative_context(current_total, prior_total, tenant_id),
            suggested_action=self._tenant_action(metric_key, current_total, prior_total),
            action_link=f"/tenants/{tenant_id}/analytics?metric={metric_key}",
            comparative_ref="prior_period" if prior_total is not None else "none",
            tenant_id=tenant_id,
            entity_id=tenant_id,
            period=current_period,
        )
        return 200, self._serialize_insight(insight)

    def benchmark(self, tenant_id: str, metric_key: str, period: str) -> Tuple[int, Dict[str, Any]]:
        entries = self.store.all_values_for_metric(tenant_id, metric_key, period)
        if not entries:
            return 200, {"metric_key": metric_key, "period": period, "rankings": [],
                          "comparative_ref": "no_data_available"}

        sorted_entries = sorted(entries, key=lambda x: x[1], reverse=True)
        avg = sum(v for _, v in entries) / len(entries)
        results = []
        for rank, (entity_id, value) in enumerate(sorted_entries, 1):
            percentile = round((1 - (rank - 1) / len(sorted_entries)) * 100, 1)
            results.append(BenchmarkEntry(
                entity_id=entity_id, entity_type="entity",
                metric_key=metric_key, value=value, rank=rank,
                percentile=percentile, vs_cohort_avg=round(value - avg, 2),
            ))

        # BC-ANALYTICS-02: always include comparative context
        return 200, {
            "metric_key": metric_key, "period": period,
            "cohort_avg": round(avg, 2),
            "comparative_ref": "cohort_average",  # BC-ANALYTICS-02
            "rankings": [{"entity_id": r.entity_id, "value": r.value, "rank": r.rank,
                           "percentile": r.percentile, "vs_cohort_avg": r.vs_cohort_avg}
                          for r in results],
        }

    def _learner_action(self, metric_key: str, current: float, prior: Optional[float]) -> str:
        if prior is not None and current < prior * 0.8:
            return f"Learner showing decline in {metric_key} — consider intervention or check-in"
        return f"Monitor {metric_key} trend for early intervention signals"

    def _tenant_action(self, metric_key: str, current: float, prior: Optional[float]) -> str:
        if prior is not None and current < prior * 0.85:
            return f"{metric_key} declined — review courses with high dropoff and send re-engagement prompts"
        return f"Review {metric_key} distribution across cohorts for optimisation opportunities"

    def _serialize_insight(self, i: InsightEnvelope) -> Dict[str, Any]:
        return {
            "metric": i.metric, "current_value": i.current_value,
            "prior_value": i.prior_value, "trend": i.trend,
            "context": i.context, "suggested_action": i.suggested_action,
            "action_link": i.action_link, "comparative_ref": i.comparative_ref,
            "tenant_id": i.tenant_id, "entity_id": i.entity_id, "period": i.period,
        }
