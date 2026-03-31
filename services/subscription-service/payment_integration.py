from __future__ import annotations

from integrations.payment import (
    InMemoryInvoiceStore,
    MockFailureAdapter,
    MockSuccessAdapter,
    PaymentFlowService,
    PaymentProviderRouter,
)


def build_subscription_payment_service(
    tenant_provider_config: dict[str, str] | None = None,
) -> PaymentFlowService:
    """Build subscription payment flow with pluggable provider adapters."""
    config = tenant_provider_config or {
        "tenant_alpha": "mock_success",
        "tenant_beta": "mock_failure",
    }
    router = PaymentProviderRouter(
        tenant_provider_config=config,
        adapters=[MockSuccessAdapter(), MockFailureAdapter()],
    )
    return PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())


def process_payment(amount: int, tenant: str) -> dict[str, str | int | None]:
    """Subscription service payment entrypoint.

    Required by task:
      process_payment(amount, tenant)
    """
    service = build_subscription_payment_service()
    return service.process_payment(amount=amount, tenant=tenant)
