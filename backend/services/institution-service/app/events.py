from __future__ import annotations

from app.models import DomainEvent


class EventPublisher:
    """In-memory publisher abstraction for lifecycle and hierarchy events."""

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[DomainEvent]:
        return list(self._events)
