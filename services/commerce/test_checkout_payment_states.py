from __future__ import annotations

import asyncio
from decimal import Decimal

from services.commerce.catalog import CatalogService
from services.commerce.checkout import CheckoutService, OrderStatus
from services.commerce.models import ProductType


def _catalog_with_product() -> CatalogService:
    catalog = CatalogService()
    catalog.create_product(
        product_id="p1",
        tenant_id="tenant_1",
        type=ProductType.COURSE,
        title="Course",
        description="Course",
        price=Decimal("10.00"),
        currency="USD",
        capability_ids=["assessment.author"],
    )
    return catalog


def test_checkout_retries_and_notifies_user_on_final_failure() -> None:
    calls: list[int] = []
    notifications: list[tuple[str, str, str]] = []

    def payment_executor(tenant_id: str, learner_id: str, amount: Decimal, currency: str, attempt: int, idempotency_key: str) -> tuple[bool, str | None, bool]:
        calls.append(attempt)
        return False, None, True

    checkout = CheckoutService(
        _catalog_with_product(),
        payment_executor,
        lambda product: product.price,
        max_retries=1,
        failure_notifier=lambda tenant_id, learner_id, order_id: notifications.append((tenant_id, learner_id, order_id)),
    )
    checkout.start_session(
        session_id="sess_1",
        tenant_id="tenant_1",
        learner_id="learner_1",
        product_id="p1",
        idempotency_key="idem_1",
    )
    order = asyncio.run(checkout.submit_session(session_id="sess_1", max_retries=1))
    assert order.status == OrderStatus.FAILED
    assert calls == [0, 1]
    assert notifications == [("tenant_1", "learner_1", order.order_id)]


def test_checkout_payment_state_transitions_retrying_to_success() -> None:
    def payment_executor(tenant_id: str, learner_id: str, amount: Decimal, currency: str, attempt: int, idempotency_key: str) -> tuple[bool, str | None, bool]:
        if attempt == 0:
            return False, None, True
        return True, "pay_1", False

    checkout = CheckoutService(_catalog_with_product(), payment_executor, lambda product: product.price, max_retries=2)
    checkout.start_session(
        session_id="sess_2",
        tenant_id="tenant_1",
        learner_id="learner_1",
        product_id="p1",
        idempotency_key="idem_2",
    )
    order = asyncio.run(checkout.submit_session(session_id="sess_2"))
    logs = checkout.get_transaction_logs(order_id=order.order_id)
    assert [log.success for log in logs] == [False, True]
    assert [log.retryable for log in logs] == [True, False]
    assert order.status == OrderStatus.PAID
