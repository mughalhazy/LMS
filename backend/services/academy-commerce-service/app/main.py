"""Academy Commerce Service — B15-010."""
from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from .service import (
    EnrollmentBasedPricingContextAdapter,
    EnrollmentOfferComposer,
    PromotionScenarioRegistry,
    StudentPaymentOrchestrationExtension,
)

app = FastAPI(title="Academy Commerce Service", version="1.0.0")

_promo_registry = PromotionScenarioRegistry()
_pricing_adapter = EnrollmentBasedPricingContextAdapter()
_offer_composer = EnrollmentOfferComposer(_pricing_adapter, _promo_registry)
_payment_orch = StudentPaymentOrchestrationExtension(_offer_composer)


@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


class OfferRequest(BaseModel):
    tenant_id: str
    user_id: str
    course_id: str
    country_code: str = "DEFAULT"
    base_price: float
    promotion_id: Optional[str] = None
    request_installments: bool = False
    installment_count: int = 2


class PromoRequest(BaseModel):
    name: str
    type: str = "early_bird"
    discount_pct: float
    max_redemptions: Optional[int] = None
    valid_from: str = ""
    valid_until: str = ""


class PaymentRefRequest(BaseModel):
    offer_id: str
    payment_method: str = "bank_transfer"
    transaction_ref: str = ""
    amount_submitted: float = 0.0


class VerifyRequest(BaseModel):
    verified: bool
    verifier_id: str


@app.post("/api/v1/academy-commerce/offers")
def compose_offer(request: OfferRequest):
    return _offer_composer.compose(request.model_dump())


@app.get("/api/v1/academy-commerce/offers/{offer_id}")
def get_offer(offer_id: str):
    offer = _offer_composer.get(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="offer_not_found")
    return offer


@app.post("/api/v1/academy-commerce/promotions/{scenario_id}")
def register_promotion(scenario_id: str, request: PromoRequest):
    return _promo_registry.register(scenario_id, request.model_dump())


@app.get("/api/v1/academy-commerce/promotions")
def list_promotions():
    return {"promotions": _promo_registry.list_active()}


@app.post("/api/v1/academy-commerce/payment-references")
def submit_payment_reference(request: PaymentRefRequest):
    status, body = _payment_orch.submit_payment_reference(request.model_dump())
    if status != 201:
        raise HTTPException(status_code=status, detail=body)
    return body


@app.post("/api/v1/academy-commerce/payment-references/{reference_id}/verify")
def verify_payment(reference_id: str, request: VerifyRequest):
    status, body = _payment_orch.verify_and_activate(
        reference_id, request.verified, request.verifier_id)
    if status != 200:
        raise HTTPException(status_code=status, detail=body)
    return body


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "academy-commerce-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "academy-commerce-service", "service_up": 1}
