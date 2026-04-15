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


@dataclass(frozen=True)
class PaymentInitiationRequest:
    tenant_id: str
    amount: int
    currency: str
    reference_id: str | None = None
    return_url: str | None = None
    metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class PaymentInitiationResponse:
    provider: str
    transaction_id: str
    status: str
    payload: dict[str, object]


@dataclass(frozen=True)
class PaymentVerificationResponse:
    status: str
    transaction_id: str
    amount: int
    reference_id: str | None = None
