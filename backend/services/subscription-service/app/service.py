from __future__ import annotations

from datetime import datetime, timezone

from .errors import SubscriptionLifecycleError
from .models import LifecycleRecord, Subscription, SubscriptionEvent, SubscriptionState


EVENT_TRANSITIONS: dict[SubscriptionEvent, tuple[set[SubscriptionState], SubscriptionState]] = {
    SubscriptionEvent.ACTIVATION: ({SubscriptionState.TRIAL, SubscriptionState.EXPIRED}, SubscriptionState.ACTIVE),
    SubscriptionEvent.RENEWAL: ({SubscriptionState.ACTIVE, SubscriptionState.EXPIRED}, SubscriptionState.ACTIVE),
    SubscriptionEvent.EXPIRATION: ({SubscriptionState.TRIAL, SubscriptionState.ACTIVE}, SubscriptionState.EXPIRED),
    SubscriptionEvent.CANCELLATION: (
        {SubscriptionState.TRIAL, SubscriptionState.ACTIVE, SubscriptionState.EXPIRED},
        SubscriptionState.CANCELLED,
    ),
}


class SubscriptionLifecycleService:
    """Single-point state machine for subscription lifecycle transitions."""

    def transition(self, subscription: Subscription, event: SubscriptionEvent, *, at: datetime | None = None) -> Subscription:
        at = at or datetime.now(timezone.utc)
        allowed_states, next_state = EVENT_TRANSITIONS[event]
        if subscription.state not in allowed_states:
            raise SubscriptionLifecycleError(
                f"invalid transition: event={event.value} from_state={subscription.state.value}"
            )

        previous_state = subscription.state
        subscription.state = next_state
        subscription.updated_at = at

        if event == SubscriptionEvent.ACTIVATION:
            subscription.activated_at = subscription.activated_at or at
            subscription.expired_at = None
        elif event == SubscriptionEvent.RENEWAL:
            subscription.expired_at = None
        elif event == SubscriptionEvent.EXPIRATION:
            subscription.expired_at = at
        elif event == SubscriptionEvent.CANCELLATION:
            subscription.cancelled_at = at

        subscription.lifecycle.append(
            LifecycleRecord(
                event=event,
                from_state=previous_state,
                to_state=next_state,
                occurred_at=at,
            )
        )
        return subscription

    def activate(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.ACTIVATION, at=at)

    def renew(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.RENEWAL, at=at)

    def expire(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.EXPIRATION, at=at)
