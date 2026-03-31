from __future__ import annotations

from integrations.payments.base_adapter import BasePaymentAdapter, normalize_tenant


class PaymentProviderRouter:
    """Country-configured payment provider selection with isolated adapters."""

    def __init__(self, country_provider_config: dict[str, str], adapters: list[BasePaymentAdapter]) -> None:
        self._country_provider_config = country_provider_config
        self._adapters = {adapter.provider_key: adapter for adapter in adapters}

    def resolve(self, tenant: object) -> BasePaymentAdapter:
        tenant_context = normalize_tenant(tenant)
        provider_key = self._country_provider_config.get(tenant_context.country_code)
        if not provider_key:
            raise ValueError(
                f"No payment provider configured for country '{tenant_context.country_code}'"
            )
        adapter = self._adapters.get(provider_key)
        if adapter is None:
            raise ValueError(f"Provider '{provider_key}' is not registered")
        return adapter
