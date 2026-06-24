from __future__ import annotations
import pytest
from app.service import UsageMeteringService
from app.store import InMemoryMeteringStore


def _svc() -> UsageMeteringService:
    return UsageMeteringService(InMemoryMeteringStore())


def _event(**kwargs) -> dict:
    return {
        "event_id": "evt-1", "tenant_id": "t1", "capability_key": "quiz",
        "domain_key": "learning", "metric_key": "request_count",
        "usage": {"quantity": 1, "unit": "count"},
        "timestamp": "2026-05-01T10:00:00",
        "producer": {"service": "quiz-engine", "version": "1.0"},
        "actor": {"actor_type": "user", "actor_id": "u1"},
        **kwargs,
    }


def test_ingest_single_event():
    svc = _svc()
    status, body = svc.ingest_events([_event()])
    assert status == 202
    assert body["accepted"] == 1
    assert body["rejected"] == []


def test_ingest_duplicate_by_event_id():
    svc = _svc()
    svc.ingest_events([_event()])
    status, body = svc.ingest_events([_event()])
    assert body["rejected"][0]["reason"] == "duplicate"


def test_ingest_duplicate_by_idempotency_key():
    svc = _svc()
    svc.ingest_events([_event(idempotency_key="idk-1")])
    status, body = svc.ingest_events([_event(event_id="evt-2", idempotency_key="idk-1")])
    assert body["rejected"][0]["reason"] == "duplicate"


def test_ingest_rejects_missing_fields():
    svc = _svc()
    status, body = svc.ingest_events([{"event_id": "x"}])
    assert body["rejected"][0]["reason"].startswith("missing_fields")


def test_aggregate_accumulates():
    svc = _svc()
    svc.ingest_events([_event(event_id="e1", usage={"quantity": 5, "unit": "count"})])
    svc.ingest_events([_event(event_id="e2", usage={"quantity": 3, "unit": "count"})])
    _, body = svc.query_usage("t1", "quiz", "2026-05-01", "2026-05-01")
    assert body["total_quantity"] == 8.0


def test_query_filters_by_range():
    svc = _svc()
    svc.ingest_events([_event(event_id="e1", timestamp="2026-05-01T10:00:00")])
    svc.ingest_events([_event(event_id="e2", timestamp="2026-05-10T10:00:00")])
    _, body = svc.query_usage("t1", "quiz", "2026-05-01", "2026-05-05")
    assert body["total_quantity"] == 1.0


def test_export_daily():
    svc = _svc()
    svc.ingest_events([_event()])
    _, body = svc.export_daily("2026-05-01")
    assert body["export_count"] >= 1
    assert body["records"][0]["tenant_id"] == "t1"


def test_multi_event_batch():
    svc = _svc()
    events = [_event(event_id=f"evt-{i}", usage={"quantity": 1, "unit": "count"}) for i in range(5)]
    status, body = svc.ingest_events(events)
    assert body["accepted"] == 5
