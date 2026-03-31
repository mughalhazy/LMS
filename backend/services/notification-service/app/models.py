from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NotificationPreference:
    preference_id: str
    tenant_id: str
    user_id: str
    category: str
    channels: dict[str, bool]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationEvent:
    event_id: str
    tenant_id: str
    event_type: str
    actor_id: str | None
    recipients: list[str]
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NotificationMessage:
    message_id: str
    tenant_id: str
    user_id: str
    category: str
    channel: str
    subject: str
    body: str
    event_id: str | None
    metadata: dict[str, Any]
    status: str = "queued"
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: datetime | None = None
    failure_reason: str | None = None
