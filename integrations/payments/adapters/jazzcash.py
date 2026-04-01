from __future__ import annotations

import hashlib
import hmac
from typing import Any
from uuid import uuid4

from integrations.payments.base_adapter import PaymentResult, PaymentVerificationResult, TenantPaymentContext
from integrations.payments.models import PaymentInitiationRequest, PaymentInitiationResponse, PaymentVerificationResponse


class JazzCashAdapter:
    provider_key = "jazzcash"

    def __init__(self, *, merchant_id: str = "sandbox_merchant", secret_key: str = "sandbox_secret") -> None:
        self._merchant_id = merchant_id
        self._secret_key = secret_key
        self._transaction_store: dict[str, PaymentVerificationResponse] = {}
        self._processed_callbacks: set[str] = set()

    def initiate_payment(self, request: PaymentInitiationRequest) -> PaymentInitiationResponse:
        transaction_id = f"jz_{request.tenant_id}_{uuid4().hex[:16]}"
        payload = {
            "provider": self.provider_key,
            "merchant_id": self._merchant_id,
            "transaction_id": transaction_id,
            "amount": request.amount,
            "currency": request.currency,
            "reference_id": request.reference_id,
            "return_url": request.return_url,
            "metadata": request.metadata or {},
            "redirect_url": f"https://sandbox.jazzcash.example/checkout/{transaction_id}",
        }
        self._transaction_store[transaction_id] = PaymentVerificationResponse(
            status="pending",
            transaction_id=transaction_id,
            amount=request.amount,
            reference_id=request.reference_id,
        )
        return PaymentInitiationResponse(
            provider=self.provider_key,
            transaction_id=transaction_id,
            status="pending",
            payload=payload,
        )

    def verify_payment(
        self,
        callback_data: dict[str, Any] | None = None,
        *,
        payment_id: str | None = None,
        tenant: TenantPaymentContext | None = None,
    ) -> PaymentVerificationResponse | PaymentVerificationResult:
        if callback_data is not None:
            return self._verify_callback(callback_data)

        if payment_id is None or tenant is None:
            raise TypeError("verify_payment requires callback_data or legacy payment_id + tenant")

        status = self.get_status(payment_id)
        is_success = status.status == "success" or payment_id.startswith("jz_")
        return PaymentVerificationResult(
            ok=is_success,
            status="verified" if is_success else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if is_success else "verification_failed",
        )


    def get_status(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return self.verify_payment(payment_id=payment_id, tenant=tenant)

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        if payload.get("provider") != self.provider_key:
            return None

        transaction_id = str(payload.get("payment_id") or payload.get("transaction_id") or "")
        if not transaction_id:
            return None

        verification = self._verify_callback(
            {
                "transaction_id": transaction_id,
                "amount": int(payload.get("amount") or 0),
                "reference_id": payload.get("reference_id"),
                "status": str(payload.get("status") or "UNKNOWN"),
                "callback_id": payload.get("callback_id"),
                "signature": payload.get("signature"),
            }
        )
        is_success = verification.status == "success"
        return PaymentVerificationResult(
            ok=is_success,
            status="verified" if is_success else "failed",
            payment_id=verification.transaction_id,
            provider=self.provider_key,
            error=None if is_success else "callback_failed",
        )

    def _verify_callback(self, callback_data: dict[str, Any]) -> PaymentVerificationResponse:
        self._validate_callback_payload(callback_data)

        transaction_id = str(callback_data["transaction_id"])
        amount = int(callback_data["amount"])
        reference_id = self._normalize_reference_id(callback_data.get("reference_id"))

        callback_key = str(callback_data.get("callback_id") or callback_data.get("event_id") or "")
        if callback_key and callback_key in self._processed_callbacks:
            return self._transaction_store.get(
                transaction_id,
                PaymentVerificationResponse(status="pending", transaction_id=transaction_id, amount=amount, reference_id=reference_id),
            )

        self._validate_signature_if_present(callback_data)
        verification = PaymentVerificationResponse(
            status=self._map_status(str(callback_data.get("status") or "UNKNOWN")),
            transaction_id=transaction_id,
            amount=amount,
            reference_id=reference_id,
        )
        self._transaction_store[transaction_id] = verification
        if callback_key:
            self._processed_callbacks.add(callback_key)
        return verification

    @staticmethod
    def _map_status(raw_status: str) -> str:
        status = raw_status.upper()
        if status == "SUCCESS":
            return "success"
        if status == "FAILED":
            return "failed"
        return "pending"

    def _validate_callback_payload(self, callback_data: dict[str, Any]) -> None:
        required_fields = {"transaction_id", "amount", "status"}
        missing = [field for field in required_fields if field not in callback_data]
        if missing:
            raise ValueError(f"missing_callback_fields:{','.join(sorted(missing))}")

    def _validate_signature_if_present(self, callback_data: dict[str, Any]) -> None:
        signature = callback_data.get("signature")
        if not signature:
            return
        message = f"{callback_data['transaction_id']}|{callback_data['amount']}|{callback_data['status']}"
        expected = hmac.new(self._secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(signature), expected):
            raise ValueError("invalid_signature")

    @staticmethod
    def _normalize_reference_id(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value)
        return normalized or None
