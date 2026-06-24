from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EarningsEntry:
    entry_id: str
    participant_id: str
    tenant_id: str
    event_type: str  # enrollment_revenue_share | session_fee | content_royalty | referral_credit
    source_event_id: str  # deduplication key
    period: str  # YYYY-MM
    gross_amount: float
    platform_commission: float
    net_amount: float
    currency: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ParticipantLedger:
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
    status: str = "calculated"  # calculated | approved | paid
    deduction_breakdown: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
