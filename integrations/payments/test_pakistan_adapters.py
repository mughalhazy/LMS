from __future__ import annotations

from integrations.payments import (
    EasyPaisaAdapter,
    JazzCashAdapter,
    RaastAdapter,
    TenantPaymentContext,
    build_pakistan_payment_router,
)


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
