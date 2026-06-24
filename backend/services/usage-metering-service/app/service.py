from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import UsageEvent
from .store import InMemoryMeteringStore

REQUIRED_FIELDS = {"event_id", "tenant_id", "capability_key", "domain_key", "metric_key"}


def _window(ts: datetime, granularity: str) -> Tuple[str, str]:
    if granularity == "hourly":
        start = ts.strftime("%Y-%m-%dT%H:00:00")
        end = ts.strftime("%Y-%m-%dT%H:59:59")
    elif granularity == "monthly":
        start = ts.strftime("%Y-%m-01")
        end = ts.strftime("%Y-%m-28")  # conservative end
    else:  # daily
        start = ts.strftime("%Y-%m-%d")
        end = ts.strftime("%Y-%m-%d")
    return start, end


class UsageMeteringService:
    def __init__(self, store: InMemoryMeteringStore) -> None:
        self.store = store

    def ingest_events(self, events: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
        accepted = 0
        rejected = []

        for raw in events:
            missing = [f for f in REQUIRED_FIELDS if not raw.get(f)]
            if missing:
                rejected.append({"event_id": raw.get("event_id", "?"), "reason": f"missing_fields:{','.join(missing)}"})
                continue

            event_id = raw["event_id"]
            idempotency_key = raw.get("idempotency_key")

            if self.store.is_duplicate(event_id, idempotency_key):
                rejected.append({"event_id": event_id, "reason": "duplicate"})
                continue

            ts_raw = raw.get("timestamp")
            ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(timezone.utc)

            event = UsageEvent(
                event_id=event_id,
                event_type=raw.get("event_type", "capability.usage.recorded.v1"),
                timestamp=ts,
                producer_service=raw.get("producer", {}).get("service", ""),
                producer_version=raw.get("producer", {}).get("version", ""),
                tenant_id=raw["tenant_id"],
                actor_type=raw.get("actor", {}).get("actor_type", "system"),
                actor_id=raw.get("actor", {}).get("actor_id", ""),
                domain_key=raw["domain_key"],
                capability_key=raw["capability_key"],
                metric_key=raw["metric_key"],
                quantity=float(raw.get("usage", {}).get("quantity", raw.get("quantity", 1))),
                unit=raw.get("usage", {}).get("unit", raw.get("unit", "count")),
                resource_id=raw.get("context", {}).get("resource_id"),
                session_id=raw.get("context", {}).get("session_id"),
                region=raw.get("context", {}).get("region"),
                idempotency_key=idempotency_key,
                payload=raw,
            )
            self.store.save_event(event)

            for gran in ("hourly", "daily", "monthly"):
                ws, we = _window(ts, gran)
                self.store.update_aggregate(
                    event.tenant_id, event.capability_key, event.domain_key,
                    event.metric_key, event.unit, ws, we, gran, event.quantity,
                )
            accepted += 1

        # B09-003: usage-metering-interface-contract.md — ingestBatch returns per-event
        # UsageIngestResult with meter_event_id, deduplicated, normalized_at
        results = []
        for raw in events:
            eid = raw.get("event_id", "?")
            is_dup = {"event_id": eid, "reason": "duplicate"} in rejected
            is_err = any(r["event_id"] == eid and "missing_fields" in r.get("reason", "") for r in rejected)
            results.append({
                "event_id": eid,
                "accepted": not (is_dup or is_err),
                "meter_event_id": f"met_{eid}" if not (is_dup or is_err) else None,
                "deduplicated": is_dup,
                "normalized_at": datetime.now(timezone.utc).isoformat(),
                "validation_errors": [r["reason"] for r in rejected if r["event_id"] == eid],
            })

        status = 207 if rejected else 202
        return status, {
            "accepted": accepted, "rejected_count": len(rejected),
            "total": len(events), "results": results,
        }

    def query_usage(self, tenant_id: str, capability_key: str,
                    from_date: str, to_date: str,
                    granularity: str = "daily",
                    metric_key: str = "request_count") -> Tuple[int, Dict[str, Any]]:
        rows = self.store.query(tenant_id, capability_key, metric_key, from_date, to_date, granularity)
        return 200, {
            "tenant_id": tenant_id,
            "capability_key": capability_key,
            "metric_key": metric_key,
            "granularity": granularity,
            "from": from_date,
            "to": to_date,
            "rows": [{"window_start": r.window_start, "total_quantity": round(r.total_quantity, 4),
                       "event_count": r.event_count, "unit": r.unit} for r in rows],
            "total_quantity": round(sum(r.total_quantity for r in rows), 4),
        }

    def export_daily(self, date: str) -> Tuple[int, Dict[str, Any]]:
        exported = []
        for agg in self.store._aggregates.values():
            if agg.granularity == "daily" and agg.window_start == date:
                exported.append({
                    "tenant_id": agg.tenant_id,
                    "capability_key": agg.capability_key,
                    "metric_key": agg.metric_key,
                    "unit": agg.unit,
                    "window": date,
                    "total_quantity": round(agg.total_quantity, 4),
                    "event_count": agg.event_count,
                })
        return 200, {"date": date, "export_count": len(exported), "records": exported}
