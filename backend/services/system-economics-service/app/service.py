from __future__ import annotations

import secrets
from typing import Any, Dict, List, Tuple

from .models import CostRecord, EconomicInsight, ProfitabilityView

COST_TYPES = {"compute", "ai_calls", "storage", "analytics"}

# BC-ECON-01: every insight type must carry a suggested action template
INSIGHT_ACTIONS = {
    "revenue_down": "Review courses with declining enrollment → check enrollment dashboard",
    "high_cost_low_uptake": "Consider downgrading or removing capability → review capability usage",
    "low_margin": "Review pricing or costs for tenant → open tenant economics report",
    "payout_overdue": "Initiate payout for overdue instructors → open payout management",
}


class SystemEconomicsService:
    def __init__(self) -> None:
        self._costs: List[CostRecord] = []
        self._revenue_data: Dict[str, Dict[str, float]] = {}   # tenant_id:period → revenue

    def record_cost(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        cost_type = body.get("cost_type", "")
        if cost_type not in COST_TYPES:
            return 400, {"error": "invalid_cost_type", "valid": list(COST_TYPES)}
        record = CostRecord(
            record_id=f"cost-{secrets.token_urlsafe(8)}",
            tenant_id=body.get("tenant_id", ""),
            capability_key=body.get("capability_key", ""),
            cost_type=cost_type,
            amount=float(body.get("amount", 0)),
            currency=body.get("currency", "USD"),
            period=body.get("period", ""),
            metric_key=body.get("metric_key"),
            quantity=body.get("quantity"),
        )
        self._costs.append(record)
        return 201, {"record_id": record.record_id, "cost_type": cost_type,
                     "amount": record.amount, "period": record.period}

    def record_revenue(self, tenant_id: str, period: str, revenue: float) -> Tuple[int, Dict[str, Any]]:
        key = f"{tenant_id}:{period}"
        self._revenue_data[key] = {"revenue": revenue, "tenant_id": tenant_id, "period": period}
        return 200, {"tenant_id": tenant_id, "period": period, "revenue": revenue}

    def get_profitability(self, tenant_id: str, period: str) -> Tuple[int, Dict[str, Any]]:
        costs = [c for c in self._costs if c.tenant_id == tenant_id and c.period == period]
        total_cost = sum(c.amount for c in costs)
        revenue_data = self._revenue_data.get(f"{tenant_id}:{period}", {})
        revenue = revenue_data.get("revenue", 0.0)
        margin = revenue - total_cost
        margin_pct = round((margin / revenue * 100), 2) if revenue > 0 else 0.0

        # BC-ECON-01: include suggested action when margin is low
        suggested_action = None
        if margin_pct < 20:
            suggested_action = INSIGHT_ACTIONS["low_margin"]

        view = ProfitabilityView(
            tenant_id=tenant_id, period=period, currency="USD",
            revenue=round(revenue, 2), cost=round(total_cost, 2),
            margin=round(margin, 2), margin_pct=margin_pct,
            suggested_action=suggested_action,
        )
        return 200, {
            "tenant_id": view.tenant_id, "period": view.period,
            "revenue": view.revenue, "cost": view.cost, "margin": view.margin,
            "margin_pct": view.margin_pct, "suggested_action": view.suggested_action,
        }

    def get_insights(self, tenant_id: str, period: str) -> Tuple[int, Dict[str, Any]]:
        insights = []
        revenue_data = self._revenue_data.get(f"{tenant_id}:{period}", {})
        revenue = revenue_data.get("revenue", 0.0)

        # Check cost types for high-cost low-uptake
        costs_by_cap: Dict[str, float] = {}
        for c in self._costs:
            if c.tenant_id == tenant_id and c.period == period:
                costs_by_cap[c.capability_key] = costs_by_cap.get(c.capability_key, 0) + c.amount

        for cap_key, cost in costs_by_cap.items():
            if cost > 100 and revenue < cost * 2:
                insights.append(EconomicInsight(
                    insight_type="high_cost_low_uptake",
                    tenant_id=tenant_id, period=period,
                    metric_value=cost, threshold=revenue * 0.5,
                    suggested_action=INSIGHT_ACTIONS["high_cost_low_uptake"],
                    severity="high", context={"capability_key": cap_key},
                ))

        return 200, {
            "tenant_id": tenant_id, "period": period,
            "insights": [
                {"insight_type": i.insight_type, "metric_value": i.metric_value,
                 "suggested_action": i.suggested_action, "severity": i.severity,
                 "context": i.context}
                for i in insights
            ],
            "count": len(insights),
        }
