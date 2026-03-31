from __future__ import annotations

import importlib.util
from pathlib import Path

from integrations.payment import (
    InMemoryInvoiceStore,
    MockFailureAdapter,
    MockSuccessAdapter,
    PaymentFlowService,
    PaymentProviderRouter,
)


def _load_subscription_module():
    module_path = Path("services/subscription-service/payment_integration.py")
    spec = importlib.util.spec_from_file_location("subscription_payment_integration", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_success_flow_links_payment_to_invoice() -> None:
    router = PaymentProviderRouter(
        tenant_provider_config={"tenant_success": "mock_success"},
        adapters=[MockSuccessAdapter(), MockFailureAdapter()],
    )
    service = PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())

    result = service.process_payment(amount=1500, tenant="tenant_success")

    assert result["status"] == "success"
    assert result["invoice_id"] is not None
    assert result["payment_id"] is not None
    assert result["invoice_payment_status"] == "paid"


def test_failure_flow_marks_invoice_payment_failed() -> None:
    router = PaymentProviderRouter(
        tenant_provider_config={"tenant_failure": "mock_failure"},
        adapters=[MockSuccessAdapter(), MockFailureAdapter()],
    )
    service = PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())

    result = service.process_payment(amount=1500, tenant="tenant_failure")

    assert result["status"] == "failure"
    assert result["payment_id"] is None
    assert result["invoice_id"] is not None
    assert result["invoice_payment_status"] == "payment_failed"


def test_subscription_entrypoint_supports_process_payment_signature() -> None:
    mod = _load_subscription_module()
    result = mod.process_payment(1500, "tenant_alpha")

    assert result["status"] == "success"
    assert result["invoice_id"] is not None


def test_no_provider_lock_in_with_runtime_config() -> None:
    mod = _load_subscription_module()
    service = mod.build_subscription_payment_service(
        tenant_provider_config={"tenant_dynamic": "mock_failure"}
    )

    result = service.process_payment(amount=2000, tenant="tenant_dynamic")
    assert result["status"] == "failure"
    assert result["provider"] == "mock_failure"


def test_country_based_payment_adapter_selection_from_config() -> None:
    router = PaymentProviderRouter(
        tenant_provider_config={"US": "mock_success", "DE": "mock_failure"},
        adapters=[MockSuccessAdapter(), MockFailureAdapter()],
    )

    us_adapter = router.resolve_for_country("us")
    de_adapter = router.resolve_for_country("DE")

    assert us_adapter.provider_key == "mock_success"
    assert de_adapter.provider_key == "mock_failure"
