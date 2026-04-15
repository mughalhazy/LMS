from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    topic: str
    producer_service: str
    schema_version: str
    timestamp: datetime
    tenant_id: str
    payload: dict[str, Any]
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def build_event(
    *,
    event_type: str,
    topic: str | None = None,
    producer_service: str = "unknown-service",
    schema_version: str = "v1",
    tenant_id: str,
    correlation_id: str = "",
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid4()),
        event_type=event_type,
        topic=topic or event_type,
        producer_service=producer_service,
        schema_version=schema_version,
        timestamp=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        payload=payload,
        metadata=metadata or {},
    )


def publish_event(
    *,
    event_type: str,
    topic: str | None = None,
    producer_service: str = "unknown-service",
    schema_version: str = "v1",
    tenant_id: str,
    correlation_id: str = "",
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> EventEnvelope:
    """Build an event envelope and publish it to the default event bus.

    CGAP-059/CGAP-082 fix: previously build_event() created envelopes with no transport.
    This function builds the envelope and delivers it to the process-level EventBus,
    making all backend service events visible to subscribers (event-ingestion, workflow engine, etc.).

    References: ARCH_05 §5, event_envelope.md, event_ingestion_spec.md §4.1
    """
    # Import deferred to avoid circular import (bus imports envelope for type hints)
    from .bus import get_default_bus

    event = build_event(
        event_type=event_type,
        topic=topic,
        producer_service=producer_service,
        schema_version=schema_version,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        payload=payload,
        metadata=metadata,
    )
    get_default_bus().publish(event)
    return event
