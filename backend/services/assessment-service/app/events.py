from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass
class DomainEvent:
    event_type: str
    tenant_id: str
    entity_id: str
    occurred_at: datetime
    payload: dict[str, Any]


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
