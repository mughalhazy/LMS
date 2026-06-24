"""Event consumers for event-ingestion-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("event-ingestion-service.consumers")

def _on_system_heartbeat(event: EventEnvelope) -> None:
    """On lms.system.heartbeat.v1 — log; future: ack platform health."""
    logger.info("event-ingestion-service: lms.system.heartbeat.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all event-ingestion-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("lms.system.heartbeat.v1", _on_system_heartbeat)
    logger.info("event-ingestion-service: event consumers registered")
