from __future__ import annotations

from collections import deque
from typing import Deque
from uuid import uuid4

from .models import PushNotification, PushSubscription, QueueMessage


class InMemoryPushStore:
    def __init__(self) -> None:
        self.subscriptions: dict[str, PushSubscription] = {}
        self.notifications: dict[str, PushNotification] = {}
        self.queue: Deque[str] = deque()
        self.queue_messages: dict[str, QueueMessage] = {}

    def create_subscription(self, subscription: PushSubscription) -> PushSubscription:
        self.subscriptions[subscription.subscription_id] = subscription
        return subscription

    def get_subscription(self, subscription_id: str) -> PushSubscription | None:
        return self.subscriptions.get(subscription_id)

    def list_subscriptions(self, tenant_id: str, user_id: str) -> list[PushSubscription]:
        return [
            subscription
            for subscription in self.subscriptions.values()
            if subscription.tenant_id == tenant_id and subscription.user_id == user_id
        ]

    def save_notification(self, notification: PushNotification) -> PushNotification:
        self.notifications[notification.notification_id] = notification
        return notification

    def enqueue_message(self, message: QueueMessage) -> QueueMessage:
        self.queue_messages[message.queue_message_id] = message
        self.queue.append(message.queue_message_id)
        return message

    def next_message(self) -> QueueMessage | None:
        while self.queue:
            msg_id = self.queue.popleft()
            message = self.queue_messages.get(msg_id)
            if message and message.status == "queued":
                return message
        return None

    @staticmethod
    def new_id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:12]}"
