from __future__ import annotations
import pytest
from app.service import RevenueService
from app.store import InMemoryRevenueStore


def _svc() -> RevenueService:
    return RevenueService(InMemoryRevenueStore())


def _fact(svc: RevenueService, **kwargs) -> dict:
    body = {"source_event_id": "evt-1", "fact_type": "invoice_line_recognized",
            "source_service": "billing", "tenant_id": "t1", "capability_key": "quiz",
            "currency": "USD", "gross": 100.0, "discount": 10.0, "net": 90.0,
            "recognized_at": "2026-05-01T00:00:00", "allocation_method": "direct_mapping", **kwargs}
    _, f = svc.ingest_fact(body)
    return f


def test_ingest_fact():
    svc = _svc()
    status, body = svc.ingest_fact({
        "source_event_id": "evt-1", "fact_type": "invoice_line_recognized",
        "source_service": "billing", "tenant_id": "t1", "capability_key": "quiz",
        "currency": "USD", "gross": 100.0, "discount": 10.0, "net": 90.0,
        "recognized_at": "2026-05-01T00:00:00", "allocation_method": "direct_mapping"
    })
    assert status == 201
    assert body["net"] == 90.0
    assert body["date"] == "2026-05-01"


def test_ingest_idempotent():
    svc = _svc()
    _fact(svc)
    status, body = svc.ingest_fact({"source_event_id": "evt-1", "net": 999})
    assert status == 200
    assert body["status"] == "already_ingested"


def test_query_tenant():
    svc = _svc()
    _fact(svc, source_event_id="e1", net=90.0, recognized_at="2026-05-01T00:00:00")
    _fact(svc, source_event_id="e2", net=50.0, recognized_at="2026-05-02T00:00:00")
    status, body = svc.query_tenant("t1", "2026-05-01", "2026-05-31")
    assert status == 200
    assert body["total_recognized"] == 140.0


def test_query_capability():
    svc = _svc()
    _fact(svc, source_event_id="e1", capability_key="quiz", net=90.0, recognized_at="2026-05-01T00:00:00")
    _fact(svc, source_event_id="e2", capability_key="video", net=50.0, recognized_at="2026-05-01T00:00:00")
    status, body = svc.query_capability("quiz", "2026-05-01", "2026-05-31")
    assert status == 200
    assert body["total_recognized"] == 90.0


def test_refund_tracked_separately():
    svc = _svc()
    _fact(svc, source_event_id="e1", net=90.0, recognized_at="2026-05-01T00:00:00")
    svc.ingest_fact({"source_event_id": "e2", "fact_type": "refund_recognized",
                     "source_service": "billing", "tenant_id": "t1",
                     "currency": "USD", "gross": 90.0, "discount": 0.0, "net": 90.0,
                     "recognized_at": "2026-05-01T00:00:00", "allocation_method": "direct_mapping"})
    status, body = svc.query_tenant("t1", "2026-05-01", "2026-05-31")
    assert body["rows"][0]["refund_delta"] == 90.0
    assert body["rows"][0]["recognized_revenue"] == 90.0
