from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from .models import PushNotification, PushSubscription, QueueMessage
from .schemas import (
    NotificationSendRequest,
    QueueDrainRequest,
    SubscriptionCreateRequest,
    SubscriptionUpdateRequest,
)
from .store import InMemoryPushStore


class PushService:
    def __init__(self, store: InMemoryPushStore) -> None:
        self.store = store

    def create_subscription(self, req: SubscriptionCreateRequest) -> tuple[int, dict[str, Any]]:
        if req.channel == "mobile" and not req.device_token:
            return 400, {"error": "device_token_required"}
        if req.channel == "web" and (not req.auth_key or not req.p256dh_key):
            return 400, {"error": "web_push_keys_required"}

        subscription = PushSubscription(
            subscription_id=self.store.new_id("sub"),
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            channel=req.channel,
            endpoint=req.endpoint,
            auth_key=req.auth_key,
            p256dh_key=req.p256dh_key,
            device_token=req.device_token,
            platform=req.platform,
        )
        self.store.create_subscription(subscription)
        return 201, {"subscription": asdict(subscription)}

    def list_subscriptions(self, tenant_id: str, user_id: str) -> tuple[int, dict[str, Any]]:
        subs = self.store.list_subscriptions(tenant_id, user_id)
        return 200, {"subscriptions": [asdict(sub) for sub in subs]}

    def update_subscription(
        self, subscription_id: str, req: SubscriptionUpdateRequest
    ) -> tuple[int, dict[str, Any]]:
        subscription = self.store.get_subscription(subscription_id)
        if subscription is None:
            return 404, {"error": "subscription_not_found"}

        subscription.enabled = req.enabled
        subscription.updated_at = datetime.utcnow()
        return 200, {"subscription": asdict(subscription)}

    def send_notification(self, req: NotificationSendRequest) -> tuple[int, dict[str, Any]]:
        supported_channels = {"mobile", "web"}
        channels = req.channels or ["mobile", "web"]
        if not set(channels).issubset(supported_channels):
            return 400, {"error": "unsupported_channel"}

        subscriptions = [
            sub
            for sub in self.store.list_subscriptions(req.tenant_id, req.user_id)
            if sub.enabled and sub.channel in channels
        ]
        if not subscriptions:
            return 202, {"status": "accepted", "queued": 0, "reason": "no_active_subscriptions"}

        notification = PushNotification(
            notification_id=self.store.new_id("notif"),
            tenant_id=req.tenant_id,
            user_id=req.user_id,
            title=req.title,
            body=req.body,
            channels=channels,
            data=req.data,
        )
        self.store.save_notification(notification)

        queued_messages: list[dict[str, Any]] = []
        for sub in subscriptions:
            queue_message = QueueMessage(
                queue_message_id=self.store.new_id("qmsg"),
                notification_id=notification.notification_id,
                subscription_id=sub.subscription_id,
                tenant_id=sub.tenant_id,
                channel=sub.channel,
                endpoint=sub.endpoint,
                payload={
                    "title": req.title,
                    "body": req.body,
                    "data": req.data,
                    "channel": sub.channel,
                },
            )
            self.store.enqueue_message(queue_message)
            queued_messages.append(asdict(queue_message))

        return 202, {
            "status": "accepted",
            "notification_id": notification.notification_id,
            "queued": len(queued_messages),
            "queue_messages": queued_messages,
        }

    def drain_queue(self, req: QueueDrainRequest) -> tuple[int, dict[str, Any]]:
        delivered: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        processed = 0

        while processed < req.max_messages:
            message = self.store.next_message()
            if message is None:
                break
            processed += 1
            message.attempts += 1
            message.updated_at = datetime.utcnow()

            if "invalid" in message.endpoint:
                message.status = "failed"
                message.last_error = "endpoint_unreachable"
                failed.append(asdict(message))
                continue

            message.status = "delivered"
            delivered.append(asdict(message))

        return 200, {
            "processed": processed,
            "delivered": len(delivered),
            "failed": len(failed),
            "delivered_messages": delivered,
            "failed_messages": failed,
        }
