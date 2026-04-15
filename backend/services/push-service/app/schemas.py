from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PushChannel = Literal["mobile", "web"]


@dataclass
class SubscriptionCreateRequest:
    tenant_id: str
    user_id: str
    channel: PushChannel
    endpoint: str
    auth_key: str | None = None
    p256dh_key: str | None = None
    device_token: str | None = None
    platform: str | None = None


@dataclass
class SubscriptionUpdateRequest:
    enabled: bool


@dataclass
class NotificationSendRequest:
    tenant_id: str
    user_id: str
    title: str
    body: str
    channels: list[PushChannel] = field(default_factory=list)
    data: dict[str, object] = field(default_factory=dict)


@dataclass
class QueueDrainRequest:
    max_messages: int = 50
