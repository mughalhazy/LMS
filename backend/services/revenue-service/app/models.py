from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class RevenueFact:
    fact_id: str
    fact_type: str  # invoice_line_recognized | credit_applied | refund_recognized | deferred_revenue_change
    source_service: str
    source_event_id: str
    tenant_id: str
    capability_key: Optional[str]
    invoice_id: Optional[str]
    invoice_line_id: Optional[str]
    subscription_id: Optional[str]
    currency: str
    gross: float
    discount: float
    net: float
    recognition_start: datetime
    recognition_end: datetime
    recognized_at: datetime
    allocation_method: str  # direct_mapping | fixed_split | usage_weighted
    usage_metric_key: Optional[str] = None
    usage_quantity: Optional[float] = None
    ingested_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RevenueTenantDaily:
    tenant_id: str
    date: str  # YYYY-MM-DD
    currency: str
    recognized_revenue: float = 0.0
    refund_delta: float = 0.0
    credit_delta: float = 0.0


@dataclass
class RevenueCapabilityDaily:
    capability_key: str
    date: str
    currency: str
    recognized_revenue: float = 0.0
    refund_delta: float = 0.0
