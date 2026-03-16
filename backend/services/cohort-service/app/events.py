from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .models import EventRecord


@dataclass
class EventPublisher:
    """In-memory event publisher placeholder for broker integration."""

    published_events: list[EventRecord]

    def __init__(self) -> None:
        self.published_events = []

    def publish(
        self,
        *,
        event_name: str,
        topic: str,
        tenant_id: str,
        aggregate_id: str,
        payload: dict[str, str],
    ) -> EventRecord:
        event = EventRecord(
            event_name=event_name,
            topic=topic,
            tenant_id=tenant_id,
            aggregate_id=aggregate_id,
            payload=payload,
            occurred_at=datetime.now(timezone.utc),
        )
        self.published_events.append(event)
        return event
