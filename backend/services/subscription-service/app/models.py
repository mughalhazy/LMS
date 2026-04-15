from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from backend.services.shared.models.product import Product


class SubscriptionState(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    # CGAP-080: billing lifecycle states — grace (payment overdue, capabilities preserved
    # with warning), suspended (non-essential capabilities blocked), plus existing terminal states.
    GRACE = "grace"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionEvent(str, Enum):
    ACTIVATION = "activation"
    RENEWAL = "renewal"
    EXPIRATION = "expiration"
    CANCELLATION = "cancellation"
    # CGAP-080: grace entry (payment overdue) and suspension (grace period elapsed unpaid).
    GRACE_ENTRY = "grace_entry"
    SUSPENSION = "suspension"


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
    segment_context: dict[str, str | int | bool] = field(default_factory=dict)
    active_enrollments: int = 0
    state: SubscriptionState = SubscriptionState.TRIAL
    trial_ends_at: datetime | None = None
    current_period_ends_at: datetime | None = None
    activated_at: datetime | None = None
    expired_at: datetime | None = None
    cancelled_at: datetime | None = None
    # CGAP-080: grace + suspension lifecycle timestamps.
    grace_entered_at: datetime | None = None
    suspended_at: datetime | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lifecycle: list[LifecycleRecord] = field(default_factory=list)


@dataclass(frozen=True)
class ProductCatalogEntry:
    product: Product
    course_ids: list[str]
