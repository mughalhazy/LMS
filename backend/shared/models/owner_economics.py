from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class OwnerEarningsEntry:
    """B15-008: canonical shared model for owner/participant economics."""
    entry_id: str
    participant_id: str
    tenant_id: str
    event_type: str
    source_event_id: str
    period: str  # YYYY-MM
    gross_amount: float
    platform_commission: float
    net_amount: float
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OwnerLedger:
    participant_id: str
    tenant_id: str
    period: str
    currency: str
    total_gross: float = 0.0
    total_commission: float = 0.0
    total_net: float = 0.0
    entry_count: int = 0


@dataclass
class PayoutRecord:
    payout_id: str
    participant_id: str
    tenant_id: str
    period: str
    currency: str
    gross_earnings: float
    platform_commission: float
    processing_fee: float
    tax_withholding: float
    net_payout: float
    deduction_breakdown: Dict[str, float] = field(default_factory=dict)
    status: str = "pending"
    schedule_type: str = "monthly"  # weekly | monthly | on_demand (from config-service)
    created_at: datetime = field(default_factory=datetime.utcnow)
