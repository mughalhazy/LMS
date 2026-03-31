from __future__ import annotations

import json
import os
from decimal import Decimal, InvalidOperation

from backend.services.shared.models.plan import BillingCycle, Plan

_PRICING_ENV = "SUBSCRIPTION_PRICING_PLANS_JSON"


def _parse_plan(plan_type: str, payload: object) -> Plan | None:
    if not isinstance(plan_type, str) or not isinstance(payload, dict):
        return None

    price_raw = payload.get("price")
    billing_cycle_raw = payload.get("billing_cycle")
    included_features_raw = payload.get("included_features")

    if not isinstance(included_features_raw, list):
        return None

    try:
        price = Decimal(str(price_raw))
    except (InvalidOperation, TypeError, ValueError):
        return None

    if price < 0:
        return None

    try:
        billing_cycle = BillingCycle(str(billing_cycle_raw).strip().lower())
    except ValueError:
        return None

    included_features = tuple(
        feature.strip()
        for feature in included_features_raw
        if isinstance(feature, str) and feature.strip()
    )

    return Plan(
        plan_type=plan_type,
        price=price,
        billing_cycle=billing_cycle,
        included_features=included_features,
    ).normalized()


def list_plans() -> dict[str, Plan]:
    raw_payload = os.getenv(_PRICING_ENV, "")
    if not raw_payload.strip():
        return {}

    try:
        parsed_payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed_payload, dict):
        return {}

    resolved: dict[str, Plan] = {}
    for plan_type, plan_payload in parsed_payload.items():
        plan = _parse_plan(plan_type, plan_payload)
        if plan is not None:
            resolved[plan.plan_type] = plan
    return resolved


def resolve_plan(plan_type: str) -> Plan | None:
    normalized = plan_type.strip().lower()
    if not normalized:
        return None
    return list_plans().get(normalized)
