"""Pakistan payment provider integration layer.

Implements PaymentOrchestrationService and PakistanPaymentRouter for
JazzCash and Easypaisa callback handling and payment initiation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class PaymentVerifiedEvent:
    transaction_id: str
    status: str
    user_id: str
    order_id: str | None


@dataclass
class PaymentInitiatedEvent:
    payment_id: str
    provider: str
    redirect_url: str
    status: str = "pending"


class PakistanPaymentRouter:
    """Resolves payment method to JazzCash or Easypaisa provider."""

    _PROVIDER_MAP: dict[str, str] = {
        "jazzcash": "jazzcash",
        "easypaisa": "easypaisa",
        "mobile_money": "jazzcash",   # default for generic mobile_money
        "mobile_wallet": "jazzcash",
    }

    def resolve_provider(self, payment_method: str) -> str:
        return self._PROVIDER_MAP.get(payment_method.lower(), "jazzcash")

    def supported_providers(self) -> list[str]:
        return ["jazzcash", "easypaisa"]


class PaymentOrchestrationService:
    """Orchestrates payment operations across Pakistan payment providers."""

    def __init__(self, router: PakistanPaymentRouter) -> None:
        self._router = router
        self._verified_events: list[PaymentVerifiedEvent] = []
        self._initiated_events: list[PaymentInitiatedEvent] = []

    async def handle_provider_callback(
        self, *, provider: str, payload: dict[str, Any]
    ) -> Any | None:
        """Process inbound payment callback from JazzCash or Easypaisa.

        Normalizes provider status string to a platform-standard verified/failed
        state and emits a PaymentVerifiedEvent.
        """
        payment_id = str(payload.get("payment_id") or "").strip()
        if not payment_id:
            return None

        raw_status = str(payload.get("status") or "").upper()
        verified = raw_status in {"SUCCESS", "COMPLETED", "PAID", "00"}

        event = PaymentVerifiedEvent(
            transaction_id=payment_id,
            status="verified" if verified else "failed",
            user_id=str(payload.get("user_id") or ""),
            order_id=payload.get("order_id"),
        )
        self._verified_events.append(event)

        class _Result:
            pass

        result = _Result()
        result.verified = verified  # type: ignore[attr-defined]
        return result

    async def initiate_payment(
        self,
        *,
        provider: str,
        order_id: str,
        user_id: str,
        amount: float,
        currency: str,
        payment_method: str,
        tenant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentInitiatedEvent:
        """Initiate a payment request with the selected provider.

        In production this would call the provider's payment creation API.
        Returns a payment_id and redirect URL / deeplink for the buyer.
        """
        payment_id = str(uuid4())

        # Provider-specific redirect construction.
        # Production implementation replaces these with real provider API calls.
        if provider == "jazzcash":
            redirect_url = (
                f"jazzcash://pay?payment_id={payment_id}"
                f"&amount={amount}&currency={currency}&order_id={order_id}"
            )
        elif provider == "easypaisa":
            redirect_url = (
                f"easypaisa://pay?payment_id={payment_id}"
                f"&amount={amount}&currency={currency}&order_id={order_id}"
            )
        else:
            redirect_url = (
                f"payment://{provider}/pay?payment_id={payment_id}"
                f"&amount={amount}&currency={currency}"
            )

        event = PaymentInitiatedEvent(
            payment_id=payment_id,
            provider=provider,
            redirect_url=redirect_url,
            status="pending",
        )
        self._initiated_events.append(event)
        return event

    def get_emitted_payment_verified_events(self) -> list[PaymentVerifiedEvent]:
        return list(self._verified_events)

    def get_emitted_payment_initiated_events(self) -> list[PaymentInitiatedEvent]:
        return list(self._initiated_events)


def build_pakistan_payment_router() -> PakistanPaymentRouter:
    return PakistanPaymentRouter()
