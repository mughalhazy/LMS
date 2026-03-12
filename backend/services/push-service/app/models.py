from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

PushChannel = Literal["mobile", "web"]


@dataclass
class PushSubscription:
    subscription_id: str
    tenant_id: str
    user_id: str
    channel: PushChannel
    endpoint: str
    auth_key: str | None = None
    p256dh_key: str | None = None
    device_token: str | None = None
    platform: str | None = None
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PushNotification:
    notification_id: str
    tenant_id: str
    user_id: str
    title: str
    body: str
    data: dict[str, object] = field(default_factory=dict)
    channels: list[PushChannel] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QueueMessage:
    queue_message_id: str
    notification_id: str
    subscription_id: str
    tenant_id: str
    channel: PushChannel
    endpoint: str
    payload: dict[str, object]
    status: Literal["queued", "delivered", "failed"] = "queued"
    attempts: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_error: str | None = None
