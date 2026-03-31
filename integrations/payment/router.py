from __future__ import annotations

from .adapters import PaymentAdapter


class PaymentProviderRouter:
    """Tenant-configured payment provider selection (no hardcoded provider)."""

    def __init__(self, tenant_provider_config: dict[str, str], adapters: list[PaymentAdapter]) -> None:
        self._tenant_provider_config = tenant_provider_config
        self._adapters = {adapter.provider_key: adapter for adapter in adapters}

    def resolve(self, tenant: str) -> PaymentAdapter:
        provider_key = self._tenant_provider_config.get(tenant)
        if not provider_key:
            raise ValueError(f"No payment provider configured for tenant '{tenant}'")
        adapter = self._adapters.get(provider_key)
        if adapter is None:
            raise ValueError(f"Provider '{provider_key}' is not registered")
        return adapter
