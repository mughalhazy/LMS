from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SubscriptionState(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionEvent(str, Enum):
    ACTIVATION = "activation"
    RENEWAL = "renewal"
    EXPIRATION = "expiration"
    CANCELLATION = "cancellation"


@dataclass
class LifecycleRecord:
    event: SubscriptionEvent
    from_state: SubscriptionState
    to_state: SubscriptionState
    timestamp: datetime


@dataclass
class Subscription:
    subscription_id: str
    tenant_id: str
    plan_id: str
    academy_package_id: str | None = None
    academy_cohort_delivery_enabled: bool = False
    academy_seat_limit: int = 0
    academy_active_enrollments: int = 0
    state: SubscriptionState = SubscriptionState.TRIAL
    trial_ends_at: datetime | None = None
    current_period_ends_at: datetime | None = None
    activated_at: datetime | None = None
    expired_at: datetime | None = None
    cancelled_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lifecycle: list[LifecycleRecord] = field(default_factory=list)
