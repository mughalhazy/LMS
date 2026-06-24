"""Event consumers for media-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("media-service.consumers")

def _on_course_archived(event: EventEnvelope) -> None:
    """On lms.course.archived.v1 — log; future: set media read-only."""
    logger.info("media-service: lms.course.archived.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all media-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("lms.course.archived.v1", _on_course_archived)
    logger.info("media-service: event consumers registered")
