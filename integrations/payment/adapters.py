from __future__ import annotations

from .base_adapter import BasePaymentAdapter as PaymentAdapter
from .base_adapter import PaymentResult, TenantPaymentContext


class MockSuccessAdapter:
    provider_key = "mock_success"

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        return PaymentResult(
            ok=True,
            status="success",
            payment_id=f"pay_{tenant.tenant_id}_{invoice_id or 'manual'}",
            provider=self.provider_key,
            invoice_id=invoice_id,
        )


class MockFailureAdapter:
    provider_key = "mock_failure"

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        return PaymentResult(
            ok=False,
            status="failure",
            provider=self.provider_key,
            error="provider_rejected",
            invoice_id=invoice_id,
        )
