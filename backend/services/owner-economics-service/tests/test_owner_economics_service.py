from __future__ import annotations
import pytest
from app.service import OwnerEconomicsService
from app.store import InMemoryEconomicsStore


def _svc() -> OwnerEconomicsService:
    return OwnerEconomicsService(InMemoryEconomicsStore())


def _earn(svc: OwnerEconomicsService, **kwargs) -> dict:
    body = {"participant_id": "p1", "tenant_id": "t1", "source_event_id": "evt-1",
            "event_type": "enrollment_revenue_share", "gross_amount": 100.0,
            "currency": "USD", "period": "2026-05", **kwargs}
    _, e = svc.record_earning(body)
    return e


def test_record_earning():
    svc = _svc()
    status, body = svc.record_earning({
        "participant_id": "p1", "tenant_id": "t1", "source_event_id": "evt-1",
        "event_type": "enrollment_revenue_share", "gross_amount": 100.0,
        "currency": "USD", "period": "2026-05"
    })
    assert status == 201
    assert body["platform_commission"] == 20.0
    assert body["net_amount"] == 80.0


def test_earning_idempotent():
    svc = _svc()
    _earn(svc)
    status, body = svc.record_earning({"source_event_id": "evt-1", "gross_amount": 999})
    assert status == 200
    assert body["status"] == "already_recorded"


def test_ledger_accumulates():
    svc = _svc()
    _earn(svc, source_event_id="e1", gross_amount=100.0)
    _earn(svc, source_event_id="e2", gross_amount=50.0)
    status, body = svc.get_ledger("p1", "t1", "2026-05")
    assert status == 200
    assert body["total_gross"] == 150.0
    assert body["total_net"] == 120.0
    assert body["entry_count"] == 2


def test_calculate_payout():
    svc = _svc()
    _earn(svc, gross_amount=100.0)
    status, body = svc.calculate_payout({"participant_id": "p1", "tenant_id": "t1", "period": "2026-05"})
    assert status == 200
    assert "net_payout" in body
    assert body["net_payout"] > 0
    assert "processing_fee" in body["deduction_breakdown"]
    assert "tax_withholding" in body["deduction_breakdown"]


def test_payout_deductions_sum():
    svc = _svc()
    _earn(svc, gross_amount=200.0)
    _, body = svc.calculate_payout({"participant_id": "p1", "tenant_id": "t1", "period": "2026-05"})
    net = body["net_payout"]
    commission = body["deduction_breakdown"]["platform_commission"]
    processing = body["deduction_breakdown"]["processing_fee"]
    tax = body["deduction_breakdown"]["tax_withholding"]
    assert abs(body["gross_earnings"] - commission - processing - tax - net) < 0.01


def test_list_payouts():
    svc = _svc()
    _earn(svc)
    svc.calculate_payout({"participant_id": "p1", "tenant_id": "t1", "period": "2026-05"})
    status, body = svc.list_payouts("p1", "t1")
    assert status == 200
    assert len(body["payouts"]) == 1


def test_ledger_not_found():
    svc = _svc()
    status, _ = svc.get_ledger("nobody", "t1", "2026-05")
    assert status == 404
