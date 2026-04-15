from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class OwnerEconomicsSnapshot:
    tenant_id: str
    reporting_period: str
    revenue_per_student: Decimal
    total_cash_in: Decimal
    outstanding_dues: Decimal
    gross_revenue: Decimal
    estimated_costs: Decimal
    estimated_profit: Decimal
    profitability_by_batch: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    profitability_by_branch: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    # CGAP-043: BC-ECON-01 — every economic snapshot carries an embedded suggested action.
    suggested_action: str = ""
