from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

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
        event_type: str,
        topic: str,
        tenant_id: str,
        aggregate_id: str,
        payload: dict[str, str],
    ) -> EventRecord:
        event = EventRecord(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            tenant_id=tenant_id,
            correlation_id=str(uuid4()),
            payload=payload,
            metadata={"topic": topic, "aggregate_id": aggregate_id, "producer": "cohort-service"},
        )
        self.published_events.append(event)
        return event
