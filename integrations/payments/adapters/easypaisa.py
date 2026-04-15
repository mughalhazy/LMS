from __future__ import annotations

import hashlib
from typing import Any

from integrations.payments.base_adapter import (
    PaymentResult,
    PaymentVerificationResult,
    TenantPaymentContext,
)
from integrations.payments.models import PaymentInitiationPayload, PaymentStatusPayload


class EasyPaisaAdapter:
    provider_key = "easypaisa"

    def __init__(self) -> None:
        self._initiations_by_idempotency_key: dict[str, PaymentResult] = {}
        self._status_by_payment_id: dict[str, str] = {}

    def _initiate_with_payload(self, payload: PaymentInitiationPayload) -> PaymentResult:
        if payload.amount <= 0:
            return PaymentResult(
                ok=False,
                status="failure",
                provider=self.provider_key,
                error="invalid_amount",
                invoice_id=payload.invoice_id,
            )

        if payload.idempotency_key:
            existing = self._initiations_by_idempotency_key.get(payload.idempotency_key)
            if existing is not None:
                return existing

        idempotency_segment = payload.idempotency_key or "manual"
        digest = hashlib.sha1(idempotency_segment.encode("utf-8")).hexdigest()[:12]
        payment_id = f"ep_{payload.tenant_id}_{payload.invoice_id or 'manual'}_{payload.amount}_{digest}"
        result = PaymentResult(
            ok=True,
            status="success",
            payment_id=payment_id,
            provider=self.provider_key,
            invoice_id=payload.invoice_id,
        )
        self._status_by_payment_id[payment_id] = "pending"
        if payload.idempotency_key:
            self._initiations_by_idempotency_key[payload.idempotency_key] = result
        return result

    def initiate_payment(
        self,
        *,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        return self._initiate_with_payload(
            PaymentInitiationPayload(
                amount=amount,
                tenant_id=tenant.tenant_id,
                country_code=tenant.country_code,
                invoice_id=invoice_id,
                idempotency_key=None,
            )
        )

    def verify_payment(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        callback_status = self.get_status(
            PaymentStatusPayload(
                payment_id=payment_id,
                tenant_id=tenant.tenant_id,
                country_code=tenant.country_code,
            )
        )
        is_verified = callback_status == "verified"
        return PaymentVerificationResult(
            ok=is_verified,
            status="verified" if is_verified else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if is_verified else "verification_failed",
        )

    def get_status(self, payload: PaymentStatusPayload) -> str:
        existing = self._status_by_payment_id.get(payload.payment_id)
        if existing == "verified":
            return "verified"
        if payload.payment_id.startswith("ep_"):
            return "verified"
        return "failed"

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        if payload.get("provider") != self.provider_key:
            return None
        payment_id = str(payload.get("payment_id") or "")
        callback_status = str(payload.get("status") or "").lower()
        callback_signature = str(payload.get("signature") or "")
        if not payment_id:
            return None

        expected_signature = hashlib.sha256(f"{self.provider_key}:{payment_id}:{callback_status}".encode("utf-8")).hexdigest()
        if callback_signature and callback_signature != expected_signature:
            return PaymentVerificationResult(
                ok=False,
                status="failed",
                payment_id=payment_id,
                provider=self.provider_key,
                error="invalid_callback_signature",
            )

        is_success = callback_status in {"success", "verified", "completed"}
        if is_success:
            self._status_by_payment_id[payment_id] = "verified"
        return PaymentVerificationResult(
            ok=is_success,
            status="verified" if is_success else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if is_success else "callback_failed",
        )
