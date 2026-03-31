from __future__ import annotations

from typing import Protocol

from backend.services.shared.events.envelope import EventEnvelope


DomainEvent = EventEnvelope


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class InMemoryEventPublisher:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
