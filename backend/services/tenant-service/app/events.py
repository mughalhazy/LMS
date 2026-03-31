from __future__ import annotations

from typing import Protocol

from backend.services.shared.events.envelope import EventEnvelope, build_event


class EventPublisher(Protocol):
    def publish(self, event: EventEnvelope) -> None: ...


class InMemoryEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)


def build_lifecycle_event(event_type: str, tenant_id: str, correlation_id: str, payload: dict) -> EventEnvelope:
    return build_event(
        event_type=event_type,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        payload=payload,
        metadata={"producer": "tenant-service", "schema_version": "1.0"},
    )
