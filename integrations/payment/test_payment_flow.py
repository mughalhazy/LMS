from __future__ import annotations

import importlib.util
from pathlib import Path

from integrations.payment import (
    EasyPaisaAdapter,
    InMemoryInvoiceStore,
    JazzCashAdapter,
    PaymentFlowService,
    PaymentProviderRouter,
    TenantPaymentContext,
)


def _load_subscription_module():
    module_path = Path("services/subscription-service/payment_integration.py")
    spec = importlib.util.spec_from_file_location("subscription_payment_integration", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_jazzcash_success_flow_links_payment_to_invoice() -> None:
    router = PaymentProviderRouter(
        country_provider_config={"PK": "jazzcash"},
        adapters=[JazzCashAdapter(), EasyPaisaAdapter()],
    )
    service = PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())

    result = service.process_payment(
        amount=1500,
        tenant=TenantPaymentContext(tenant_id="tenant_pk", country_code="PK"),
    )

    assert result["status"] == "success"
    assert result["provider"] == "jazzcash"
    assert result["invoice_id"] is not None
    assert result["payment_id"] is not None
    assert result["invoice_payment_status"] == "paid"


def test_easypaisa_success_flow_links_payment_to_invoice() -> None:
    router = PaymentProviderRouter(
        country_provider_config={"PK": "easypaisa"},
        adapters=[JazzCashAdapter(), EasyPaisaAdapter()],
    )
    service = PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())

    result = service.process_payment(
        amount=1500,
        tenant=TenantPaymentContext(tenant_id="tenant_pk", country_code="PK"),
    )

    assert result["status"] == "success"
    assert result["provider"] == "easypaisa"
    assert result["payment_id"] is not None
    assert result["invoice_id"] is not None
    assert result["invoice_payment_status"] == "paid"


def test_subscription_entrypoint_supports_process_payment_signature() -> None:
    mod = _load_subscription_module()
    result = mod.process_payment(1500, "tenant_alpha")

    assert result["status"] == "success"
    assert result["invoice_id"] is not None


def test_no_provider_lock_in_with_runtime_config() -> None:
    mod = _load_subscription_module()
    service = mod.build_subscription_payment_service(
        country_provider_config={"PK": "easypaisa"}
    )

    result = service.process_payment(
        amount=2000,
        tenant=TenantPaymentContext(tenant_id="tenant_dynamic", country_code="PK"),
    )
    assert result["status"] == "success"
    assert result["provider"] == "easypaisa"
