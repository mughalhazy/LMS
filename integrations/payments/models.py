from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


PaymentStatus = Literal["success", "failed", "pending"]


@dataclass(frozen=True)
class PaymentInitiationRequest:
    amount: int
    currency: str
    tenant_id: str
    reference_id: str | None = None
    return_url: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PaymentInitiationResponse:
    provider: str
    transaction_id: str
    status: PaymentStatus
    payload: dict[str, Any]


@dataclass(frozen=True)
class PaymentVerificationResponse:
    status: PaymentStatus
    transaction_id: str
    amount: int
    reference_id: str | None


class PaymentAdapter(Protocol):
    provider_key: str

    def initiate_payment(self, request: PaymentInitiationRequest) -> PaymentInitiationResponse:
        """Initiate a payment with the provider and return checkout payload."""

    def verify_payment(self, callback_data: dict[str, Any]) -> PaymentVerificationResponse:
        """Verify callback payload and normalize provider status semantics."""

    def get_status(self, transaction_id: str) -> PaymentVerificationResponse:
        """Fetch latest provider status for transaction."""
