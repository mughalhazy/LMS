from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integrations.payments.base_adapter import (
    PaymentResult,
    PaymentVerificationResult,
    TenantPaymentContext,
)


class RaastAdapter:
    provider_key = "raast"

    @dataclass(frozen=True)
    class _RaastPaymentRecord:
        payment_id: str
        reference_id: str
        status: str
        amount: int
        invoice_id: str | None

    def __init__(self) -> None:
        self._records_by_reference: dict[str, RaastAdapter._RaastPaymentRecord] = {}

    def initiate_payment(
        self,
        *,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
        transfer_reference: str | None = None,
    ) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                ok=False,
                status="failure",
                provider=self.provider_key,
                error="invalid_amount",
                invoice_id=invoice_id,
            )

        reference = transfer_reference or f"rref_{tenant.tenant_id}_{invoice_id or 'manual'}_{amount}"
        payment_id = f"rs_{reference}"
        record = self._RaastPaymentRecord(
            payment_id=payment_id,
            reference_id=reference,
            status="verified",
            amount=amount,
            invoice_id=invoice_id,
        )
        self._records_by_reference[reference] = record

        return PaymentResult(
            ok=True,
            status="success",
            payment_id=payment_id,
            provider=self.provider_key,
            invoice_id=invoice_id,
        )

    def _status_from_reference(self, *, reference_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        _ = tenant
        record = self._records_by_reference.get(reference_id)
        if record is None:
            return PaymentVerificationResult(
                ok=False,
                status="failed",
                payment_id=f"rs_{reference_id}",
                provider=self.provider_key,
                error="reference_not_found",
            )

        return PaymentVerificationResult(
            ok=record.status in {"verified", "success", "completed"},
            status="verified" if record.status in {"verified", "success", "completed"} else "failed",
            payment_id=record.payment_id,
            provider=self.provider_key,
            error=None if record.status in {"verified", "success", "completed"} else "verification_failed",
        )

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        return self.initiate_payment(
            amount=amount,
            tenant=tenant,
            invoice_id=invoice_id,
        )

    def verify_payment(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        reference_id = payment_id.removeprefix("rs_")
        by_reference = self._status_from_reference(reference_id=reference_id, tenant=tenant)
        if by_reference.error != "reference_not_found":
            return by_reference

        return PaymentVerificationResult(
            ok=payment_id.startswith("rs_"),
            status="verified" if payment_id.startswith("rs_") else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if payment_id.startswith("rs_") else "verification_failed",
        )
    def get_status(
        self,
        *,
        payment_id: str | None = None,
        reference_id: str | None = None,
        tenant: TenantPaymentContext,
    ) -> PaymentVerificationResult:
        resolved_reference = reference_id
        if resolved_reference is None and payment_id is not None:
            resolved_reference = payment_id.removeprefix("rs_")
        if resolved_reference is None:
            return PaymentVerificationResult(
                ok=False,
                status="failed",
                payment_id=payment_id or "rs_unknown",
                provider=self.provider_key,
                error="missing_reference_or_payment_id",
            )
        return self._status_from_reference(reference_id=resolved_reference, tenant=tenant)

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        if payload.get("provider") != self.provider_key:
            return None
        payment_id = str(payload.get("payment_id") or "")
        callback_status = str(payload.get("status") or "").lower()
        if not payment_id:
            return None
        reference_id = payment_id.removeprefix("rs_")
        existing = self._records_by_reference.get(reference_id)
        if existing is not None:
            self._records_by_reference[reference_id] = self._RaastPaymentRecord(
                payment_id=existing.payment_id,
                reference_id=existing.reference_id,
                status="verified" if callback_status in {"success", "verified", "completed"} else "failed",
                amount=existing.amount,
                invoice_id=existing.invoice_id,
            )
        return PaymentVerificationResult(
            ok=callback_status in {"success", "verified", "completed"},
            status="verified" if callback_status in {"success", "verified", "completed"} else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if callback_status in {"success", "verified", "completed"} else "callback_failed",
        )
