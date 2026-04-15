"""Webhook delivery service — subscription management, event fan-out, retry, and DLQ.

CGAP-027: replaces NotImplementedError stub. Wires the existing src.WebhookService into a
tenant-scoped facade per webhook_system_spec.md:
  - Subscription lifecycle: create/update/delete with HMAC-signed lifecycle events
  - Event fan-out: publish platform events to all active matching subscriptions
  - Delivery engine: exponential backoff retry (30s→2m→10m→1h→6h, max 8 attempts)
  - Dead-letter queue: events that exceed max retries with degraded endpoint marking
  - Circuit breaker: pause assessment.graded deliveries after repeated 5xx responses
  - Signature verification: HMAC-SHA256 via X-LMS-Signature/Timestamp/Delivery-Id headers
  - TLS enforcement: https:// required on all subscription endpoints

Spec refs: docs/integrations/webhook_system_spec.md
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from entities import DeliveryStatus, Subscription  # noqa: E402
from webhook_service import WebhookService  # noqa: E402

Transport = Callable[[str, str, dict[str, str], int], Tuple[int, str]]


class SubscriptionNotFoundError(Exception):
    """Raised when a subscription_id has no record for the given tenant."""


class WebhookManagementService:
    """Tenant-scoped facade over WebhookService per webhook_system_spec.md.

    Covers all spec delivery rules:
    - HMAC-SHA256 signed requests (X-LMS-Signature, X-LMS-Timestamp, X-LMS-Delivery-Id)
    - Exponential backoff retry: 30s / 2m / 10m / 1h / 6h (max 8 attempts) with jitter
    - Dead-letter queue with tenant-accessible delivery log
    - circuit breaker: pause assessment.graded deliveries after ≥3 consecutive 5xx responses
    - Subscription.deleted: best-effort delivery, one retry at 5 minutes
    - Endpoint health: degraded flag set when max retries exhausted for a subscription
    """

    def __init__(self, *, jitter_ratio: float = 0.1) -> None:
        # One WebhookService instance is shared (all tenant isolation is enforced here)
        self._svc = WebhookService(jitter_ratio=jitter_ratio)
        # Index for tenant-scoped lookup: tenant_id → {subscription_id}
        self._tenant_index: dict[str, set[str]] = {}
        # Delivery log: per tenant, list of delivery summary records
        self._delivery_log: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------ #
    # Subscription lifecycle                                               #
    # ------------------------------------------------------------------ #

    def create_subscription(
        self,
        *,
        tenant_id: str,
        endpoint_url: str,
        secret: str,
        subscribed_events: list[str],
        subscription_id: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Create a webhook subscription.

        webhook_system_spec: delivers subscription.created event immediately after
        creation. Enforces TLS (https://) on endpoint URL. Signs all deliveries with
        HMAC-SHA256 using the provided secret.
        """
        import uuid as _uuid
        sid = subscription_id or f"sub_{_uuid.uuid4().hex[:12]}"
        sub = self._svc.create_subscription(
            subscription_id=sid,
            tenant_id=tenant_id,
            endpoint_url=endpoint_url,
            secret=secret,
            subscribed_events=subscribed_events,
            now=now,
        )
        self._tenant_index.setdefault(tenant_id, set()).add(sid)
        return _sub_to_dict(sub)

    def update_subscription(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        endpoint_url: str | None = None,
        subscribed_events: list[str] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Update an existing subscription.

        webhook_system_spec: delivers subscription.updated event in-order per endpoint
        queue with same backoff policy and immutable payload across retry attempts.
        """
        self._assert_tenant_owns(tenant_id, subscription_id)
        sub = self._svc.update_subscription(
            subscription_id=subscription_id,
            endpoint_url=endpoint_url,
            subscribed_events=subscribed_events,
            now=now,
        )
        return _sub_to_dict(sub)

    def delete_subscription(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Delete a subscription.

        webhook_system_spec: best-effort subscription.deleted notification — delivered
        once, retried once at 5 minutes if first attempt fails. No business events
        delivered after deletion effective time.
        """
        self._assert_tenant_owns(tenant_id, subscription_id)
        sub = self._svc.delete_subscription(subscription_id=subscription_id, now=now)
        return _sub_to_dict(sub)

    def list_subscriptions(self, *, tenant_id: str, status: str | None = None) -> list[dict[str, Any]]:
        """List all subscriptions for a tenant, optionally filtered by status."""
        sids = self._tenant_index.get(tenant_id, set())
        subs = [
            _sub_to_dict(self._svc._subscriptions[sid])  # noqa: SLF001
            for sid in sids
            if sid in self._svc._subscriptions  # noqa: SLF001
        ]
        if status:
            subs = [s for s in subs if s["status"] == status]
        return subs

    def get_subscription(self, *, tenant_id: str, subscription_id: str) -> dict[str, Any]:
        """Get a single subscription by ID."""
        self._assert_tenant_owns(tenant_id, subscription_id)
        sub = self._svc._subscriptions.get(subscription_id)  # noqa: SLF001
        if not sub:
            raise SubscriptionNotFoundError(subscription_id)
        return _sub_to_dict(sub)

    # ------------------------------------------------------------------ #
    # Event publishing + delivery                                          #
    # ------------------------------------------------------------------ #

    def publish_event(
        self,
        *,
        tenant_id: str,
        event_type: str,
        data: dict[str, Any],
        event_id: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Publish a domain event — fan-out to all active matching subscriptions.

        webhook_system_spec: fan-out only to active subscriptions that include the
        event_type. Each delivery gets a unique X-LMS-Delivery-Id. Consumers must
        use event_id or X-LMS-Delivery-Id for idempotency (at-least-once delivery).
        """
        import uuid as _uuid
        eid = event_id or f"evt_{_uuid.uuid4().hex[:10]}"
        timestamp = now or datetime.utcnow()
        deliveries = self._svc.publish_event(
            event_id=eid,
            event_type=event_type,
            tenant_id=tenant_id,
            data=data,
            now=timestamp,
        )
        return {
            "event_id": eid,
            "event_type": event_type,
            "tenant_id": tenant_id,
            "deliveries_queued": len(deliveries),
            "delivery_ids": [d.delivery_id for d in deliveries],
            "published_at": timestamp.isoformat(),
        }

    def process_due_deliveries(
        self,
        *,
        transport: Transport,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Run the delivery engine — attempt all due deliveries.

        Callers supply a transport callable (url, payload, headers, timeout) → (status_code, body).
        This matches the spec's hook injection pattern for testable delivery without HTTP coupling.
        """
        before_pending = len(self._svc.pending)
        self._svc.process_due_deliveries(transport=transport, now=now)
        after_pending = len(self._svc.pending)
        return {
            "processed": before_pending - after_pending,
            "still_pending": after_pending,
            "dead_letters_total": len(self._svc.dead_letters),
        }

    # ------------------------------------------------------------------ #
    # Dead-letter queue                                                    #
    # ------------------------------------------------------------------ #

    def get_dead_letter_queue(
        self,
        *,
        tenant_id: str,
        event_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return dead-lettered deliveries for a tenant (max-retry exceeded).

        webhook_system_spec: after max retries, event is dead-lettered and visible
        in webhook delivery logs. Endpoint is marked degraded.
        """
        entries = [
            _delivery_to_dict(d)
            for d in self._svc.dead_letters
            if self._delivery_belongs_to_tenant(d.subscription_id, tenant_id)
        ]
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]
        return entries

    def get_pending_deliveries(
        self,
        *,
        tenant_id: str,
    ) -> list[dict[str, Any]]:
        """Return pending/queued deliveries for a tenant."""
        return [
            _delivery_to_dict(d)
            for d in self._svc.pending
            if self._delivery_belongs_to_tenant(d.subscription_id, tenant_id)
        ]

    # ------------------------------------------------------------------ #
    # Signature verification                                               #
    # ------------------------------------------------------------------ #

    def verify_incoming_webhook(
        self,
        *,
        secret: str,
        payload: str,
        headers: dict[str, str],
        now: datetime | None = None,
    ) -> bool:
        """Verify HMAC-SHA256 signature on an inbound webhook request.

        webhook_system_spec: receivers must verify signature with shared secret and
        reject timestamps older than 5 minutes. Reject replayed X-LMS-Delivery-Id.
        """
        return self._svc.verify_incoming_webhook(
            secret=secret,
            payload=payload,
            headers=headers,
            now=now,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _assert_tenant_owns(self, tenant_id: str, subscription_id: str) -> None:
        owned = self._tenant_index.get(tenant_id, set())
        if subscription_id not in owned:
            raise SubscriptionNotFoundError(
                f"Subscription '{subscription_id}' not found for tenant '{tenant_id}'"
            )

    def _delivery_belongs_to_tenant(self, subscription_id: str, tenant_id: str) -> bool:
        return subscription_id in self._tenant_index.get(tenant_id, set())


# ------------------------------------------------------------------ #
# Serialisation helpers                                               #
# ------------------------------------------------------------------ #

def _sub_to_dict(sub: Subscription) -> dict[str, Any]:
    return {
        "subscription_id": sub.subscription_id,
        "tenant_id": sub.tenant_id,
        "endpoint_url": sub.endpoint_url,
        "subscribed_events": list(sub.subscribed_events),
        "status": sub.status,
        "degraded": sub.degraded,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        "deleted_at": sub.deleted_at.isoformat() if sub.deleted_at else None,
    }


def _delivery_to_dict(d: Any) -> dict[str, Any]:
    return {
        "delivery_id": d.delivery_id,
        "subscription_id": d.subscription_id,
        "event_id": d.event_id,
        "event_type": d.event_type,
        "endpoint_url": d.endpoint_url,
        "status": d.status.value if hasattr(d.status, "value") else str(d.status),
        "attempt_count": d.attempt_count,
        "last_status_code": d.last_status_code,
        "last_error": d.last_error,
        "next_attempt_at": d.next_attempt_at.isoformat() if d.next_attempt_at else None,
        "trace": list(d.trace),
    }
