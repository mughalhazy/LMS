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
    # CAT-001: anchor event-envelope.md mandates exactly 7 top-level fields.
    # topic, producer_service, schema_version are kept as dataclass fields for internal
    # bus routing but are ALSO written into metadata so external consumers see a
    # 7-field-conformant envelope with non-canonical data in metadata.
    resolved_topic = topic or event_type
    meta = dict(metadata or {})
    meta.setdefault("topic", resolved_topic)
    meta.setdefault("producer", producer_service)
    meta.setdefault("schema_version", schema_version)
    return EventEnvelope(
        event_id=str(uuid4()),
        event_type=event_type,
        topic=resolved_topic,
        producer_service=producer_service,
        schema_version=schema_version,
        timestamp=datetime.now(timezone.utc),
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        payload=payload,
        metadata=meta,
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
