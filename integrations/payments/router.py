from __future__ import annotations

from typing import Any

from integrations.payments.base_adapter import (
    BasePaymentAdapter,
    PaymentResult,
    PaymentVerificationResult,
    TenantPaymentContext,
    normalize_tenant,
)


class PaymentProviderRouter:
    """Country-configured payment provider selection with isolated adapters."""

    def __init__(self, country_provider_config: dict[str, str], adapters: list[BasePaymentAdapter]) -> None:
        self._country_provider_config = country_provider_config
        self._adapters = {adapter.provider_key: adapter for adapter in adapters}

    def resolve_provider(self, tenant: object) -> str:
        tenant_context = normalize_tenant(tenant)
        provider_key = self._country_provider_config.get(tenant_context.country_code)
        if not provider_key:
            raise ValueError(
                f"No payment provider configured for country '{tenant_context.country_code}'"
            )
        if provider_key not in self._adapters:
            raise ValueError(f"Provider '{provider_key}' is not registered")
        return provider_key

    def process_checkout(
        self,
        *,
        tenant: object,
        amount: int,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        tenant_context = normalize_tenant(tenant)
        provider_key = self.resolve_provider(tenant_context)
        adapter = self._adapters[provider_key]
        return adapter.process_payment(amount=amount, tenant=tenant_context, invoice_id=invoice_id)

    def verify(
        self,
        *,
        tenant: TenantPaymentContext,
        provider: str,
        payment_id: str,
    ) -> PaymentVerificationResult:
        adapter = self._adapters.get(provider)
        if adapter is None:
            return PaymentVerificationResult(
                ok=False,
                status="failed",
                payment_id=payment_id,
                provider=provider,
                error="provider_not_registered",
            )
        return adapter.verify_payment(payment_id=payment_id, tenant=tenant)

    def parse_callback(self, *, provider: str, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        adapter = self._adapters.get(provider)
        if adapter is None:
            return None
        return adapter.parse_callback(payload)
