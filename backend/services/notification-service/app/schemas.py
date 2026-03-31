from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreferenceUpsertRequest:
    tenant_id: str
    user_id: str
    category: str
    channels: dict[str, bool]


@dataclass
class NotificationOrchestrationRequest:
    tenant_id: str
    category: str
    recipients: list[str]
    subject: str
    body: str
    tenant_country_code: str = "ZZ"
    channels: list[str] = field(default_factory=lambda: ["email", "push", "in_app"])
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventNotificationRequest:
    tenant_id: str
    event_type: str
    tenant_country_code: str = "ZZ"
    actor_id: str | None = None
    recipients: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryDrainRequest:
    max_messages: int = 100


@dataclass
class EventRouteUpsertRequest:
    tenant_id: str
    event_type: str
    category: str
    channels: list[str]
    subject_template: str
    body_template: str
