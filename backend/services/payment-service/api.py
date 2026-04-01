from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from integrations.payments import PaymentOrchestrationService, build_pakistan_payment_router


class PaymentCallbackRequest(BaseModel):
    payment_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    provider: str | None = None
    user_id: str | None = None
    order_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentCallbackResponse(BaseModel):
    transaction_id: str
    status: str
    user_id: str
    order_id: str | None
    verified: bool


app = FastAPI(title="payment-service", version="1.0.0")
orchestrator = PaymentOrchestrationService(router=build_pakistan_payment_router())


@app.post("/payments/callback/{provider}", response_model=PaymentCallbackResponse)
async def payment_callback(provider: str, payload: PaymentCallbackRequest) -> PaymentCallbackResponse:
    transaction_id = payload.payment_id
    callback_payload = payload.model_dump()
    callback_payload["provider"] = provider
    updated = await orchestrator.handle_provider_callback(provider=provider, payload=callback_payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="payment_not_found")

    emitted = orchestrator.get_emitted_payment_verified_events()
    event = next((evt for evt in reversed(emitted) if evt.transaction_id == transaction_id), None)
    if event is None:
        raise HTTPException(status_code=500, detail="payment_verified_event_not_emitted")

    return PaymentCallbackResponse(
        transaction_id=event.transaction_id,
        status=event.status,
        user_id=event.user_id,
        order_id=event.order_id,
        verified=updated.verified,
    )
