from __future__ import annotations
import pytest
from app.service import CheckoutService
from app.store import InMemoryCheckoutStore


def _svc() -> CheckoutService:
    return CheckoutService(InMemoryCheckoutStore())


def _session(svc: CheckoutService, **kwargs) -> dict:
    _, s = svc.create_session({"tenant_id": "t1", "customer_id": "c1", "currency": "USD", **kwargs})
    return s


def _add_item(svc: CheckoutService, session_id: str) -> None:
    svc.update_items(session_id, "t1", [{"sku": "SKU-1", "quantity": 1, "display_price_ref": "pr1"}])


def test_create_session():
    svc = _svc()
    s = _session(svc)
    assert s["status"] == "open"
    assert s["currency"] == "USD"


def test_update_items():
    svc = _svc()
    s = _session(svc)
    status, body = svc.update_items(s["session_id"], "t1",
                                     [{"sku": "A", "quantity": 2, "display_price_ref": "p1"}])
    assert status == 200
    assert len(body["line_items"]) == 1


def test_submit_session_creates_order():
    svc = _svc()
    s = _session(svc)
    _add_item(svc, s["session_id"])
    status, body = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    assert status == 202
    assert "order_id" in body


def test_submit_empty_session_fails():
    svc = _svc()
    s = _session(svc)
    status, body = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    assert status == 422


def test_submit_idempotent():
    svc = _svc()
    s = _session(svc)
    _add_item(svc, s["session_id"])
    _, first = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    _, second = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    assert second.get("idempotent_replay") is True
    assert first["order_id"] == second["order_id"]


def test_initiate_payment():
    svc = _svc()
    s = _session(svc)
    _add_item(svc, s["session_id"])
    _, order = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    status, body = svc.initiate_payment(order["order_id"], "t1", {"request_id": "req-1"})
    assert status == 200
    assert body["status"] == "payment_initiated"


def test_payment_idempotent():
    svc = _svc()
    s = _session(svc)
    _add_item(svc, s["session_id"])
    _, order = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    svc.initiate_payment(order["order_id"], "t1", {"request_id": "req-1"})
    status, body = svc.initiate_payment(order["order_id"], "t1", {"request_id": "req-1"})
    assert body.get("idempotent_replay") is True


def test_get_order():
    svc = _svc()
    s = _session(svc)
    _add_item(svc, s["session_id"])
    _, order = svc.submit_session(s["session_id"], "t1", {"idempotency_key": "ik-1"})
    status, body = svc.get_order(order["order_id"], "t1")
    assert status == 200
    assert body["source_session_id"] == s["session_id"]
