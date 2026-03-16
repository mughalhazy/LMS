from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4


@dataclass
class TenantLifecycleEventEnvelope:
    event_id: str
    event_type: str
    tenant_id: str
    timestamp: datetime
    payload: dict[str, Any] = field(default_factory=dict)


class EventPublisher(Protocol):
    def publish(self, event: TenantLifecycleEventEnvelope) -> None: ...


class InMemoryEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[TenantLifecycleEventEnvelope] = []

    def publish(self, event: TenantLifecycleEventEnvelope) -> None:
        self.events.append(event)


def build_lifecycle_event(event_type: str, tenant_id: str, payload: dict[str, Any]) -> TenantLifecycleEventEnvelope:
    return TenantLifecycleEventEnvelope(
        event_id=f"evt_{uuid4().hex}",
        event_type=event_type,
        tenant_id=tenant_id,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
    )
