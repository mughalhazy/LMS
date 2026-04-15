from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

from .entities import DeliveryAttempt, DeliveryStatus, EventMessage, Subscription
from .webhook_signing import WebhookSigner

Transport = Callable[[str, str, Dict[str, str], int], Tuple[int, str]]


class WebhookService:
    """In-memory reference implementation for webhook subscription and delivery rules."""

    RETRY_SCHEDULE_SECONDS = [30, 120, 600, 3600, 21600, 21600, 21600]
    SUBSCRIPTION_DELETE_RETRY_SECONDS = [300]
    MAX_ATTEMPTS = 8
    DELIVERY_TIMEOUT_SECONDS = 10

    def __init__(self, *, jitter_ratio: float = 0.1) -> None:
        self._subscriptions: Dict[str, Subscription] = {}
        self._pending: List[DeliveryAttempt] = []
        self._dead_letters: List[DeliveryAttempt] = []
        self._signer = WebhookSigner()
        self._endpoint_failures: Dict[str, int] = {}
        self._endpoint_breaker_until: Dict[str, datetime] = {}
        self._jitter_ratio = jitter_ratio

    @property
    def dead_letters(self) -> List[DeliveryAttempt]:
        return list(self._dead_letters)

    @property
    def pending(self) -> List[DeliveryAttempt]:
        return list(self._pending)

    def create_subscription(
        self,
        *,
        subscription_id: str,
        tenant_id: str,
        endpoint_url: str,
        secret: str,
        subscribed_events: List[str],
        now: Optional[datetime] = None,
    ) -> Subscription:
        self._validate_endpoint(endpoint_url)
        timestamp = now or datetime.utcnow()
        subscription = Subscription(
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            endpoint_url=endpoint_url,
            secret=secret,
            subscribed_events=list(subscribed_events),
            created_at=timestamp,
        )
        self._subscriptions[subscription_id] = subscription
        self._enqueue_system_event(
            subscription=subscription,
            event_type="subscription.created",
            payload={
                "subscription_id": subscription.subscription_id,
                "tenant_id": tenant_id,
                "endpoint_url": endpoint_url,
                "subscribed_events": subscribed_events,
                "status": "active",
                "created_at": timestamp.isoformat() + "Z",
            },
            now=timestamp,
        )
        return subscription

    def update_subscription(
        self,
        *,
        subscription_id: str,
        endpoint_url: Optional[str] = None,
        subscribed_events: Optional[List[str]] = None,
        now: Optional[datetime] = None,
    ) -> Subscription:
        subscription = self._subscriptions[subscription_id]
        if endpoint_url:
            self._validate_endpoint(endpoint_url)
            subscription.endpoint_url = endpoint_url
        if subscribed_events is not None:
            subscription.subscribed_events = list(subscribed_events)

        timestamp = now or datetime.utcnow()
        subscription.updated_at = timestamp

        self._enqueue_system_event(
            subscription=subscription,
            event_type="subscription.updated",
            payload={
                "subscription_id": subscription.subscription_id,
                "tenant_id": subscription.tenant_id,
                "endpoint_url": subscription.endpoint_url,
                "subscribed_events": subscription.subscribed_events,
                "status": subscription.status,
                "updated_at": timestamp.isoformat() + "Z",
            },
            now=timestamp,
        )
        return subscription

    def delete_subscription(self, *, subscription_id: str, now: Optional[datetime] = None) -> Subscription:
        subscription = self._subscriptions[subscription_id]
        timestamp = now or datetime.utcnow()
        self._enqueue_system_event(
            subscription=subscription,
            event_type="subscription.deleted",
            payload={
                "subscription_id": subscription.subscription_id,
                "tenant_id": subscription.tenant_id,
                "status": "deleted",
                "deleted_at": timestamp.isoformat() + "Z",
            },
            now=timestamp,
            delete_event=True,
        )
        subscription.status = "deleted"
        subscription.deleted_at = timestamp
        return subscription

    def publish_event(
        self,
        *,
        event_id: str,
        event_type: str,
        tenant_id: str,
        data: Dict[str, object],
        timestamp: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> List[DeliveryAttempt]:
        timestamp = now or datetime.utcnow()
        event = EventMessage(
            event_id=event_id,
            event_type=event_type,
            tenant_id=tenant_id,
            timestamp=timestamp or timestamp,
            data=data,
        )
        deliveries: List[DeliveryAttempt] = []
        for subscription in self._subscriptions.values():
            if subscription.tenant_id != tenant_id or subscription.status != "active":
                continue
            if event_type not in subscription.subscribed_events:
                continue
            deliveries.append(self._build_delivery(subscription=subscription, event=event, now=timestamp))

        self._pending.extend(deliveries)
        return deliveries

    def process_due_deliveries(self, *, transport: Transport, now: Optional[datetime] = None) -> None:
        timestamp = now or datetime.utcnow()
        for delivery in list(self._pending):
            if delivery.status not in {DeliveryStatus.PENDING, DeliveryStatus.FAILED}:
                continue
            if delivery.next_attempt_at > timestamp:
                continue

            subscription = self._subscriptions[delivery.subscription_id]
            if subscription.status != "active" and delivery.event_type != "subscription.deleted":
                delivery.status = DeliveryStatus.SKIPPED
                self._pending.remove(delivery)
                continue

            if self._breaker_open(delivery.endpoint_url, timestamp) and delivery.event_type == "assessment.graded":
                delivery.trace.append("circuit_breaker_open")
                delivery.next_attempt_at = timestamp + timedelta(seconds=60)
                continue

            self._attempt_delivery(delivery=delivery, subscription=subscription, transport=transport, now=timestamp)

            if delivery.status in {DeliveryStatus.DELIVERED, DeliveryStatus.DEAD_LETTERED, DeliveryStatus.SKIPPED}:
                self._pending.remove(delivery)

    def _attempt_delivery(
        self,
        *,
        delivery: DeliveryAttempt,
        subscription: Subscription,
        transport: Transport,
        now: datetime,
    ) -> None:
        headers = self._signer.build_headers(
            secret=subscription.secret,
            payload=delivery.payload,
            timestamp=str(int(now.timestamp())),
            delivery_id=delivery.delivery_id,
        )
        delivery.attempt_count += 1
        delivery.last_attempt_at = now
        status_code, response_text = transport(
            delivery.endpoint_url,
            delivery.payload,
            headers,
            self.DELIVERY_TIMEOUT_SECONDS,
        )

        delivery.last_status_code = status_code
        if 200 <= status_code < 300:
            delivery.status = DeliveryStatus.DELIVERED
            self._endpoint_failures[delivery.endpoint_url] = 0
            delivery.trace.append(f"attempt_{delivery.attempt_count}:success")
            return

        delivery.status = DeliveryStatus.FAILED
        delivery.last_error = response_text or f"HTTP {status_code}"
        delivery.trace.append(f"attempt_{delivery.attempt_count}:failed:{status_code}")

        if 500 <= status_code < 600:
            current = self._endpoint_failures.get(delivery.endpoint_url, 0) + 1
            self._endpoint_failures[delivery.endpoint_url] = current
            if delivery.event_type == "assessment.graded" and current >= 3:
                self._endpoint_breaker_until[delivery.endpoint_url] = now + timedelta(minutes=5)

        if delivery.attempt_count >= self.MAX_ATTEMPTS or (
            delivery.event_type == "subscription.deleted" and delivery.attempt_count >= 2
        ):
            delivery.status = DeliveryStatus.DEAD_LETTERED
            subscription.degraded = True
            self._dead_letters.append(delivery)
            return

        delay = self._compute_delay(delivery.event_type, delivery.attempt_count)
        delivery.next_attempt_at = now + timedelta(seconds=delay)

    def _compute_delay(self, event_type: str, attempt_count: int) -> int:
        if event_type == "subscription.deleted":
            return self.SUBSCRIPTION_DELETE_RETRY_SECONDS[0]

        base = self.RETRY_SCHEDULE_SECONDS[min(attempt_count - 1, len(self.RETRY_SCHEDULE_SECONDS) - 1)]
        jitter = int(base * self._jitter_ratio)
        if jitter <= 0:
            return base
        return base + random.randint(-jitter, jitter)

    def _build_delivery(self, *, subscription: Subscription, event: EventMessage, now: datetime) -> DeliveryAttempt:
        payload = json.dumps(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat() + "Z",
                "tenant_id": event.tenant_id,
                "data": event.data,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return DeliveryAttempt(
            delivery_id=f"dlv_{uuid.uuid4().hex}",
            subscription_id=subscription.subscription_id,
            event_id=event.event_id,
            event_type=event.event_type,
            endpoint_url=subscription.endpoint_url,
            payload=payload,
            next_attempt_at=now,
        )

    def _enqueue_system_event(
        self,
        *,
        subscription: Subscription,
        event_type: str,
        payload: Dict[str, object],
        now: datetime,
        delete_event: bool = False,
    ) -> None:
        event = EventMessage(
            event_id=f"evt_{uuid.uuid4().hex[:10]}",
            event_type=event_type,
            tenant_id=subscription.tenant_id,
            timestamp=now,
            data=payload,
        )
        delivery = self._build_delivery(subscription=subscription, event=event, now=now)
        if delete_event:
            delivery.trace.append("best_effort_notification")
        self._pending.append(delivery)

    @staticmethod
    def _validate_endpoint(endpoint_url: str) -> None:
        if not endpoint_url.startswith("https://"):
            raise ValueError("Webhook endpoint must enforce TLS (https://)")

    def verify_incoming_webhook(
        self,
        *,
        secret: str,
        payload: str,
        headers: Dict[str, str],
        now: Optional[datetime] = None,
    ) -> bool:
        return self._signer.verify_request(
            secret=secret,
            payload=payload,
            headers=headers,
            now=now or datetime.utcnow(),
        )

    def export_state(self) -> Dict[str, object]:
        return {
            "subscriptions": {key: asdict(value) for key, value in self._subscriptions.items()},
            "pending": [asdict(item) for item in self._pending],
            "dead_letters": [asdict(item) for item in self._dead_letters],
        }

    def _breaker_open(self, endpoint_url: str, now: datetime) -> bool:
        breaker_until = self._endpoint_breaker_until.get(endpoint_url)
        return bool(breaker_until and now < breaker_until)
