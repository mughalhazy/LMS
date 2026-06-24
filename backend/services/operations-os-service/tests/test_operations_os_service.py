from __future__ import annotations
import pytest
from app.service import OperationsOSService


def _svc() -> OperationsOSService:
    return OperationsOSService()


def test_record_metric():
    svc = _svc()
    status, body = svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                                       "value": 85.0, "threshold": 70.0, "period": "2026-W21"})
    assert status == 201


def test_critical_action_generated_for_low_attendance():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 55.0, "threshold": 70.0, "period": "2026-W21"})
    _, body = svc.get_action_queue("op1", "t1")
    assert body["critical_count"] >= 1


def test_important_action_generated():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 65.0, "threshold": 70.0, "period": "2026-W21"})
    _, body = svc.get_action_queue("op1", "t1")
    assert body["important_count"] >= 1


def test_no_action_when_metric_healthy():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 90.0, "threshold": 70.0, "period": "2026-W21"})
    _, body = svc.get_action_queue("op1", "t1")
    assert body["critical_count"] == 0
    assert body["important_count"] == 0


def test_action_queue_critical_first():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 55.0, "threshold": 70.0, "period": "week-1"})
    svc.record_metric({"tenant_id": "t1", "metric_type": "fee_collection_rate",
                        "value": 75.0, "threshold": 80.0, "period": "week-1"})
    _, body = svc.get_action_queue("op1", "t1")
    tiers = [a["tier"] for a in body["actions"]]
    tier_order = {"CRITICAL": 0, "IMPORTANT": 1, "OPTIONAL": 2}
    assert tiers == sorted(tiers, key=lambda t: tier_order.get(t, 99))


def test_daily_action_list_structure():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 55.0, "threshold": 70.0, "period": "2026-05-29"})
    status, body = svc.get_daily_action_list("op1", "t1", "2026-05-29")
    assert status == 200
    assert "critical" in body
    assert "important" in body
    assert "optional" in body
    assert len(body["critical"]) >= 1


def test_bc_ops_01_action_items_have_pattern_and_implication():
    svc = _svc()
    svc.record_metric({"tenant_id": "t1", "metric_type": "attendance_rate",
                        "value": 50.0, "threshold": 70.0, "period": "2026-W21"})
    _, body = svc.get_action_queue("op1", "t1")
    for action in body["actions"]:
        assert action["pattern"] is not None
        assert action["implication"] is not None
        assert action["action_command"] is not None
