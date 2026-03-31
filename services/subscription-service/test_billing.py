from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal

sys.path.append(str(Path(__file__).resolve().parents[2]))

from service import Subscription, SubscriptionService


REQUIRED_FIELDS = {"invoice_id", "tenant_id", "amount", "status", "created_at"}


def test_generates_invoice_on_activation() -> None:
    service = SubscriptionService()
    draft = Subscription(subscription_id="sub_1", tenant_id="tenant_1", amount=Decimal("49.99"))

    activated, invoice = service.activate_subscription(draft)

    assert activated.active is True
    assert invoice.tenant_id == "tenant_1"
    assert invoice.amount == Decimal("49.99")
    assert invoice.status == "issued"
    assert REQUIRED_FIELDS.issubset(invoice.__dict__.keys())


def test_generates_invoice_on_renewal() -> None:
    service = SubscriptionService()
    active_sub = Subscription(
        subscription_id="sub_2",
        tenant_id="tenant_2",
        amount=Decimal("19.00"),
        active=True,
    )

    invoice = service.renew_subscription(active_sub)

    assert invoice.tenant_id == "tenant_2"
    assert invoice.amount == Decimal("19.00")
    assert invoice.status == "issued"
    assert REQUIRED_FIELDS.issubset(invoice.__dict__.keys())


def test_rejects_missing_invoice_data() -> None:
    service = SubscriptionService()
    active_sub = Subscription(
        subscription_id="sub_3",
        tenant_id="",
        amount=Decimal("10.00"),
        active=True,
    )

    try:
        service.renew_subscription(active_sub)
    except ValueError as exc:
        assert "tenant_id is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing tenant_id")
