"""Academy Commerce Extensions — implements academy-commerce-extensions.md.
B15-010: EnrollmentOfferComposer, StudentPaymentOrchestrationExtension,
EnrollmentBasedPricingContextAdapter, PromotionScenarioRegistry."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class PromotionScenarioRegistry:
    """Registry of academy-specific promotion scenarios (early-bird, group, scholarship)."""

    def __init__(self) -> None:
        self._scenarios: Dict[str, Dict[str, Any]] = {}

    def register(self, scenario_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        scenario = {
            "scenario_id": scenario_id,
            "name": body.get("name", ""),
            "type": body.get("type", "early_bird"),  # early_bird | group | scholarship | referral
            "discount_pct": float(body.get("discount_pct", 0.0)),
            "max_redemptions": body.get("max_redemptions"),
            "valid_from": body.get("valid_from", ""),
            "valid_until": body.get("valid_until", ""),
            "active": True,
            "redemption_count": 0,
        }
        self._scenarios[scenario_id] = scenario
        return scenario

    def get(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        return self._scenarios.get(scenario_id)

    def list_active(self) -> List[Dict[str, Any]]:
        return [s for s in self._scenarios.values() if s.get("active")]

    def apply(self, scenario_id: str, base_price: float) -> Tuple[float, Dict[str, Any]]:
        scenario = self._scenarios.get(scenario_id)
        if not scenario or not scenario["active"]:
            return base_price, {"applied": False, "reason": "scenario_not_found_or_inactive"}
        if scenario.get("max_redemptions") and scenario["redemption_count"] >= scenario["max_redemptions"]:
            return base_price, {"applied": False, "reason": "max_redemptions_reached"}
        discount = base_price * (scenario["discount_pct"] / 100)
        scenario["redemption_count"] += 1
        final = round(base_price - discount, 2)
        return final, {"applied": True, "scenario_id": scenario_id,
                       "discount_pct": scenario["discount_pct"],
                       "discount_amount": round(discount, 2), "final_price": final}


class EnrollmentBasedPricingContextAdapter:
    """B15-010: resolve regional policy pack + pricing context for enrollment."""

    REGIONAL_POLICIES = {
        "PK": {"currency": "PKR", "tax_pct": 0.0, "installments_allowed": True, "max_installments": 3},
        "US": {"currency": "USD", "tax_pct": 8.5, "installments_allowed": False, "max_installments": 1},
        "GB": {"currency": "GBP", "tax_pct": 20.0, "installments_allowed": True, "max_installments": 2},
        "DEFAULT": {"currency": "USD", "tax_pct": 0.0, "installments_allowed": False, "max_installments": 1},
    }

    def resolve_context(self, tenant_id: str, user_id: str,
                        country_code: str, course_id: str) -> Dict[str, Any]:
        policy = self.REGIONAL_POLICIES.get(country_code, self.REGIONAL_POLICIES["DEFAULT"])
        return {
            "tenant_id": tenant_id, "user_id": user_id,
            "course_id": course_id, "country_code": country_code,
            "pricing_policy": policy,
            "context_id": f"ctx-{secrets.token_urlsafe(6)}",
        }


class EnrollmentOfferComposer:
    """B15-010: compose enrollment offer — pricing context + promotions + installment plan."""

    def __init__(self, pricing_adapter: EnrollmentBasedPricingContextAdapter,
                 promo_registry: PromotionScenarioRegistry) -> None:
        self._pricing = pricing_adapter
        self._promos = promo_registry
        self._offers: Dict[str, Dict[str, Any]] = {}

    def compose(self, body: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = body.get("tenant_id", "")
        user_id = body.get("user_id", "")
        course_id = body.get("course_id", "")
        country_code = body.get("country_code", "DEFAULT")
        base_price = float(body.get("base_price", 0.0))
        promo_id = body.get("promotion_id")

        context = self._pricing.resolve_context(tenant_id, user_id, country_code, course_id)
        policy = context["pricing_policy"]

        final_price = base_price
        promo_detail = {"applied": False}
        if promo_id:
            final_price, promo_detail = self._promos.apply(promo_id, base_price)

        tax = round(final_price * policy["tax_pct"] / 100, 2)
        total = round(final_price + tax, 2)

        installments = []
        if policy["installments_allowed"] and body.get("request_installments"):
            n = min(int(body.get("installment_count", 2)), policy["max_installments"])
            installment_amt = round(total / n, 2)
            installments = [{"installment": i + 1, "amount": installment_amt,
                              "currency": policy["currency"]} for i in range(n)]

        offer_id = f"offer-{secrets.token_urlsafe(8)}"
        offer = {
            "offer_id": offer_id, "tenant_id": tenant_id, "user_id": user_id,
            "course_id": course_id, "country_code": country_code,
            "base_price": base_price, "final_price": final_price,
            "tax": tax, "total": total, "currency": policy["currency"],
            "promotion": promo_detail,
            "installments": installments,
            "pricing_context_id": context["context_id"],
            "composed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._offers[offer_id] = offer
        return offer

    def get(self, offer_id: str) -> Optional[Dict[str, Any]]:
        return self._offers.get(offer_id)


class StudentPaymentOrchestrationExtension:
    """B15-010: orchestrate student payment reference submission → enrollment activation."""

    def __init__(self, offer_composer: EnrollmentOfferComposer) -> None:
        self._composer = offer_composer
        self._references: Dict[str, Dict[str, Any]] = {}

    def submit_payment_reference(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        offer_id = body.get("offer_id", "")
        offer = self._composer.get(offer_id)
        if not offer:
            return 404, {"error": "offer_not_found", "offer_id": offer_id}

        ref_id = f"payref-{secrets.token_urlsafe(8)}"
        reference = {
            "reference_id": ref_id,
            "offer_id": offer_id,
            "tenant_id": offer["tenant_id"],
            "user_id": offer["user_id"],
            "course_id": offer["course_id"],
            "payment_method": body.get("payment_method", "bank_transfer"),
            "transaction_ref": body.get("transaction_ref", ""),
            "amount_submitted": float(body.get("amount_submitted", 0.0)),
            "currency": offer["currency"],
            "status": "pending_verification",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self._references[ref_id] = reference

        # Emit event for enrollment service to pick up
        try:
            from backend.services.shared.events.bus import get_default_bus
            from backend.services.shared.events.envelope import build_event
            bus = get_default_bus()
            bus.publish(build_event(
                event_type="academy.payment.reference.submitted",
                tenant_id=offer["tenant_id"],
                payload=reference,
            ))
        except Exception:
            pass

        return 201, reference

    def verify_and_activate(self, reference_id: str, verified: bool,
                             verifier_id: str) -> Tuple[int, Dict[str, Any]]:
        ref = self._references.get(reference_id)
        if not ref:
            return 404, {"error": "reference_not_found"}
        ref["status"] = "verified" if verified else "rejected"
        ref["verified_by"] = verifier_id
        ref["verified_at"] = datetime.now(timezone.utc).isoformat()

        if verified:
            try:
                from backend.services.shared.events.bus import get_default_bus
                from backend.services.shared.events.envelope import build_event
                bus = get_default_bus()
                bus.publish(build_event(
                    event_type="academy.offer.composed",
                    tenant_id=ref["tenant_id"],
                    payload={**ref, "action": "enrollment_activate"},
                ))
            except Exception:
                pass

        return 200, ref
