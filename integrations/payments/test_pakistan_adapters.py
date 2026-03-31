from __future__ import annotations

from integrations.payments import (
    EasyPaisaAdapter,
    JazzCashAdapter,
    PaymentOrchestrationService,
    PaymentResult,
    RaastAdapter,
    TenantPaymentContext,
    build_pakistan_payment_router,
)
from integrations.payments.base_adapter import BasePaymentAdapter


def test_pakistan_adapters_are_isolated_by_provider_keys() -> None:
    adapters = [JazzCashAdapter(), EasyPaisaAdapter(), RaastAdapter()]
    assert [adapter.provider_key for adapter in adapters] == ["jazzcash", "easypaisa", "raast"]


def test_pakistan_router_resolves_raast() -> None:
    router = build_pakistan_payment_router(default_provider="raast")
    adapter = router.resolve(TenantPaymentContext(tenant_id="tenant_pk", country_code="PK"))
    result = adapter.process_payment(
        amount=5000,
        tenant=TenantPaymentContext(tenant_id="tenant_pk", country_code="PK"),
    )

    assert result.ok is True
    assert result.provider == "raast"
    assert result.payment_id is not None


class FlakyRetryAdapter:
    provider_key = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        self.calls += 1
        if self.calls == 1:
            return PaymentResult(
                ok=False,
                status="failure",
                provider=self.provider_key,
                error="timeout",
                invoice_id=invoice_id,
            )
        return PaymentResult(
            ok=True,
            status="success",
            provider=self.provider_key,
            payment_id=f"fl_{tenant.tenant_id}_{amount}",
            invoice_id=invoice_id,
        )


def test_orchestration_supports_retries_idempotency_and_async_verification() -> None:
    class InlineRouter:
        def __init__(self, adapter: BasePaymentAdapter) -> None:
            self._adapter = adapter

        def resolve(self, tenant: object) -> BasePaymentAdapter:
            return self._adapter

    adapter = FlakyRetryAdapter()
    orchestrator = PaymentOrchestrationService(router=InlineRouter(adapter), max_retries=2)
    tenant = TenantPaymentContext(tenant_id="tenant_pk", country_code="PK")

    first = orchestrator.process_checkout_payment(
        idempotency_key="idem_1",
        tenant=tenant,
        amount=7500,
        currency="PKR",
    )
    second = orchestrator.process_checkout_payment(
        idempotency_key="idem_1",
        tenant=tenant,
        amount=7500,
        currency="PKR",
    )

    assert first.payment_id is not None
    assert first.status == "pending_verification"
    assert second.payment_id == first.payment_id
    assert adapter.calls == 2

    import asyncio

    verified = asyncio.run(orchestrator.await_verification(idempotency_key="idem_1"))
    assert verified.verified is True
    assert verified.status == "verified"
    assert verified.verified_at is not None
