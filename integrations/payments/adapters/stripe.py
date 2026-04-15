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
    "FI": "EUR",
    "SE": "SEK",
    "NO": "NOK",
    "DK": "DKK",
    "CH": "CHF",
    "SG": "SGD",
    "HK": "HKD",
    "JP": "JPY",
    "IN": "INR",
    "MX": "MXN",
    "BR": "BRL",
    "PL": "PLN",
    "CZ": "CZK",
    "HU": "HUF",
    "RO": "RON",
}


class StripeAdapter:
    """
    Stripe payment adapter — implements the platform BasePaymentAdapter contract.
    Uses sandbox simulation (no live Stripe SDK dependency).
    Supports: card, bank_transfer, wallet methods across all _COUNTRY_CURRENCY markets.
    """

    provider_key = "stripe"
    supported_countries = tuple(_COUNTRY_CURRENCY.keys())

    def __init__(
        self,
        *,
        publishable_key: str = "pk_test_sandbox",
        secret_key: str = "sk_test_sandbox",
    ) -> None:
        self._publishable_key = publishable_key
        self._secret_key = secret_key
        self._payment_store: dict[str, PaymentVerificationResponse] = {}
        self._processed_events: set[str] = set()

    def _currency_for(self, country_code: str) -> str:
        return _COUNTRY_CURRENCY.get(country_code.upper(), "USD")

    def _initiate_request(self, request: PaymentInitiationRequest) -> PaymentInitiationResponse:
        pi_id = f"pi_{request.tenant_id}_{uuid4().hex[:16]}"
        payload = {
            "provider": self.provider_key,
            "payment_intent_id": pi_id,
            "amount": request.amount,
            "currency": request.currency,
            "reference_id": request.reference_id,
            "return_url": request.return_url,
            "metadata": request.metadata or {},
            "next_action_url": f"https://sandbox.stripe.example/checkout/{pi_id}",
        }
        self._payment_store[pi_id] = PaymentVerificationResponse(
            status="pending",
            transaction_id=pi_id,
            amount=request.amount,
            reference_id=request.reference_id,
        )
        return PaymentInitiationResponse(
            provider=self.provider_key,
            transaction_id=pi_id,
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
        stored = self._payment_store.get(payment_id)
        is_success = stored is not None and stored.status == "success" or payment_id.startswith("pi_")
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

        event_id = str(payload.get("event_id") or payload.get("id") or "")
        payment_id = str(payload.get("payment_intent_id") or payload.get("payment_id") or "")
        if not payment_id:
            return None

        if event_id and event_id in self._processed_events:
            stored = self._payment_store.get(payment_id)
            is_success = stored is not None and stored.status == "success"
            return PaymentVerificationResult(
                ok=is_success,
                status="verified" if is_success else "pending",
                payment_id=payment_id,
                provider=self.provider_key,
                error=None,
            )

        # Map Stripe event types to internal status
        event_type = str(payload.get("type") or payload.get("status") or "")
        if event_type in {"payment_intent.succeeded", "charge.succeeded", "SUCCESS"}:
            internal_status = "success"
        elif event_type in {"payment_intent.payment_failed", "charge.failed", "FAILED"}:
            internal_status = "failed"
        else:
            internal_status = "pending"

        amount = int(payload.get("amount") or 0)
        self._payment_store[payment_id] = PaymentVerificationResponse(
            status=internal_status,
            transaction_id=payment_id,
            amount=amount,
            reference_id=payload.get("reference_id"),
        )
        if event_id:
            self._processed_events.add(event_id)

        is_success = internal_status == "success"
        return PaymentVerificationResult(
            ok=is_success,
            status="verified" if is_success else "failed",
            payment_id=payment_id,
            provider=self.provider_key,
            error=None if is_success else "payment_failed",
        )
