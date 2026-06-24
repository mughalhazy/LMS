from __future__ import annotations
import pytest
from app.service import SystemEconomicsService


def _svc() -> SystemEconomicsService:
    return SystemEconomicsService()


def test_record_cost():
    svc = _svc()
    status, body = svc.record_cost({"tenant_id": "t1", "capability_key": "ai-tutor",
                                     "cost_type": "ai_calls", "amount": 50.0,
                                     "currency": "USD", "period": "2026-05"})
    assert status == 201


def test_invalid_cost_type():
    svc = _svc()
    status, _ = svc.record_cost({"tenant_id": "t1", "capability_key": "x",
                                  "cost_type": "unknown", "amount": 10.0, "period": "2026-05"})
    assert status == 400


def test_profitability_calculation():
    svc = _svc()
    svc.record_cost({"tenant_id": "t1", "capability_key": "ai", "cost_type": "ai_calls",
                      "amount": 200.0, "currency": "USD", "period": "2026-05"})
    svc.record_revenue("t1", "2026-05", 1000.0)
    status, body = svc.get_profitability("t1", "2026-05")
    assert status == 200
    assert body["revenue"] == 1000.0
    assert body["cost"] == 200.0
    assert body["margin"] == 800.0
    assert body["margin_pct"] == 80.0


def test_low_margin_triggers_suggested_action():
    svc = _svc()
    svc.record_cost({"tenant_id": "t1", "capability_key": "ai", "cost_type": "compute",
                      "amount": 900.0, "currency": "USD", "period": "2026-05"})
    svc.record_revenue("t1", "2026-05", 1000.0)
    _, body = svc.get_profitability("t1", "2026-05")
    assert body["suggested_action"] is not None
    assert "pricing" in body["suggested_action"].lower() or "cost" in body["suggested_action"].lower()


def test_insight_bc_econ_01_always_has_action():
    svc = _svc()
    svc.record_cost({"tenant_id": "t1", "capability_key": "expensive-cap",
                      "cost_type": "ai_calls", "amount": 500.0, "period": "2026-05"})
    svc.record_revenue("t1", "2026-05", 100.0)
    _, body = svc.get_insights("t1", "2026-05")
    for insight in body["insights"]:
        # BC-ECON-01: every insight must carry a suggested action
        assert insight["suggested_action"] is not None
        assert len(insight["suggested_action"]) > 0


def test_zero_cost_zero_margin():
    svc = _svc()
    svc.record_revenue("t1", "2026-05", 500.0)
    _, body = svc.get_profitability("t1", "2026-05")
    assert body["cost"] == 0.0
    assert body["margin"] == 500.0
