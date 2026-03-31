from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RevenueRecord:
    tenant_id: str
    plan_id: str
    amount: float
    billed_at: datetime
    currency: str = "USD"
    source_event_id: str | None = None
