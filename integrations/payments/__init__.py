# CANONICAL payment adapter package — CGAP-076 / DF-04 resolved.
# All adapters (Pakistan + international) are in integrations/payments/adapters/.
# Legacy path integrations/payment/ (singular) is deprecated — see its __init__.py.

from integrations.payments.adapters import EasyPaisaAdapter, JazzCashAdapter, RaastAdapter, StripeAdapter, PayPalAdapter
from integrations.payments.base_adapter import PaymentResult, TenantPaymentContext
from integrations.payments.orchestration import (
    PaymentLedgerEntry,
    PaymentOrchestrationService,
    build_pakistan_payment_orchestration,
    build_pakistan_payment_router,
)
from integrations.payments.router import PaymentProviderRouter

__all__ = [
    "PaymentResult",
    "TenantPaymentContext",
    "PaymentProviderRouter",
    "PaymentLedgerEntry",
    "PaymentOrchestrationService",
    "JazzCashAdapter",
    "EasyPaisaAdapter",
    "RaastAdapter",
    "StripeAdapter",
    "PayPalAdapter",
    "build_pakistan_payment_router",
    "build_pakistan_payment_orchestration",
]
