# ⚠ DEPRECATED — CGAP-076 / DF-04
# Canonical payment adapter path is `integrations/payments/` (plural).
# `integrations/payment/` (singular) is a legacy folder retained for backward
# compatibility only. All Pakistan adapters (JazzCash, EasyPaisa, Raast) and
# international adapters (Stripe, PayPal) are authoritative in:
#   integrations/payments/adapters/
# New code must import from `integrations.payments` — not this package.

from .adapters import MockFailureAdapter, MockSuccessAdapter
from .base_adapter import PaymentResult, TenantPaymentContext
from .easypaisa_adapter import EasyPaisaAdapter
from .flow import InMemoryInvoiceStore, PaymentFlowService
from .jazzcash_adapter import JazzCashAdapter
from .router import PaymentProviderRouter

__all__ = [
    "MockFailureAdapter",
    "MockSuccessAdapter",
    "PaymentResult",
    "TenantPaymentContext",
    "JazzCashAdapter",
    "EasyPaisaAdapter",
    "InMemoryInvoiceStore",
    "PaymentFlowService",
    "PaymentProviderRouter",
]
