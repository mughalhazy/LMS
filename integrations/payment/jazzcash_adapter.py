from __future__ import annotations

from .base_adapter import PaymentResult, TenantPaymentContext


class JazzCashAdapter:
    provider_key = "jazzcash"

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                ok=False,
                status="failure",
                provider=self.provider_key,
                error="invalid_amount",
                invoice_id=invoice_id,
            )

        return PaymentResult(
            ok=True,
            status="success",
            payment_id=f"jz_{tenant.tenant_id}_{invoice_id or 'manual'}_{amount}",
            provider=self.provider_key,
            invoice_id=invoice_id,
        )
