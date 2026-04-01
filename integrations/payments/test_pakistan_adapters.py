from __future__ import annotations

import asyncio
from typing import Any

from integrations.payments import (
    EasyPaisaAdapter,
    JazzCashAdapter,
    PaymentOrchestrationService,
    PaymentResult,
    RaastAdapter,
    TenantPaymentContext,
    build_pakistan_payment_router,
)
from integrations.payments.base_adapter import BasePaymentAdapter, PaymentVerificationResult


def test_pakistan_adapters_are_isolated_by_provider_keys() -> None:
    adapters = [JazzCashAdapter(), EasyPaisaAdapter(), RaastAdapter()]
    assert [adapter.provider_key for adapter in adapters] == ["jazzcash", "easypaisa", "raast"]


def test_pakistan_router_processes_checkout_and_verification() -> None:
    router = build_pakistan_payment_router(default_provider="raast")
    tenant = TenantPaymentContext(tenant_id="tenant_pk", country_code="PK")
    result = router.process_checkout(
        amount=5000,
        tenant=tenant,
    )

    assert result.ok is True
    assert result.provider == "raast"
    assert result.payment_id is not None

    verification = router.verify(tenant=tenant, provider="raast", payment_id=result.payment_id)
    assert verification.ok is True
    assert verification.status == "verified"


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

    def verify_payment(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(
            ok=payment_id.startswith("fl_"),
            status="verified" if payment_id.startswith("fl_") else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None,
        )

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        if payload.get("provider") != self.provider_key:
            return None
        payment_id = str(payload.get("payment_id") or "")
        if not payment_id:
            return None
        return PaymentVerificationResult(
            ok=str(payload.get("status") or "").lower() == "success",
            status="verified" if str(payload.get("status") or "").lower() == "success" else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None,
        )


def test_orchestration_supports_retries_idempotency_and_async_verification() -> None:
    class InlineRouter:
        def __init__(self, adapter: BasePaymentAdapter) -> None:
            self._adapter = adapter

        def process_checkout(
            self,
            *,
            tenant: object,
            amount: int,
            invoice_id: str | None = None,
        ) -> PaymentResult:
            assert isinstance(tenant, TenantPaymentContext)
            return self._adapter.process_payment(amount=amount, tenant=tenant, invoice_id=invoice_id)

        def verify(
            self,
            *,
            tenant: TenantPaymentContext,
            provider: str,
            payment_id: str,
        ) -> PaymentVerificationResult:
            return self._adapter.verify_payment(payment_id=payment_id, tenant=tenant)

        def parse_callback(self, *, provider: str, payload: dict[str, Any]) -> PaymentVerificationResult | None:
            return self._adapter.parse_callback(payload)

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

    verified = asyncio.run(orchestrator.await_verification(idempotency_key="idem_1"))
    assert verified.verified is True
    assert verified.status == "verified"
    assert verified.verified_at is not None


def test_orchestration_accepts_async_callback() -> None:
    orchestrator = PaymentOrchestrationService(router=build_pakistan_payment_router(default_provider="jazzcash"))
    tenant = TenantPaymentContext(tenant_id="tenant_pk", country_code="PK")
    created = orchestrator.process_checkout_payment(
        idempotency_key="idem_callback",
        tenant=tenant,
        amount=9000,
        currency="PKR",
    )

    assert created.payment_id is not None

    updated = asyncio.run(
        orchestrator.handle_provider_callback(
            provider="jazzcash",
            payload={"provider": "jazzcash", "payment_id": created.payment_id, "status": "success"},
        )
    )

    assert updated is not None
    assert updated.status == "verified"
    assert updated.verified is True


def test_callback_routes_to_verify_and_emits_payment_verified_event() -> None:
    class VerifyingRouter:
        def __init__(self) -> None:
            self.verify_calls = 0

        def process_checkout(self, *, tenant: object, amount: int, invoice_id: str | None = None) -> PaymentResult:
            assert isinstance(tenant, TenantPaymentContext)
            return PaymentResult(ok=True, status="success", provider="jazzcash", payment_id="jz_txn_1", invoice_id=invoice_id)

        def verify(self, *, tenant: TenantPaymentContext, provider: str, payment_id: str) -> PaymentVerificationResult:
            self.verify_calls += 1
            return PaymentVerificationResult(ok=True, status="verified", payment_id=payment_id, provider=provider, error=None)

        def parse_callback(self, *, provider: str, payload: dict[str, Any]) -> PaymentVerificationResult | None:
            return PaymentVerificationResult(ok=True, status="verified", payment_id=str(payload["payment_id"]), provider=provider, error=None)

    router = VerifyingRouter()
    orchestrator = PaymentOrchestrationService(router=router)
    tenant = TenantPaymentContext(tenant_id="user_123", country_code="PK")
    created = orchestrator.process_checkout_payment(idempotency_key="idem_evt_1", tenant=tenant, amount=2000, currency="PKR", invoice_id="ord_123")

    updated = asyncio.run(
        orchestrator.handle_provider_callback(
            provider="jazzcash",
            payload={"provider": "jazzcash", "payment_id": created.payment_id, "status": "success", "user_id": "user_123", "order_id": "ord_123"},
        )
    )

    assert updated is not None
    assert router.verify_calls == 1
    events = orchestrator.get_emitted_payment_verified_events()
    assert len(events) == 1
    assert events[0].transaction_id == created.payment_id
    assert events[0].status == "verified"
    assert events[0].user_id == "user_123"
    assert events[0].order_id == "ord_123"


def test_duplicate_callback_is_idempotent_and_duplicate_safe() -> None:
    orchestrator = PaymentOrchestrationService(router=build_pakistan_payment_router(default_provider="jazzcash"))
    payment_id = "jz_duplicate_1"

    first = asyncio.run(
        orchestrator.handle_provider_callback(
            provider="jazzcash",
            payload={"provider": "jazzcash", "payment_id": payment_id, "status": "success", "user_id": "user_duplicate", "order_id": "order_duplicate"},
        )
    )
    second = asyncio.run(
        orchestrator.handle_provider_callback(
            provider="jazzcash",
            payload={"provider": "jazzcash", "payment_id": payment_id, "status": "success", "user_id": "user_duplicate", "order_id": "order_duplicate"},
        )
    )

    assert first is not None and second is not None
    assert first.status == "verified"
    assert second.status == "verified"
    events = orchestrator.get_emitted_payment_verified_events()
    assert len(events) == 1
    assert events[0].transaction_id == payment_id
