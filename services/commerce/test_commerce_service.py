from __future__ import annotations

from decimal import Decimal

from integrations.payment.adapters import MockFailureAdapter, MockSuccessAdapter
from integrations.payment.base_adapter import PaymentResult, TenantPaymentContext
from integrations.payment.router import PaymentProviderRouter
from services.commerce.catalog import ProductType
from services.commerce.service import CommerceService


class FlakyAdapter:
    provider_key = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def process_payment(self, amount: int, tenant: TenantPaymentContext, invoice_id: str | None = None) -> PaymentResult:
        self.calls += 1
        if self.calls == 1:
            return PaymentResult(ok=False, status="failure", provider=self.provider_key, error="timeout")
        return PaymentResult(ok=True, status="success", provider=self.provider_key, payment_id="pay_retry_ok")


def test_catalog_checkout_billing_separation_and_completion_flow() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_router=router)

    commerce.add_product(
        product_id="p_course",
        tenant_id="tenant_1",
        sku="course-101",
        product_type=ProductType.COURSE,
        title="Course 101",
        price=Decimal("99.00"),
        currency="USD",
    )

    order, invoice = commerce.checkout_and_invoice_sync(
        session_id="sess_1",
        tenant_id="tenant_1",
        learner_id="learner_1",
        product_id="p_course",
        idempotency_key="idem_1",
    )

    assert order.status.value == "completed"
    assert invoice.state.value == "issued"
    assert invoice.invoice_type == "one_time"
    assert commerce.catalog.get_product("p_course") is not None
    assert commerce.checkout.get_order(order.order_id) is not None
    assert commerce.billing.get_invoice(invoice.invoice_id) is not None


def test_checkout_retries_and_idempotency() -> None:
    flaky = FlakyAdapter()
    router = PaymentProviderRouter({"US": "flaky"}, [flaky])
    commerce = CommerceService(payment_router=router)
    commerce.add_product(
        product_id="p_bundle",
        tenant_id="tenant_2",
        sku="bundle-201",
        product_type=ProductType.BUNDLE,
        title="Bundle 201",
        price=Decimal("149.00"),
        currency="USD",
    )

    order_a, _ = commerce.checkout_and_invoice_sync(
        session_id="sess_2",
        tenant_id="tenant_2",
        learner_id="learner_2",
        product_id="p_bundle",
        idempotency_key="idem_same",
    )
    order_b, _ = commerce.checkout_and_invoice_sync(
        session_id="sess_3",
        tenant_id="tenant_2",
        learner_id="learner_2",
        product_id="p_bundle",
        idempotency_key="idem_same",
    )

    assert order_a.order_id == order_b.order_id
    assert flaky.calls == 2


def test_subscription_product_activates_subscription_service_contract() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter(), MockFailureAdapter()])
    commerce = CommerceService(payment_router=router)

    commerce.add_product(
        product_id="p_sub",
        tenant_id="tenant_3",
        sku="sub-301",
        product_type=ProductType.SUBSCRIPTION,
        title="Pro Subscription",
        price=Decimal("29.00"),
        currency="USD",
    )

    _, invoice = commerce.checkout_and_invoice_sync(
        session_id="sess_4",
        tenant_id="tenant_3",
        learner_id="learner_3",
        product_id="p_sub",
        idempotency_key="idem_sub",
    )

    contract = commerce.subscription_service.get_subscription_contract("sub_tenant_3_p_sub")
    assert invoice.invoice_type == "subscription"
    assert contract is not None
    assert contract.status == "active"
