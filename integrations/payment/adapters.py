from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentRequest:
    amount: int
    tenant: str
    invoice_id: str


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    status: str
    payment_id: str | None = None
    provider: str | None = None
    error: str | None = None
    invoice_id: str | None = None


class PaymentAdapter(Protocol):
    """Provider adapter contract for processing payments."""

    provider_key: str

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        """Process a payment request and return a normalized result."""


class MockSuccessAdapter:
    provider_key = "mock_success"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        return PaymentResult(
            ok=True,
            status="success",
            payment_id=f"pay_{request.tenant}_{request.invoice_id}",
            provider=self.provider_key,
            invoice_id=request.invoice_id,
        )


class MockFailureAdapter:
    provider_key = "mock_failure"

    def process_payment(self, request: PaymentRequest) -> PaymentResult:
        return PaymentResult(
            ok=False,
            status="failure",
            provider=self.provider_key,
            error="provider_rejected",
            invoice_id=request.invoice_id,
        )
