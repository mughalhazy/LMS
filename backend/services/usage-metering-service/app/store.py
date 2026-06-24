from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .models import UsageAggregate, UsageEvent


class InMemoryMeteringStore:
    def __init__(self) -> None:
        self._events: Dict[str, UsageEvent] = {}
        self._idempotency_keys: set = set()
        self._aggregates: Dict[Tuple, UsageAggregate] = {}

    def is_duplicate(self, event_id: str, idempotency_key: Optional[str]) -> bool:
        if event_id in self._events:
            return True
        if idempotency_key and idempotency_key in self._idempotency_keys:
            return True
        return False

    def save_event(self, event: UsageEvent) -> None:
        self._events[event.event_id] = event
        if event.idempotency_key:
            self._idempotency_keys.add(event.idempotency_key)

    def update_aggregate(self, tenant_id: str, capability_key: str, domain_key: str,
                         metric_key: str, unit: str, window_start: str, window_end: str,
                         granularity: str, quantity: float) -> None:
        key = (tenant_id, capability_key, metric_key, granularity, window_start)
        agg = self._aggregates.setdefault(key, UsageAggregate(
            tenant_id=tenant_id, capability_key=capability_key, domain_key=domain_key,
            metric_key=metric_key, unit=unit, window_start=window_start,
            window_end=window_end, granularity=granularity,
        ))
        agg.total_quantity += quantity
        agg.event_count += 1
        agg.last_updated_at = datetime.now(timezone.utc)

    def query(self, tenant_id: str, capability_key: str, metric_key: str,
              from_date: str, to_date: str, granularity: str) -> List[UsageAggregate]:
        results = []
        for (tid, ck, mk, gran, ws), agg in self._aggregates.items():
            if (tid == tenant_id and ck == capability_key and
                    mk == metric_key and gran == granularity and
                    from_date <= ws <= to_date):
                results.append(agg)
        return sorted(results, key=lambda a: a.window_start)
