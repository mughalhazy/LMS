from __future__ import annotations

from typing import Any

from integrations.payments.base_adapter import (
    PaymentResult,
    PaymentVerificationResult,
    TenantPaymentContext,
)


class RaastAdapter:
    provider_key = "raast"

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
            payment_id=f"rs_{tenant.tenant_id}_{invoice_id or 'manual'}_{amount}",
            provider=self.provider_key,
            invoice_id=invoice_id,
        )

    def verify_payment(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(
            ok=payment_id.startswith("rs_"),
            status="verified" if payment_id.startswith("rs_") else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if payment_id.startswith("rs_") else "verification_failed",
        )

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        if payload.get("provider") != self.provider_key:
            return None
        payment_id = str(payload.get("payment_id") or "")
        callback_status = str(payload.get("status") or "").lower()
        if not payment_id:
            return None
        return PaymentVerificationResult(
            ok=callback_status in {"success", "verified", "completed"},
            status="verified" if callback_status in {"success", "verified", "completed"} else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if callback_status in {"success", "verified", "completed"} else "callback_failed",
        )
