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
        if event in {SubscriptionEvent.ACTIVATION, SubscriptionEvent.RENEWAL} and subscription.segment_context.get("package_id"):
            if int(subscription.segment_context.get("seat_limit", 0)) < subscription.active_enrollments:
                raise SubscriptionLifecycleError("academy enrollments exceed seat_limit")
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
                timestamp=at,
            )
        )
        return subscription

    def activate(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.ACTIVATION, at=at)

    def renew(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.RENEWAL, at=at)

    def expire(self, subscription: Subscription, *, at: datetime | None = None) -> Subscription:
        return self.transition(subscription, SubscriptionEvent.EXPIRATION, at=at)

    def reserve_segment_enrollment(self, subscription: Subscription) -> Subscription:
        if not subscription.segment_context.get("package_id"):
            raise SubscriptionLifecycleError("package_id is required for enrollment")
        if not bool(subscription.segment_context.get("cohort_delivery_enabled", False)):
            raise SubscriptionLifecycleError("cohort-based delivery is disabled for this subscription")
        if subscription.state != SubscriptionState.ACTIVE:
            raise SubscriptionLifecycleError("subscription must be active for academy enrollment")
        if subscription.active_enrollments >= int(subscription.segment_context.get("seat_limit", 0)):
            raise SubscriptionLifecycleError("seat limit reached")
        subscription.active_enrollments += 1
        return subscription

    def release_segment_enrollment(self, subscription: Subscription) -> Subscription:
        if subscription.active_enrollments > 0:
            subscription.active_enrollments -= 1
        return subscription
