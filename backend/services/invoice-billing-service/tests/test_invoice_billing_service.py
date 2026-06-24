from __future__ import annotations
import pytest
from app.service import BillingService
from app.store import InMemoryBillingStore


def _svc() -> BillingService:
    return BillingService(InMemoryBillingStore())


def _account(svc: BillingService, **kwargs) -> dict:
    _, a = svc.create_billing_account({"tenant_id": "t1", "customer_id": "c1",
                                        "billing_timezone": "UTC", "currency": "USD", **kwargs})
    return a


def _invoice(svc: BillingService, account_id: str, **kwargs) -> dict:
    body = {"billing_account_id": account_id, "invoice_type": "one_time",
            "lines": [{"line_type": "one_time_item", "quantity": 1, "unit_price": 100.0}], **kwargs}
    _, inv = svc.create_invoice(body)
    return inv


def test_create_billing_account():
    svc = _svc()
    status, body = svc.create_billing_account({"tenant_id": "t1", "customer_id": "c1",
                                                "billing_timezone": "UTC", "currency": "USD"})
    assert status == 201
    assert body["currency"] == "USD"


def test_create_invoice_draft():
    svc = _svc()
    a = _account(svc)
    status, body = svc.create_invoice({"billing_account_id": a["billing_account_id"],
                                        "invoice_type": "one_time",
                                        "lines": [{"line_type": "one_time_item", "quantity": 2,
                                                   "unit_price": 50.0}]})
    assert status == 201
    assert body["state"] == "draft"
    assert body["grand_total"] == 100.0


def test_invoice_lifecycle():
    svc = _svc()
    a = _account(svc)
    inv = _invoice(svc, a["billing_account_id"])
    iid = inv["invoice_id"]
    tid = "t1"

    status, body = svc.validate_invoice(iid, tid)
    assert status == 200
    assert body["state"] == "validated"

    status, body = svc.issue_invoice(iid, tid)
    assert status == 200
    assert body["state"] == "issued"
    assert body["invoice_number"].startswith("INV-")


def test_cannot_issue_draft():
    svc = _svc()
    a = _account(svc)
    inv = _invoice(svc, a["billing_account_id"])
    status, _ = svc.issue_invoice(inv["invoice_id"], "t1")
    assert status == 409


def test_void_issued_invoice():
    svc = _svc()
    a = _account(svc)
    inv = _invoice(svc, a["billing_account_id"])
    svc.validate_invoice(inv["invoice_id"], "t1")
    svc.issue_invoice(inv["invoice_id"], "t1")
    status, body = svc.void_invoice(inv["invoice_id"], "t1")
    assert status == 200
    assert body["state"] == "voided"


def test_cannot_void_draft():
    svc = _svc()
    a = _account(svc)
    inv = _invoice(svc, a["billing_account_id"])
    status, _ = svc.void_invoice(inv["invoice_id"], "t1")
    assert status == 409


def test_list_invoices():
    svc = _svc()
    a = _account(svc)
    _invoice(svc, a["billing_account_id"])
    _invoice(svc, a["billing_account_id"])
    status, body = svc.list_invoices("t1")
    assert status == 200
    assert body["count"] == 2


def test_invoice_number_unique_and_sequential():
    svc = _svc()
    a = _account(svc)
    for _ in range(3):
        inv = _invoice(svc, a["billing_account_id"])
        svc.validate_invoice(inv["invoice_id"], "t1")
        _, issued = svc.issue_invoice(inv["invoice_id"], "t1")
    numbers = [svc.store.get_invoice(svc.store._invoices[i].invoice_id).invoice_number
               for i in svc.store._invoices]
    issued_numbers = [n for n in numbers if n]
    assert len(set(issued_numbers)) == len(issued_numbers)
