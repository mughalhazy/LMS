from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class UsageEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    producer_service: str
    producer_version: str
    tenant_id: str
    actor_type: str
    actor_id: str
    domain_key: str
    capability_key: str
    metric_key: str
    quantity: float
    unit: str
    resource_id: Optional[str]
    session_id: Optional[str]
    region: Optional[str]
    idempotency_key: Optional[str]
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageAggregate:
    tenant_id: str
    capability_key: str
    domain_key: str
    metric_key: str
    unit: str
    window_start: str   # ISO date string
    window_end: str
    granularity: str    # hourly | daily | monthly
    total_quantity: float = 0.0
    event_count: int = 0
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
