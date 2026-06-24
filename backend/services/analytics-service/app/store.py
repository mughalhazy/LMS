from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .models import AnalyticsEvent


class InMemoryAnalyticsStore:
    def __init__(self) -> None:
        self._events: Dict[str, AnalyticsEvent] = {}
        # aggregated: tenant_id -> entity_id -> metric_key -> period -> value
        self._agg: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )

    def save_event(self, event: AnalyticsEvent) -> None:
        self._events[event.event_id] = event
        bucket = self._agg[event.tenant_id][event.entity_id][event.metric_key]
        bucket[event.period] = bucket.get(event.period, 0.0) + event.value

    def get_values(self, tenant_id: str, entity_id: str, metric_key: str) -> Dict[str, float]:
        return dict(self._agg.get(tenant_id, {}).get(entity_id, {}).get(metric_key, {}))

    def get_tenant_entities(self, tenant_id: str, entity_type: str) -> List[str]:
        entities = set()
        for ev in self._events.values():
            if ev.tenant_id == tenant_id and ev.entity_type == entity_type:
                entities.add(ev.entity_id)
        return list(entities)

    def all_values_for_metric(self, tenant_id: str, metric_key: str, period: str) -> List[Tuple[str, float]]:
        results = []
        tenant_data = self._agg.get(tenant_id, {})
        for entity_id, metrics in tenant_data.items():
            val = metrics.get(metric_key, {}).get(period)
            if val is not None:
                results.append((entity_id, val))
        return results
