from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CostRecord:
    record_id: str
    tenant_id: str
    capability_key: str
    cost_type: str          # compute | ai_calls | storage | analytics
    amount: float
    currency: str
    period: str             # YYYY-MM
    metric_key: Optional[str] = None
    quantity: Optional[float] = None


@dataclass
class ProfitabilityView:
    tenant_id: str
    period: str
    currency: str
    revenue: float
    cost: float
    margin: float
    margin_pct: float
    suggested_action: Optional[str] = None


@dataclass
class EconomicInsight:
    insight_type: str       # revenue_down | high_cost_low_uptake | low_margin | payout_overdue
    tenant_id: str
    period: str
    metric_value: float
    threshold: float
    suggested_action: str   # BC-ECON-01: every insight must carry a suggested action
    severity: str = "medium"
    context: Dict[str, Any] = field(default_factory=dict)
