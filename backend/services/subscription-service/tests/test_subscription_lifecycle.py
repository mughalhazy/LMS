from datetime import datetime, timezone

import pytest

from app.errors import SubscriptionLifecycleError
from app.models import Subscription, SubscriptionState
from app.service import SubscriptionLifecycleService


def _subscription(state: SubscriptionState = SubscriptionState.TRIAL) -> Subscription:
    return Subscription(subscription_id="sub_1", tenant_id="tenant_1", plan_id="pro", state=state)


def test_activation_renewal_and_expiration_flow_is_valid() -> None:
    service = SubscriptionLifecycleService()
    activation_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    renewal_time = datetime(2026, 2, 1, tzinfo=timezone.utc)
    expiration_time = datetime(2026, 3, 1, tzinfo=timezone.utc)

    subscription = _subscription(SubscriptionState.TRIAL)

    service.activate(subscription, at=activation_time)
    assert subscription.state == SubscriptionState.ACTIVE
    assert subscription.activated_at == activation_time

    service.renew(subscription, at=renewal_time)
    assert subscription.state == SubscriptionState.ACTIVE
    assert subscription.expired_at is None

    service.expire(subscription, at=expiration_time)
    assert subscription.state == SubscriptionState.EXPIRED
    assert subscription.expired_at == expiration_time
    assert [item.event.value for item in subscription.lifecycle] == ["activation", "renewal", "expiration"]


def test_invalid_transition_is_blocked_for_consistent_state() -> None:
    service = SubscriptionLifecycleService()
    subscription = _subscription(SubscriptionState.CANCELLED)

    with pytest.raises(SubscriptionLifecycleError):
        service.renew(subscription)

    assert subscription.state == SubscriptionState.CANCELLED
    assert subscription.lifecycle == []
