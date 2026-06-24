from __future__ import annotations
import pytest
from app.service import FinancialLedgerService


def _svc() -> FinancialLedgerService:
    return FinancialLedgerService()


def test_record_fee_charged():
    svc = _svc()
    status, body = svc.record_entry({"student_id": "s1", "tenant_id": "t1",
                                      "entry_type": "fee_charged", "amount": 500.0, "currency": "USD"})
    assert status == 201


def test_balance_after_fee():
    svc = _svc()
    svc.record_entry({"student_id": "s1", "tenant_id": "t1", "entry_type": "fee_charged",
                       "amount": 500.0, "currency": "USD"})
    _, body = svc.get_balance("s1", "t1")
    assert body["total_owed"] == 500.0
    assert body["balance"] == 500.0
    assert body["overdue"] is True


def test_payment_reduces_balance():
    svc = _svc()
    svc.record_entry({"student_id": "s1", "tenant_id": "t1", "entry_type": "fee_charged",
                       "amount": 500.0, "currency": "USD"})
    svc.record_entry({"student_id": "s1", "tenant_id": "t1", "entry_type": "payment_received",
                       "amount": 300.0, "currency": "USD"})
    _, body = svc.get_balance("s1", "t1")
    assert body["balance"] == 200.0
    assert body["total_paid"] == 300.0


def test_full_payment_clears_balance():
    svc = _svc()
    svc.record_entry({"student_id": "s1", "tenant_id": "t1", "entry_type": "fee_charged",
                       "amount": 500.0, "currency": "USD"})
    svc.record_entry({"student_id": "s1", "tenant_id": "t1", "entry_type": "payment_received",
                       "amount": 500.0, "currency": "USD"})
    _, body = svc.get_balance("s1", "t1")
    assert body["balance"] == 0.0
    assert body["overdue"] is False


def test_add_obligation():
    svc = _svc()
    status, body = svc.add_obligation({"student_id": "s1", "tenant_id": "t1",
                                        "enrollment_id": "enr-1", "amount": 200.0,
                                        "currency": "USD", "due_date": "2026-12-31T00:00:00"})
    assert status == 201
    assert body["status"] == "pending"


def test_list_obligations():
    svc = _svc()
    svc.add_obligation({"student_id": "s1", "tenant_id": "t1", "enrollment_id": "enr-1",
                         "amount": 200.0, "currency": "USD", "due_date": "2026-12-31T00:00:00"})
    _, body = svc.list_obligations("s1", "t1")
    assert len(body["obligations"]) == 1


def test_invalid_entry_type():
    svc = _svc()
    status, _ = svc.record_entry({"student_id": "s1", "tenant_id": "t1",
                                   "entry_type": "invalid", "amount": 100.0})
    assert status == 400


def test_zero_balance_new_student():
    svc = _svc()
    _, body = svc.get_balance("new-student", "t1")
    assert body["balance"] == 0.0
    assert body["overdue"] is False
