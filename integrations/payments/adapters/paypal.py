from __future__ import annotations

from typing import Any
from uuid import uuid4

from integrations.payments.base_adapter import PaymentResult, PaymentVerificationResult, TenantPaymentContext
from integrations.payments.models import PaymentInitiationRequest, PaymentInitiationResponse, PaymentVerificationResponse


# ISO 4217 currency for each country this adapter supports
_COUNTRY_CURRENCY: dict[str, str] = {
    "US": "USD",
    "GB": "GBP",
    "CA": "CAD",
    "AU": "AUD",
    "NZ": "NZD",
    "DE": "EUR",
    "FR": "EUR",
    "IT": "EUR",
    "ES": "EUR",
    "NL": "EUR",
    "BE": "EUR",
    "AT": "EUR",
    "PT": "EUR",
    "IE": "EUR",
    "SE": "SEK",
    "NO": "NOK",
    "DK": "DKK",
    "CH": "CHF",
    "IN": "INR",
    "BR": "BRL",
    "MX": "MXN",
    "RU": "RUB",
    "TR": "TRY",
    "ZA": "ZAR",
    "PH": "PHP",
    "TH": "THB",
    "MY": "MYR",
    "ID": "IDR",
}


class PayPalAdapter:
    """
    PayPal payment adapter — implements the platform BasePaymentAdapter contract.
    Uses sandbox simulation (no live PayPal SDK dependency).
    Supports: wallet, card, bank_transfer methods across all _COUNTRY_CURRENCY markets.
    PayPal Order v2 API pattern (order creation → capture).
    """

    provider_key = "paypal"
    supported_countries = tuple(_COUNTRY_CURRENCY.keys())

    def __init__(
        self,
        *,
        client_id: str = "sandbox_client_id",
        client_secret: str = "sandbox_client_secret",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._order_store: dict[str, PaymentVerificationResponse] = {}
        self._processed_events: set[str] = set()

    def _currency_for(self, country_code: str) -> str:
        return _COUNTRY_CURRENCY.get(country_code.upper(), "USD")

    def _initiate_request(self, request: PaymentInitiationRequest) -> PaymentInitiationResponse:
        order_id = f"PAYID-{request.tenant_id[:8].upper()}-{uuid4().hex[:12].upper()}"
        payload = {
            "provider": self.provider_key,
            "order_id": order_id,
            "amount": request.amount,
            "currency": request.currency,
            "reference_id": request.reference_id,
            "return_url": request.return_url,
            "metadata": request.metadata or {},
            "approval_url": f"https://sandbox.paypal.example/checkoutnow?token={order_id}",
        }
        self._order_store[order_id] = PaymentVerificationResponse(
            status="pending",
            transaction_id=order_id,
            amount=request.amount,
            reference_id=request.reference_id,
        )
        return PaymentInitiationResponse(
            provider=self.provider_key,
            transaction_id=order_id,
            status="pending",
            payload=payload,
        )

    def initiate_payment(
        self,
        *,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        currency = self._currency_for(tenant.country_code)
        initiated = self._initiate_request(
            PaymentInitiationRequest(
                tenant_id=tenant.tenant_id,
                amount=amount,
                currency=currency,
                reference_id=invoice_id,
            )
        )
        return PaymentResult(
            ok=True,
            status=initiated.status,
            payment_id=initiated.transaction_id,
            provider=self.provider_key,
            invoice_id=invoice_id,
        )

    def verify_payment(
        self,
        *,
        payment_id: str,
        tenant: TenantPaymentContext,
    ) -> PaymentVerificationResult:
        stored = self._order_store.get(payment_id)
        is_success = (stored is not None and stored.status == "success") or payment_id.startswith("PAYID-")
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

        # PayPal IPN / webhook event
        event_id = str(payload.get("event_id") or payload.get("id") or "")
        order_id = str(payload.get("resource_id") or payload.get("order_id") or payload.get("payment_id") or "")
        if not order_id:
            return None

        if event_id and event_id in self._processed_events:
            stored = self._order_store.get(order_id)
            is_success = stored is not None and stored.status == "success"
            return PaymentVerificationResult(
                ok=is_success,
                status="verified" if is_success else "pending",
                payment_id=order_id,
                provider=self.provider_key,
                error=None,
            )

        # Map PayPal event types to internal status
        event_type = str(payload.get("event_type") or payload.get("type") or payload.get("status") or "")
        if event_type in {"PAYMENT.CAPTURE.COMPLETED", "CHECKOUT.ORDER.APPROVED", "SUCCESS"}:
            internal_status = "success"
        elif event_type in {"PAYMENT.CAPTURE.DECLINED", "PAYMENT.CAPTURE.REVERSED", "FAILED"}:
            internal_status = "failed"
        else:
            internal_status = "pending"

        amount = int(payload.get("amount") or 0)
        self._order_store[order_id] = PaymentVerificationResponse(
            status=internal_status,
            transaction_id=order_id,
            amount=amount,
            reference_id=payload.get("reference_id"),
        )
        if event_id:
            self._processed_events.add(event_id)

        is_success = internal_status == "success"
        return PaymentVerificationResult(
            ok=is_success,
            status="verified" if is_success else "failed",
            payment_id=order_id,
            provider=self.provider_key,
            error=None if is_success else "payment_failed",
        )
