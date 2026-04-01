from __future__ import annotations

from integrations.payments.base_adapter import PaymentResult, PaymentVerificationResult, TenantPaymentContext


class MockSuccessAdapter:
    provider_key = "mock_success"

    def initiate(self, *, amount: int, tenant: TenantPaymentContext, invoice_id: str | None = None) -> PaymentResult:
        return PaymentResult(
            ok=True,
            status="success",
            payment_id=f"pay_{tenant.tenant_id}_{invoice_id or 'manual'}",
            provider=self.provider_key,
            invoice_id=invoice_id,
        )

    def verify(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(ok=True, status="verified", payment_id=payment_id, provider=self.provider_key)

    def reconcile(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return self.verify(payment_id=payment_id, tenant=tenant)


class MockFailureAdapter:
    provider_key = "mock_failure"

    def initiate(self, *, amount: int, tenant: TenantPaymentContext, invoice_id: str | None = None) -> PaymentResult:
        return PaymentResult(
            ok=False,
            status="failure",
            provider=self.provider_key,
            error="provider_rejected",
            invoice_id=invoice_id,
        )

    def verify(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(
            ok=False,
            status="failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error="provider_rejected",
        )

    def reconcile(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return self.verify(payment_id=payment_id, tenant=tenant)
