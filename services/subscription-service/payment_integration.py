from __future__ import annotations

from integrations.payments import (
    EasyPaisaAdapter,
    JazzCashAdapter,
    PaymentOrchestrationService,
    PaymentProviderRouter,
    TenantPaymentContext,
)


class Tenant:
    def __init__(self, tenant_id: str, country_code: str) -> None:
        self.tenant_id = tenant_id
        self.country_code = country_code


def build_subscription_payment_service(
    country_provider_config: dict[str, str] | None = None,
) -> PaymentOrchestrationService:
    config = country_provider_config or {"PK": "jazzcash"}
    router = PaymentProviderRouter(
        country_provider_config=config,
        adapters=[JazzCashAdapter(), EasyPaisaAdapter()],
    )
    return PaymentOrchestrationService(router=router)


def initiate(
    amount: int,
    tenant: str | Tenant | TenantPaymentContext,
) -> dict[str, str | int | None]:
    service = build_subscription_payment_service()
    tenant_context = tenant
    if isinstance(tenant, str):
        tenant_context = TenantPaymentContext(tenant_id=tenant, country_code="PK")

    entry = service.process_checkout_payment(
        idempotency_key=f"subscription:{tenant_context.tenant_id}:{amount}",
        tenant=tenant_context,
        amount=amount,
        currency="PKR",
    )
    result = {
        "status": "success" if entry.status == "reconciled" else "failure",
        "provider": entry.provider,
        "payment_id": entry.payment_id,
        "amount": amount,
    }
    if result["status"] == "failure":
        result["event_type"] = "billing.missed_payment"
        result["workflow_action"] = "reminder"
    return result
