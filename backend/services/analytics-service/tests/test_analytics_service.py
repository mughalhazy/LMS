from __future__ import annotations
import pytest
from app.service import AnalyticsService
from app.store import InMemoryAnalyticsStore


def _svc() -> AnalyticsService:
    return AnalyticsService(InMemoryAnalyticsStore())


def _event(svc: AnalyticsService, entity_id: str, metric: str, value: float,
           period: str, event_id: str = None, tenant_id: str = "t1") -> None:
    svc.ingest([{
        "event_id": event_id or f"e-{entity_id}-{period}",
        "tenant_id": tenant_id, "entity_id": entity_id,
        "entity_type": "learner", "metric_key": metric,
        "value": value, "period": period,
    }])


def test_ingest_events():
    svc = _svc()
    status, body = svc.ingest([{
        "event_id": "e1", "tenant_id": "t1", "entity_id": "u1",
        "metric_key": "completion_rate", "value": 0.75, "period": "2026-05",
    }])
    assert status == 202
    assert body["accepted"] == 1


def test_ingest_idempotent():
    svc = _svc()
    _event(svc, "u1", "completion_rate", 0.75, "2026-05", "e1")
    status, body = svc.ingest([{
        "event_id": "e1", "tenant_id": "t1", "entity_id": "u1",
        "metric_key": "completion_rate", "value": 0.80, "period": "2026-05",
    }])
    assert body["accepted"] == 0


def test_learner_insight_bc_analytics_01():
    svc = _svc()
    _event(svc, "u1", "completion_rate", 0.62, "2026-05")
    _event(svc, "u1", "completion_rate", 0.76, "2026-04", event_id="e2")
    status, body = svc.learner_insights("t1", "u1", "completion_rate", "2026-05", "2026-04")
    assert status == 200
    # BC-ANALYTICS-01: insight envelope fields all present
    for field in ("metric", "current_value", "trend", "context", "suggested_action", "action_link"):
        assert field in body
    assert body["suggested_action"] is not None
    assert len(body["suggested_action"]) > 0


def test_trend_label_down():
    svc = _svc()
    _event(svc, "u1", "score", 60.0, "2026-05")
    _event(svc, "u1", "score", 80.0, "2026-04", event_id="e2")
    _, body = svc.learner_insights("t1", "u1", "score", "2026-05", "2026-04")
    assert "down" in body["trend"]


def test_trend_label_no_prior():
    svc = _svc()
    _event(svc, "u1", "score", 75.0, "2026-05")
    _, body = svc.learner_insights("t1", "u1", "score", "2026-05")
    assert "no_prior_period_data" in body["trend"]


def test_tenant_insights_bc_analytics_01():
    svc = _svc()
    _event(svc, "u1", "completion_rate", 0.7, "2026-05")
    _event(svc, "u2", "completion_rate", 0.5, "2026-05", event_id="e2")
    status, body = svc.tenant_insights("t1", "completion_rate", "2026-05")
    assert status == 200
    assert body["suggested_action"] is not None
    assert body["current_value"] == pytest.approx(1.2)


def test_benchmark_bc_analytics_02():
    svc = _svc()
    _event(svc, "u1", "score", 80.0, "2026-05")
    _event(svc, "u2", "score", 60.0, "2026-05", event_id="e2")
    _event(svc, "u3", "score", 70.0, "2026-05", event_id="e3")
    status, body = svc.benchmark("t1", "score", "2026-05")
    assert status == 200
    # BC-ANALYTICS-02: comparative_ref must be present
    assert body["comparative_ref"] == "cohort_average"
    assert "cohort_avg" in body
    assert len(body["rankings"]) == 3
    assert body["rankings"][0]["rank"] == 1


def test_benchmark_rankings_ordered():
    svc = _svc()
    for i, (uid, score) in enumerate([("a", 90.0), ("b", 50.0), ("c", 70.0)]):
        _event(svc, uid, "score", score, "2026-05", event_id=f"e{i}")
    _, body = svc.benchmark("t1", "score", "2026-05")
    ranks = [r["rank"] for r in body["rankings"]]
    assert ranks == sorted(ranks)
    assert body["rankings"][0]["entity_id"] == "a"
