from __future__ import annotations

from decimal import Decimal

from integrations.payment.adapters import MockFailureAdapter, MockSuccessAdapter
from integrations.payments.base_adapter import PaymentResult, TenantPaymentContext
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.router import PaymentProviderRouter
from services.commerce.catalog import ProductType
from services.commerce.service import CommerceService
from shared.utils.entitlement import TenantEntitlementContext


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
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))

    commerce.add_product(
        product_id="p_course",
        tenant_id="tenant_1",
        sku="course-101",
        product_type=ProductType.COURSE,
        title="Course 101",
        price=Decimal("99.00"),
        currency="USD",
        metadata={"capability_id": "recommendation.basic"},
    )

    order, invoice = commerce.checkout_and_invoice_sync(
        session_id="sess_1",
        tenant_id="tenant_1",
        learner_id="learner_1",
        product_id="p_course",
        idempotency_key="idem_1",
    )

    assert order.status.value == "reconciled"
    assert invoice.state.value == "issued"
    assert invoice.invoice_type == "one_time"
    assert commerce.catalog.get_product("p_course") is not None
    assert commerce.checkout.get_order(order.order_id) is not None
    assert commerce.billing.get_invoice(invoice.invoice_id) is not None


def test_checkout_retries_and_idempotency() -> None:
    flaky = FlakyAdapter()
    router = PaymentProviderRouter({"US": "flaky"}, [flaky])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))
    commerce.add_product(
        product_id="p_bundle",
        tenant_id="tenant_2",
        sku="bundle-201",
        product_type=ProductType.BUNDLE,
        title="Bundle 201",
        price=Decimal("149.00"),
        currency="USD",
        metadata={"capability_id": "assessment.author"},
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
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))

    commerce.add_product(
        product_id="p_sub",
        tenant_id="tenant_3",
        sku="sub-301",
        product_type=ProductType.SUBSCRIPTION,
        title="Pro Subscription",
        price=Decimal("29.00"),
        currency="USD",
        metadata={"capability_id": "assessment.author"},
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


def test_capability_monetization_add_on_usage_and_plan_mapping() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))

    tenant = TenantEntitlementContext(
        tenant_id="tenant_monetize",
        plan_type="pro",
        add_ons=("ai_tutor_pack",),
        country_code="US",
        segment_id="academy",
    )
    commerce.entitlement_service.upsert_tenant_context(tenant)

    pro_mapping = commerce.monetization.plan_capability_mapping("pro")
    assert "assessment.author" in pro_mapping
    assert "learning.analytics.advanced" not in pro_mapping

    enterprise_mapping = commerce.monetization.plan_capability_mapping(" Enterprise ")
    assert "learning.analytics.advanced" in enterprise_mapping

    commerce.enable_capability_add_on(tenant_id="tenant_monetize", capability_id="learning.analytics.advanced")
    purchased = commerce.subscription_service.get_purchased_capability_add_ons("tenant_monetize")
    assert "learning.analytics.advanced" in purchased

    commerce.record_capability_usage(
        tenant_id="tenant_monetize",
        capability_id="learning.analytics.advanced",
        units=7,
    )
    charges = commerce.calculate_capability_charges(tenant)
    charge_map = {charge.capability_id: charge for charge in charges}

    assert charge_map["learning.analytics.advanced"].amount == Decimal("0.70")
    assert charge_map["learning.analytics.advanced"].units == 7
    assert charge_map["assessment.author"].amount == Decimal("29.00")


def test_pakistan_payment_router_connection_for_commerce_orchestration() -> None:
    from services.commerce.service import build_commerce_service_for_pakistan

    commerce = build_commerce_service_for_pakistan(default_provider="easypaisa")
    entry = commerce._payment_orchestrator.process_checkout_payment(
        idempotency_key="idem_pk_orch",
        tenant=TenantPaymentContext(tenant_id="tenant_pk_orch", country_code="PK"),
        amount=5000,
        currency="PKR",
    )

    assert entry.provider == "easypaisa"
