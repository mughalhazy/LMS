from __future__ import annotations

from .base_adapter import BasePaymentAdapter as PaymentAdapter
from .base_adapter import PaymentResult, TenantPaymentContext


class MockSuccessAdapter:
    provider_key = "mock_success"

    def initiate_payment(
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

    def verify_payment(self, payment_id: str, tenant: TenantPaymentContext) -> PaymentResult:
        return PaymentResult(ok=True, status="verified", payment_id=payment_id, provider=self.provider_key)

    def get_status(self, payment_id: str, tenant: TenantPaymentContext) -> PaymentResult:
        return self.verify_payment(payment_id=payment_id, tenant=tenant)


class MockFailureAdapter:
    provider_key = "mock_failure"

    def initiate_payment(
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

    def verify_payment(self, payment_id: str, tenant: TenantPaymentContext) -> PaymentResult:
        return PaymentResult(
            ok=False,
            status="failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error="provider_rejected",
        )

    def get_status(self, payment_id: str, tenant: TenantPaymentContext) -> PaymentResult:
        return self.verify_payment(payment_id=payment_id, tenant=tenant)
