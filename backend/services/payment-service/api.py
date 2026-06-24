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


class PaymentInitiateRequest(BaseModel):
    order_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    payment_method: str = Field(min_length=1, description="jazzcash | easypaisa | mobile_money")
    tenant_id: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentInitiateResponse(BaseModel):
    payment_id: str
    provider: str
    redirect_url: str
    status: str
    order_id: str
    user_id: str


app = FastAPI(title="payment-service", version="1.0.0")

# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers  # noqa: E402
_register_consumers()

orchestrator = PaymentOrchestrationService(router=build_pakistan_payment_router())


@app.post("/api/v1/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(payload: PaymentInitiateRequest) -> PaymentInitiateResponse:
    provider = orchestrator._router.resolve_provider(payload.payment_method)
    event = await orchestrator.initiate_payment(
        provider=provider,
        order_id=payload.order_id,
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        payment_method=payload.payment_method,
        tenant_id=payload.tenant_id,
        metadata=payload.metadata,
    )
    return PaymentInitiateResponse(
        payment_id=event.payment_id,
        provider=event.provider,
        redirect_url=event.redirect_url,
        status=event.status,
        order_id=payload.order_id,
        user_id=payload.user_id,
    )


@app.post("/api/v1/payments/callback/{provider}", response_model=PaymentCallbackResponse)
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
