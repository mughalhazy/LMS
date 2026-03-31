from __future__ import annotations

from integrations.payment import (
    EasyPaisaAdapter,
    InMemoryInvoiceStore,
    JazzCashAdapter,
    PaymentFlowService,
    PaymentProviderRouter,
    TenantPaymentContext,
)


class Tenant:
    def __init__(self, tenant_id: str, country_code: str) -> None:
        self.tenant_id = tenant_id
        self.country_code = country_code


def build_subscription_payment_service(
    country_provider_config: dict[str, str] | None = None,
) -> PaymentFlowService:
    """Build subscription payment flow with pluggable provider adapters."""
    config = country_provider_config or {
        "PK": "jazzcash",
    }
    router = PaymentProviderRouter(
        country_provider_config=config,
        adapters=[JazzCashAdapter(), EasyPaisaAdapter()],
    )
    return PaymentFlowService(router=router, invoice_store=InMemoryInvoiceStore())


def process_payment(amount: int, tenant: str | Tenant | TenantPaymentContext) -> dict[str, str | int | None]:
    """Subscription service payment entrypoint.

    Required by task:
      process_payment(amount, tenant)
    """
    service = build_subscription_payment_service()
    tenant_payload = (
        TenantPaymentContext(tenant_id=tenant, country_code="PK") if isinstance(tenant, str) else tenant
    )
    result = service.process_payment(amount=amount, tenant=tenant_payload)
    if result.get("status") == "failure":
        result["event_type"] = "billing.missed_payment"
        result["workflow_action"] = "reminder"
    return result
