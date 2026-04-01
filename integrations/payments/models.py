from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentInitiationPayload:
    amount: int
    tenant_id: str
    country_code: str
    invoice_id: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True)
class PaymentStatusPayload:
    payment_id: str
    tenant_id: str
    country_code: str
