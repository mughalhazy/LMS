"""Event consumers for learning-path-service (FA-024, G-24).

Spec: event-consumer-infrastructure.md — Phase 1 in-process bus.
Subscriptions anchor to published event contracts; business logic is stub (logging only).
Full implementation deferred to event-sprint.
"""
from __future__ import annotations

import logging

from backend.services.shared.events.bus import get_default_bus
from backend.services.shared.events.envelope import EventEnvelope

logger = logging.getLogger("learning-path-service.consumers")

def _on_enrollment_changed(event: EventEnvelope) -> None:
    """On enrollment.lifecycle.changed — log; future: advance learning path node."""
    logger.info("learning-path-service: enrollment.lifecycle.changed received — tenant=%s", event.tenant_id)

def _on_course_published(event: EventEnvelope) -> None:
    """On lms.course.published.v1 — log; future: unlock path node."""
    logger.info("learning-path-service: lms.course.published.v1 received — tenant=%s", event.tenant_id)


def register_consumers() -> None:
    """Register all learning-path-service consumers on the default event bus."""
    bus = get_default_bus()
    bus.subscribe("enrollment.lifecycle.changed", _on_enrollment_changed)
    bus.subscribe("lms.course.published.v1", _on_course_published)
    logger.info("learning-path-service: event consumers registered")
