from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    SKIPPED = "skipped"


@dataclass
class Subscription:
    subscription_id: str
    tenant_id: str
    endpoint_url: str
    secret: str
    subscribed_events: List[str]
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    degraded: bool = False


@dataclass
class EventMessage:
    event_id: str
    event_type: str
    tenant_id: str
    occurred_at: datetime
    data: Dict[str, object]


@dataclass
class DeliveryAttempt:
    delivery_id: str
    subscription_id: str
    event_id: str
    event_type: str
    endpoint_url: str
    payload: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt_count: int = 0
    next_attempt_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_error: Optional[str] = None
    last_status_code: Optional[int] = None
    last_attempt_at: Optional[datetime] = None
    trace: List[str] = field(default_factory=list)
