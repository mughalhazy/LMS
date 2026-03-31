from __future__ import annotations

from integrations.payments.adapters import EasyPaisaAdapter, JazzCashAdapter, RaastAdapter
from integrations.payments.router import PaymentProviderRouter


def build_pakistan_payment_router(default_provider: str = "jazzcash") -> PaymentProviderRouter:
    """Commerce orchestration entrypoint for Pakistan-specific provider routing."""
    return PaymentProviderRouter(
        country_provider_config={"PK": default_provider},
        adapters=[JazzCashAdapter(), EasyPaisaAdapter(), RaastAdapter()],
    )
