from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class TeacherEarningsEntry:
    """B15-008: canonical shared model for teacher/tutor economics.
    Distinct from owner economics — driven by session delivery and tutor rating events."""
    entry_id: str
    tutor_id: str
    tenant_id: str
    event_type: str          # session_delivered | rating_bonus | milestone_bonus
    source_event_id: str
    session_id: Optional[str]
    period: str              # YYYY-MM
    base_amount: float       # per-session fee from config
    rating_multiplier: float = 1.0   # rating-driven bonus multiplier
    gross_amount: float = 0.0
    platform_fee: float = 0.0
    net_amount: float = 0.0
    currency: str = "USD"
    rating_score: Optional[float] = None  # tutor rating at time of event
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TeacherLedger:
    tutor_id: str
    tenant_id: str
    period: str
    currency: str
    total_sessions: int = 0
    total_gross: float = 0.0
    total_platform_fee: float = 0.0
    total_net: float = 0.0
    average_rating: float = 0.0
